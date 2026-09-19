"""physics.py — Mesin fisika Chrono-Craft.

Berisi class `Entity`: benda bergerak dengan posisi/kecepatan/percepatan
(Vector2), gravitasi, friksi lantai, dan AABB collision terhadap batas arena.

Konvensi:
- `position` adalah PUSAT AABB (memudahkan rotasi/lingkaran di masa depan).
- Semua satuan: piksel dan detik. Semua perubahan dikali `dt`.
"""
from math import copysign

import pygame
from pygame.math import Vector2

import settings as S


class Entity:
    def __init__(
        self,
        x,
        y,
        width=12,
        height=12,
        mass=1.0,
        restitution=S.PHYSICS_RESTITUTION,
        friction=1.0,
        use_gravity=True,
        bounds=None,
    ):
        if mass <= 0:
            raise ValueError("mass harus > 0")

        self.position = Vector2(x, y)
        self.velocity = Vector2()
        # `acceleration` berfungsi sebagai AKUMULATOR gaya per-frame:
        # direset ke nol di akhir setiap update().
        self.acceleration = Vector2()

        self.half_size = Vector2(width, height) / 2
        self.mass = float(mass)
        self.restitution = restitution   # elastisitas pantulan
        self.friction = friction         # pengali friksi lantai (1.0 = normal)
        self.use_gravity = use_gravity

        # Batas arena (referensi, bukan salinan -> bisa dibagi antar entitas).
        self.bounds = bounds if bounds is not None else pygame.Rect(S.ARENA_RECT)

        self.on_ground = False
        # Kecepatan benturan terkuat pada frame terakhir (px/s). Disiapkan
        # untuk Kinetic Damage; 0.0 bila tidak ada benturan berarti.
        self.last_impact_speed = 0.0

    # ------------------------------------------------------------------ API
    @property
    def rect(self):
        """AABB integer untuk menggambar / uji tumpang tindih kasar."""
        return pygame.Rect(
            round(self.position.x - self.half_size.x),
            round(self.position.y - self.half_size.y),
            round(self.half_size.x * 2),
            round(self.half_size.y * 2),
        )

    def apply_force(self, force):
        """Gaya KONTINU (F = m*a). Berlaku hanya untuk frame ini, jadi panggil
        tiap frame selama gaya aktif (mis. magnet Attract/Repulse)."""
        self.acceleration += force / self.mass

    def apply_impulse(self, impulse):
        """Dorongan SESAAT: langsung mengubah velocity (dv = J/m).
        Dipakai untuk efek kartu satu-kali seperti Kinetic Dash."""
        self.velocity += impulse / self.mass

    def update(self, dt):
        self.last_impact_speed = 0.0

        # Gravitasi adalah percepatan (independen dari massa).
        if self.use_gravity:
            self.acceleration.y += S.PHYSICS_GRAVITY

        # Semi-implicit Euler: update velocity dulu, baru position.
        # Lebih stabil daripada explicit Euler untuk pantulan.
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt
        self.acceleration.update(0, 0)  # reset akumulator gaya

        self._collide_bounds()

        # Friksi hanya untuk kontak diam/menggelinding (vy == 0 setelah
        # collision). Frame benturan tidak dikenai friksi: durasi benturan
        # 1 frame berapa pun FPS-nya, jadi friksi di sana akan bergantung dt.
        if self.on_ground and self.velocity.y == 0.0:
            self._apply_floor_friction(dt)

    # ------------------------------------------------------------ internals
    def _collide_bounds(self):
        """AABB vs batas arena: O(1) per entitas. Posisi di-clamp ke dalam
        arena (jadi tidak bisa tembus), lalu velocity dipantulkan."""
        b, h = self.bounds, self.half_size
        p = self.position
        self.on_ground = False

        # Sumbu X: dinding kiri (normal +1) / kanan (normal -1)
        if p.x - h.x < b.left:
            p.x = b.left + h.x
            self._rebound(0, +1)
        elif p.x + h.x > b.right:
            p.x = b.right - h.x
            self._rebound(0, -1)

        # Sumbu Y: langit-langit (normal +1) / lantai (normal -1)
        if p.y - h.y < b.top:
            p.y = b.top + h.y
            self._rebound(1, +1)
        elif p.y + h.y > b.bottom:
            p.y = b.bottom - h.y
            self._rebound(1, -1)
            self.on_ground = True

    def _rebound(self, axis, normal):
        """Pantulkan velocity pada `axis` (0=x, 1=y). `normal` = arah normal
        permukaan yang menghadap ke dalam arena (+1 atau -1)."""
        v = self.velocity[axis]
        if v * normal >= 0:      # sudah bergerak menjauhi dinding -> abaikan
            return

        impact = abs(v)
        if impact > S.PHYSICS_REST_THRESHOLD:
            self.last_impact_speed = max(self.last_impact_speed, impact)

        v = -v * self.restitution
        # Cegah jitter tak berujung saat benda "diam" di lantai.
        self.velocity[axis] = 0.0 if abs(v) < S.PHYSICS_REST_THRESHOLD else v

    def _apply_floor_friction(self, dt):
        """Friksi Coulomb: perlambatan konstan (px/s^2) melawan arah gerak.
        Dikali dt -> konsisten di FPS berapa pun. Berhenti tepat di 0
        (tidak berbalik arah)."""
        decel = S.PHYSICS_FLOOR_FRICTION * self.friction * dt
        vx = self.velocity.x
        self.velocity.x = 0.0 if abs(vx) <= decel else vx - copysign(decel, vx)
