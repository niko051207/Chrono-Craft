"""cards.py — Sistem kartu Chrono-Craft.

Isi modul:
- Card         : data kartu + `execute_effect(target)` (mengubah physics Entity).
- CardHand     : tata letak kartu di tangan, hit-test mouse, dan penggambaran.
- draw_timeline: menggambar slot `action_timeline` (antrean aksi terencana).
- try_queue_card: logika klik -> pindahkan kartu dari tangan ke timeline.

Semua koordinat di sini adalah koordinat CANVAS internal (480x270), bukan
koordinat window. Konversi mouse dilakukan di main.py.
"""
import pygame
from pygame.math import Vector2

import settings as S

# --- Definisi kartu (data-driven: tambah kartu baru = tambah satu entri) ----
# `direction` masih tetap (placeholder). Nanti diganti oleh lintasan/aim yang
# dipilih pemain di fase PLANNING.
CARD_DEFS = {
    "DASH": {"name": "Kinetic Dash", "direction": (1, 0),  "power": 300, "color": "NEON_CYAN"},
    "PULL": {"name": "Magnet Pull",  "direction": (-1, 0), "power": 240, "color": "NEON_PINK"},
    "LEAP": {"name": "Sky Leap",     "direction": (0, -1), "power": 280, "color": "NEON_YEL"},
}


class Card:
    def __init__(self, name, card_type, power, direction, color):
        self.name = name
        self.type = card_type                          # 'DASH', 'PULL', ...
        self.power = power                             # besar impuls (px/s untuk massa 1)
        self.direction = Vector2(direction).normalize()  # vektor satuan
        self.color = color                             # RGB untuk UI

    @classmethod
    def from_type(cls, card_type):
        d = CARD_DEFS[card_type]
        return cls(d["name"], card_type, d["power"], d["direction"], S.COLORS[d["color"]])

    def execute_effect(self, target_entity):
        """Terapkan efek kartu ke entitas fisika. Saat ini semua kartu berupa
        impuls sesaat: dv = (arah * power) / massa (dihitung di Entity)."""
        target_entity.apply_impulse(self.direction * self.power)

    def __repr__(self):
        return f"Card({self.type})"


def build_starting_hand():
    return [Card.from_type(t) for t in ("DASH", "PULL", "LEAP")]


# ------------------------------------------------------------------ Layout
def centered_row(count, y, width, height, gap):
    """Deretan `count` Rect yang berpusat horizontal di canvas."""
    total = count * width + (count - 1) * gap
    x0 = (S.INTERNAL_WIDTH - total) // 2
    return [pygame.Rect(x0 + i * (width + gap), y, width, height) for i in range(count)]


# Slot timeline itu tetap, jadi cukup dihitung sekali.
TIMELINE_SLOT_RECTS = centered_row(
    S.TIMELINE_MAX_SLOTS, S.TIMELINE_SLOT_Y, S.CARD_WIDTH, S.TIMELINE_SLOT_HEIGHT, S.CARD_GAP
)


def _blit_centered(surface, font, text, color, center):
    img = font.render(text, False, color)  # antialias=False -> tetap pixelated
    surface.blit(img, img.get_rect(center=center))


# -------------------------------------------------------------------- Hand
class CardHand:
    def __init__(self, cards):
        self.cards = list(cards)
        self.rects = []
        self._layout()

    def _layout(self):
        # Dihitung ulang hanya saat isi tangan berubah, bukan tiap frame.
        self.rects = centered_row(
            len(self.cards), S.CARD_HAND_Y, S.CARD_WIDTH, S.CARD_HEIGHT, S.CARD_GAP
        )

    def index_at(self, pos):
        """Mouse collision: indeks kartu di bawah `pos`, atau None.
        O(n) dengan n <= 5 kartu (tidak perlu struktur data spasial)."""
        x, y = pos
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(x, y):
                return i
        return None

    def take(self, index):
        """Keluarkan kartu dari tangan (dan rapikan ulang posisi sisanya)."""
        card = self.cards.pop(index)
        self._layout()
        return card

    def draw(self, surface, font, mouse_pos=None, interactive=True):
        # Hit-test memakai rect DASAR (bukan rect yang sedang terangkat),
        # jadi tidak ada flicker di tepi atas kartu.
        hovered = self.index_at(mouse_pos) if (interactive and mouse_pos) else None

        for i, (card, base) in enumerate(zip(self.cards, self.rects)):
            is_hover = i == hovered
            rect = base.move(0, -S.CARD_HOVER_LIFT) if is_hover else base

            if not interactive:
                accent = text = S.COLORS["DIM"]
            else:
                accent = S.COLORS["WHITE"] if is_hover else card.color
                text = S.COLORS["WHITE"]

            pygame.draw.rect(surface, S.COLORS["CARD_BG"], rect)
            pygame.draw.rect(surface, accent, rect, 1)
            pygame.draw.rect(surface, accent, (rect.x, rect.y, rect.w, 4))  # pita warna atas

            _blit_centered(surface, font, card.name, text, (rect.centerx, rect.y + 14))
            _blit_centered(surface, font, card.type, accent, (rect.centerx, rect.centery + 4))
            _blit_centered(surface, font, f"PWR {card.power}", text, (rect.centerx, rect.bottom - 10))


# ---------------------------------------------------------------- Timeline
def draw_timeline(surface, font, timeline):
    for i, rect in enumerate(TIMELINE_SLOT_RECTS):
        if i < len(timeline):
            card = timeline[i]
            pygame.draw.rect(surface, card.color, rect)
            _blit_centered(surface, font, f"{i + 1}. {card.type}", S.COLORS["BLACK"], rect.center)
        else:
            pygame.draw.rect(surface, S.COLORS["GRID"], rect, 1)
            _blit_centered(surface, font, str(i + 1), S.COLORS["DIM"], rect.center)


def try_queue_card(hand, timeline, canvas_pos):
    """Klik pada `canvas_pos`: pindahkan kartu yang diklik dari tangan ke
    `timeline`. Return True bila berhasil. Pengecekan fase (PLANNING) dilakukan
    oleh pemanggil, bukan di sini (nanti oleh FSM)."""
    if len(timeline) >= S.TIMELINE_MAX_SLOTS:   # timeline penuh -> tolak
        return False
    idx = hand.index_at(canvas_pos)
    if idx is None:
        return False
    timeline.append(hand.take(idx))
    return True
