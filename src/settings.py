"""settings.py — Konstanta global Chrono-Craft.

Semua angka "ajaib" ditaruh di sini supaya modul lain tidak hardcode nilai.
"""

# --- Display -----------------------------------------------------------------
TITLE = "Chrono-Craft"
SCREEN_WIDTH = 1280      # ukuran window sebenarnya
SCREEN_HEIGHT = 720
INTERNAL_WIDTH = 480     # resolusi native (pixel-art canvas)
INTERNAL_HEIGHT = 270
FPS = 60

# Faktor skala (float). Dipakai nanti untuk konversi koordinat mouse
# window -> canvas internal (penting untuk drag & drop kartu).
SCALE_X = SCREEN_WIDTH / INTERNAL_WIDTH
SCALE_Y = SCREEN_HEIGHT / INTERNAL_HEIGHT

# Batas atas dt (detik). Mencegah "lompatan" fisika saat window di-drag/lag.
MAX_DT = 0.05

# --- Game States -------------------------------------------------------------
STATE_PLANNING = "PLANNING"   # turn-based, waktu berhenti
STATE_ACTION = "ACTION"       # real-time, fisika berjalan

# --- Colors (palet retro cyberpunk) -----------------------------------------
COLORS = {
    "BG":        (13, 2, 33),      # ungu gelap
    "GRID":      (36, 14, 74),
    "NEON_CYAN": (0, 255, 249),
    "NEON_PINK": (255, 42, 109),
    "NEON_YEL":  (249, 200, 14),
    "WHITE":     (240, 240, 255),
    "BLACK":     (0, 0, 0),
    "PANEL":     (20, 6, 46),      # latar panel UI bawah
    "CARD_BG":   (26, 12, 58),
    "DIM":       (96, 84, 130),    # teks/border nonaktif
}

# --- Physics -----------------------------------------------------------------
# Semua satuan dalam piksel canvas internal dan detik.
PHYSICS_GRAVITY = 250.0          # px/s^2 (gravitasi "ringan")
PHYSICS_FLOOR_FRICTION = 180.0   # px/s^2, perlambatan horizontal saat menyentuh lantai
PHYSICS_RESTITUTION = 0.65       # 0 = tidak memantul, 1 = pantulan sempurna
PHYSICS_REST_THRESHOLD = 12.0    # px/s, di bawah ini pantulan dianggap diam

# --- UI layout (koordinat canvas internal 480x270) -----------------------------
UI_PANEL_TOP = 176               # y awal panel bawah (timeline + tangan kartu)
ARENA_RECT = (8, 8, INTERNAL_WIDTH - 16, UI_PANEL_TOP - 12)  # x, y, w, h (bawah di y=172)

CARD_WIDTH = 72
CARD_HEIGHT = 60
CARD_GAP = 12
CARD_HAND_Y = 202
CARD_HOVER_LIFT = 4              # kartu naik sekian piksel saat di-hover

TIMELINE_MAX_SLOTS = 3           # GDD: maksimal 3 aksi berurutan
TIMELINE_SLOT_Y = 182
TIMELINE_SLOT_HEIGHT = 16
