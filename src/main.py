"""main.py — Entry point Chrono-Craft.

Tanggung jawab: event loop, dt, render ke canvas internal + scaling ke window,
dan routing fase PLANNING <-> ACTION. Logika fase di class Game ini nanti
dipindah ke states.py (FSM penuh); nama method transisi sudah disiapkan.
"""
import sys
from collections import deque

import pygame

import settings as S
from cards import (
    TIMELINE_SLOT_RECTS,
    CardHand,
    build_starting_hand,
    draw_timeline,
    try_queue_card,
)
from physics import Entity
from vfx import ParticleSystem

# --- Aturan giliran (nanti dipindah ke settings.py) --------------------------
CARDS_PER_TURN = min(2, S.TIMELINE_MAX_SLOTS)   # kartu yang WAJIB dipilih
ACTION_DURATION = 3.0                           # detik simulasi per giliran
PHYSICS_HZ = 120                                # fixed timestep simulasi
FIXED_DT = 1.0 / PHYSICS_HZ
ACTION_STEPS = round(ACTION_DURATION * PHYSICS_HZ)   # 360 step total
CARD_SLICE_STEPS = ACTION_STEPS // CARDS_PER_TURN    # jeda antar kartu: 180 step = 1,5 s

# Urutan asli tangan, dipakai untuk mengembalikan kartu yang dibatalkan.
_HAND_ORDER = tuple(c.type for c in build_starting_hand())


def to_canvas_pos(window_pos):
    """Koordinat mouse window (1280x720) -> canvas internal (480x270)."""
    return (window_pos[0] / S.SCALE_X, window_pos[1] / S.SCALE_Y)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.screen = pygame.display.set_mode((S.SCREEN_WIDTH, S.SCREEN_HEIGHT))
        self.canvas = pygame.Surface((S.INTERNAL_WIDTH, S.INTERNAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 16)
        self.running = True

        self.current_state = S.STATE_PLANNING
        self.player = self._spawn_player()
        self.hand = CardHand(build_starting_hand())
        self.action_timeline = []      # kartu terpilih, urutan klik = urutan eksekusi

        # Runtime fase ACTION
        self.pending = deque()         # antrean (step_eksekusi, kartu), FIFO
        self.action_step = 0           # jumlah step fisika yang sudah berjalan
        self.accumulator = 0.0         # sisa waktu frame untuk fixed timestep
        self.executed = 0              # jumlah kartu yang sudah dieksekusi

        # VFX (kosmetik saja; tidak memengaruhi simulasi)
        self.particles = ParticleSystem(bounds=pygame.Rect(S.ARENA_RECT))
        self.trail_color = S.COLORS["NEON_CYAN"]   # warna jejak = kartu terakhir yang jalan

    # ------------------------------------------------------------- lifecycle
    def run(self):
        while self.running:
            dt = min(self.clock.tick(S.FPS) / 1000.0, S.MAX_DT)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    def _spawn_player(self):
        p = Entity(80, 0)
        p.position.y = p.bounds.bottom - p.half_size.y   # mulai diam di lantai
        return p

    # ---------------------------------------------------------------- events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self._try_start_action()
                elif event.key == pygame.K_BACKSPACE:
                    self._undo_last_card()
                elif event.key == pygame.K_r:
                    self._reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._click_card(to_canvas_pos(event.pos))
                elif event.button == 3:
                    self._undo_last_card()

    def _click_card(self, canvas_pos):
        # Kartu hanya bisa dipilih saat PLANNING dan slot giliran belum penuh.
        if self.current_state != S.STATE_PLANNING:
            return
        if len(self.action_timeline) < CARDS_PER_TURN:
            try_queue_card(self.hand, self.action_timeline, canvas_pos)

    def _undo_last_card(self):
        if self.current_state != S.STATE_PLANNING or not self.action_timeline:
            return
        card = self.action_timeline.pop()
        restored = sorted(self.hand.cards + [card], key=lambda c: _HAND_ORDER.index(c.type))
        self.hand = CardHand(restored)

    def _reset(self):
        self.player = self._spawn_player()
        self.particles.clear()
        self._enter_planning()

    # ----------------------------------------------------- transisi fase (FSM)
    def _try_start_action(self):
        if self.current_state == S.STATE_PLANNING and len(self.action_timeline) == CARDS_PER_TURN:
            self._enter_action()

    def _enter_action(self):
        self.current_state = S.STATE_ACTION
        # Jadwalkan kartu: kartu ke-i menyala pada step i * CARD_SLICE_STEPS.
        self.pending = deque(
            (i * CARD_SLICE_STEPS, card) for i, card in enumerate(self.action_timeline)
        )
        self.action_step = 0
        self.accumulator = 0.0
        self.executed = 0
        self.trail_color = S.COLORS["NEON_CYAN"]

    def _enter_planning(self):
        # Waktu "dibekukan": kecepatan & percepatan dinolkan, posisi dipertahankan.
        self.player.velocity.update(0, 0)
        self.player.acceleration.update(0, 0)
        self.action_timeline.clear()
        self.hand = CardHand(build_starting_hand())   # "Draw phase" sederhana
        self.pending.clear()
        self.accumulator = 0.0
        self.action_step = 0
        self.executed = 0
        self.current_state = S.STATE_PLANNING

    # ---------------------------------------------------------------- update
    def update(self, dt):
        # Partikel murni visual: pakai dt frame dan selalu berjalan, jadi sisa
        # jejak tetap memudar (tidak "membeku") saat kembali ke PLANNING.
        # Dipanggil SEBELUM simulasi agar partikel yang baru lahir di frame ini
        # tidak ikut menua dengan dt frame yang sama.
        self.particles.update(dt)

        # PLANNING: waktu berhenti, tidak ada entitas yang bergerak.
        if self.current_state == S.STATE_ACTION:
            self._update_action(dt)

    def _update_action(self, dt):
        """Fixed timestep: waktu frame (dt) ditampung, lalu simulasi maju dalam
        langkah tetap FIXED_DT. Hasil identik di FPS berapa pun (deterministik)."""
        self.accumulator += dt
        while self.accumulator >= FIXED_DT and self.current_state == S.STATE_ACTION:
            self._physics_step()
            self.accumulator -= FIXED_DT

    def _physics_step(self):
        # 1. Eksekusi kartu yang jadwalnya tiba (FIFO -> urutan timeline terjaga).
        while self.pending and self.pending[0][0] <= self.action_step:
            _, card = self.pending.popleft()
            card.execute_effect(self.player)
            self.executed += 1
            # VFX: semburan di BELAKANG pemain (berlawanan arah dorongan kartu).
            self.trail_color = card.color
            back = -card.direction
            self.particles.burst(self.player.position + back * self.player.half_size.x,
                                 back, card.color)

        # 2. Maju satu langkah fisika.
        self.player.update(FIXED_DT)
        self.action_step += 1

        # VFX: jejak kontinu selama melaju. Diemisikan per step tetap, jadi
        # kepadatannya konsisten di FPS berapa pun.
        self.particles.trail(self.player.position, self.player.velocity,
                             self.trail_color, FIXED_DT)

        # 3. Durasi habis -> kembali ke PLANNING.
        if self.action_step >= ACTION_STEPS:
            self._enter_planning()

    # ------------------------------------------------------------------ draw
    def draw(self):
        c, font = self.canvas, self.font
        planning = self.current_state == S.STATE_PLANNING

        c.fill(S.COLORS["BG"])
        panel_h = S.INTERNAL_HEIGHT - S.UI_PANEL_TOP
        pygame.draw.rect(c, S.COLORS["PANEL"], (0, S.UI_PANEL_TOP, S.INTERNAL_WIDTH, panel_h))
        pygame.draw.rect(c, S.COLORS["GRID"], S.ARENA_RECT, 1)   # batas arena
        self.particles.draw(c, clip=pygame.Rect(S.ARENA_RECT))   # di belakang pemain
        pygame.draw.rect(c, S.COLORS["NEON_CYAN"], self.player.rect)

        can_pick = planning and len(self.action_timeline) < CARDS_PER_TURN
        self.hand.draw(c, font, to_canvas_pos(pygame.mouse.get_pos()), interactive=can_pick)
        draw_timeline(c, font, self.action_timeline)
        for rect in TIMELINE_SLOT_RECTS[: self.executed]:        # sorot kartu yang sudah jalan
            pygame.draw.rect(c, S.COLORS["WHITE"], rect, 1)

        self._draw_progress_bar()
        self._draw_hud(planning)

        pygame.transform.scale(c, (S.SCREEN_WIDTH, S.SCREEN_HEIGHT), self.screen)
        pygame.display.flip()

    def _draw_progress_bar(self):
        x, y, w, h = 12, 24, 160, 4
        pygame.draw.rect(self.canvas, S.COLORS["GRID"], (x, y, w, h))
        fill = int(w * self.action_step / ACTION_STEPS)
        pygame.draw.rect(self.canvas, S.COLORS["NEON_CYAN"], (x, y, fill, h))
        for i, card in enumerate(self.action_timeline):          # penanda kapan tiap kartu menyala
            tx = x + int(w * i * CARD_SLICE_STEPS / ACTION_STEPS)
            pygame.draw.rect(self.canvas, card.color, (tx, y - 2, 2, h + 4))

    def _draw_hud(self, planning):
        if planning:
            n = len(self.action_timeline)
            if n < CARDS_PER_TURN:
                text = f"PLANNING | Pilih kartu {n}/{CARDS_PER_TURN}"
                color = S.COLORS["WHITE"]
            else:
                text = "PLANNING | Tekan [SPACE] untuk eksekusi!"
                color = S.COLORS["NEON_YEL"]
            text += "  | [Klik kanan] batal  [R] reset"
        else:
            t = self.action_step * FIXED_DT
            text = f"ACTION | t = {t:.2f} / {ACTION_DURATION:.1f} s"
            color = S.COLORS["NEON_PINK"]

        self.canvas.blit(self.font.render(text, False, color), (12, 12))
        fps = self.font.render(f"{self.clock.get_fps():.0f} FPS", False, S.COLORS["DIM"])
        self.canvas.blit(fps, (S.INTERNAL_WIDTH - fps.get_width() - 12, 12))


def main():
    Game().run()


if __name__ == "__main__":
    main()
