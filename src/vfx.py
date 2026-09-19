"""vfx.py — Efek visual (juiciness): sistem partikel piksel.

ParticleSystem menyebar kotak piksel 2x2 / 4x4 yang bergerak, melambat karena
drag, lalu memudar (fade-out) sampai hilang.

Catatan desain:
- Murni kosmetik: RNG milik sendiri dan TIDAK menyentuh simulasi fisika, jadi
  determinisme fixed timestep di main.py tidak terganggu.
- Tidak bergantung pada settings.py (warna dikirim oleh pemanggil).
- Semua posisi/kecepatan memakai Vector2 dan semua perubahan dikali dt.
"""
import math
import random

import pygame
from pygame.math import Vector2

# --- Parameter default (knob tuning) -----------------------------------------
MAX_PARTICLES = 512      # batas keras jumlah partikel hidup (spawn ditolak bila penuh)
BIG_CHANCE = 0.3         # peluang ukuran 4x4 (sisanya 2x2)
DRAG = 3.0               # 1/s, peredam kecepatan (eksponensial -> independen FPS)
FADE_LEVELS = 6          # tingkat alpha: fade "bertahap" ala retro + cache sprite kecil
BOUNCE = 0.35            # kelembaman pantulan partikel di batas arena (0 = menempel)


class Particle:
    """Data satu partikel. __slots__ + pooling -> tidak ada alokasi per spawn."""
    __slots__ = ("pos", "vel", "life", "max_life", "size", "color")

    def __init__(self):
        self.pos = Vector2()
        self.vel = Vector2()
        self.life = 0.0          # sisa umur (detik)
        self.max_life = 1.0
        self.size = 2
        self.color = (255, 255, 255)


class ParticleSystem:
    def __init__(self, max_particles=MAX_PARTICLES, drag=DRAG, seed=None, bounds=None):
        self.max_particles = max_particles
        self.drag = drag
        # Opsional (pygame.Rect): partikel memantul pelan di batas ini, sehingga
        # semburan ke arah lantai jadi puff debu yang menyebar, bukan terpotong.
        self.bounds = bounds
        self.rng = random.Random(seed)   # terpisah dari random global
        self.particles = []              # partikel hidup
        self._pool = []                  # partikel mati, siap dipakai ulang
        self._sprites = {}               # cache: (size, color, level) -> Surface
        self._trail_accum = 0.0          # sisa pecahan partikel untuk emitter jejak

    def __len__(self):
        return len(self.particles)

    def clear(self):
        self._pool.extend(self.particles)
        self.particles.clear()
        self._trail_accum = 0.0

    # ------------------------------------------------------------- spawning
    def _spawn(self, pos, vel, color, life):
        if len(self.particles) >= self.max_particles:
            return
        p = self._pool.pop() if self._pool else Particle()
        p.pos.update(pos)
        p.vel.update(vel)
        p.life = p.max_life = life
        p.size = 4 if self.rng.random() < BIG_CHANCE else 2
        p.color = color
        self.particles.append(p)

    def burst(self, pos, direction, color, count=14,
              speed=(60.0, 160.0), cone=35.0, life=(0.35, 0.75)):
        """Semburan sesaat berbentuk kerucut. `direction` = arah semburan
        (mis. berlawanan dengan arah dorongan kartu), `cone` = setengah sudut
        sebar dalam derajat, `speed` dalam px/s, `life` dalam detik."""
        base = direction.normalize() if direction.length_squared() > 0 else Vector2(0, -1)
        for _ in range(count):
            # Putar arah dasar secara acak dalam kerucut, lalu skalakan kecepatannya.
            vel = base.rotate(self.rng.uniform(-cone, cone)) * self.rng.uniform(*speed)
            jitter = Vector2(self.rng.uniform(-2, 2), self.rng.uniform(-2, 2))
            self._spawn(pos + jitter, vel, color, self.rng.uniform(*life))

    def trail(self, pos, velocity, color, dt, rate=90.0, min_speed=50.0,
              ref_speed=300.0, back_offset=6.0):
        """Emitter jejak kontinu: panggil tiap step simulasi dengan dt step itu.
        Jumlah partikel ~ rate * (speed/ref_speed) per detik, muncul DI BELAKANG
        arah gerak. Pecahan partikel ditampung di accumulator (dt-independen)."""
        speed = velocity.length()
        if speed < min_speed:
            return
        self._trail_accum += rate * min(1.0, speed / ref_speed) * dt
        n = int(self._trail_accum)
        self._trail_accum -= n

        back = -velocity / speed                      # vektor satuan ke belakang
        for _ in range(n):
            offset = back * back_offset + Vector2(self.rng.uniform(-3, 3), self.rng.uniform(-3, 3))
            drift = back * self.rng.uniform(10, 40) + Vector2(
                self.rng.uniform(-20, 20), self.rng.uniform(-20, 20))
            self._spawn(pos + offset, drift, color, self.rng.uniform(0.35, 0.7))

    # --------------------------------------------------------------- update
    def update(self, dt):
        parts = self.particles
        if not parts:
            return
        damp = math.exp(-self.drag * dt)     # sama untuk semua partikel -> hitung sekali
        i = 0
        while i < len(parts):
            p = parts[i]
            p.life -= dt
            if p.life <= 0.0:
                # Swap-remove: O(1), urutan tidak penting. Jangan naikkan i
                # karena elemen hasil swap belum diproses.
                parts[i] = parts[-1]
                parts.pop()
                self._pool.append(p)
                continue
            p.vel *= damp
            p.pos += p.vel * dt
            if self.bounds is not None:
                self._collide(p)
            i += 1

    def _collide(self, p):
        """Pantulan teredam di sisi-sisi bounds. Tepi diinset setengah ukuran
        partikel agar kotak tidak tenggelam ke dinding/lantai."""
        b, h = self.bounds, p.size / 2
        pos, vel = p.pos, p.vel
        if pos.y > b.bottom - h:
            pos.y, vel.y = b.bottom - h, -abs(vel.y) * BOUNCE
        elif pos.y < b.top + h:
            pos.y, vel.y = b.top + h, abs(vel.y) * BOUNCE
        if pos.x > b.right - h:
            pos.x, vel.x = b.right - h, -abs(vel.x) * BOUNCE
        elif pos.x < b.left + h:
            pos.x, vel.x = b.left + h, abs(vel.x) * BOUNCE

    # ----------------------------------------------------------------- draw
    def _sprite(self, size, color, ratio):
        """Sprite kotak dengan alpha sesuai sisa umur (ratio 1 -> 0)."""
        level = min(FADE_LEVELS - 1, int(ratio * FADE_LEVELS))
        key = (size, color, level)
        sprite = self._sprites.get(key)
        if sprite is None:
            sprite = pygame.Surface((size, size))
            sprite.fill(color)
            sprite.set_alpha(255 * (level + 1) // FADE_LEVELS)
            self._sprites[key] = sprite
        return sprite

    def draw(self, surface, clip=None):
        """Gambar semua partikel ke `surface` (canvas internal). `clip`
        (pygame.Rect) mencegah partikel menimpa area di luar arena, mis. UI."""
        if not self.particles:
            return
        previous_clip = surface.get_clip()
        if clip is not None:
            surface.set_clip(clip)
        seq = [
            (self._sprite(p.size, p.color, p.life / p.max_life),
             (int(p.pos.x) - p.size // 2, int(p.pos.y) - p.size // 2))
            for p in self.particles
        ]
        surface.blits(seq, doreturn=False)   # batch blit (loop-nya di C)
        surface.set_clip(previous_clip)
