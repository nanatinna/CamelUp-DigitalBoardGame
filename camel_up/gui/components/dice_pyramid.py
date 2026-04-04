import math
import pygame
from gui.theme import WOOD_DARK, WOOD_MID, GOLD, TEXT_LIGHT, CAMEL_COLOR_MAP, WHITE, load_font
from game.models import CAMEL_COLORS


class DicePyramid:
    """
    Dice Tracker panel (right panel, lower half).

    Shows one coloured tile per die:
      • 5 racing dice  (green / purple / yellow / blue / red)
      • 1 grey die     (moves a random crazy camel backward)

    Unrevealed dice show "?" in their full colour.
    Revealed dice show the rolled value, dimmed.
    A "Last Roll" banner at the bottom shows the most-recent result.
    """

    # Tile dimensions & layout
    _TILE_W   = 42
    _TILE_H   = 42
    _TILE_GAP = 7

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._font_title = None
        self._font_label = None
        self._font_big   = None
        self._font_small = None
        self._font_tiny  = None

        # Track rolled values for the current leg: color -> int
        self._rolled: dict[str, int] = {}
        self._prev_racing_remaining = 5  # detect leg reset

        # Pop animation
        self._pop_color    = None
        self._pop_result   = None   # (color, value, is_crazy, camel_moved)
        self._pop_progress = 0.0
        self._pop_active   = False

    # ---------------------------------------------------------------- fonts
    def _get_fonts(self):
        if self._font_title is None:
            self._font_title = load_font(13)
            self._font_label = load_font(10)
            self._font_big   = load_font(18)
            self._font_small = load_font(12)
            self._font_tiny  = load_font(10)

    # --------------------------------------------------------- animation API
    def animate_roll(self, die_color: str, value: int, camel_moved: str = None):
        is_crazy = die_color == 'grey'
        self._rolled[die_color] = value
        self._pop_color    = die_color
        self._pop_result   = (die_color, value, is_crazy, camel_moved)
        self._pop_progress = 0.0
        self._pop_active   = True

    def update(self):
        if self._pop_active:
            self._pop_progress += 0.05
            if self._pop_progress >= 1.0:
                self._pop_progress = 1.0
                self._pop_active   = False

    # ----------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, dice_remaining: list):
        self._get_fonts()

        # Detect new leg: all racing dice are back → clear history
        racing_remaining = sum(1 for c in dice_remaining if c != 'grey')
        if racing_remaining == 5 and self._prev_racing_remaining < 5:
            self._rolled = {}
        self._prev_racing_remaining = racing_remaining

        # Panel background
        pygame.draw.rect(surface, WOOD_DARK, self.rect, border_radius=8)
        pygame.draw.rect(surface, WOOD_MID,  self.rect, width=2, border_radius=8)

        cx = self.rect.centerx
        r  = self.rect

        # ── Title ────────────────────────────────────────────────────────────
        title = self._font_title.render("DICE TRACKER", True, GOLD)
        surface.blit(title, (cx - title.get_width() // 2, r.y + 10))

        # ── Racing dice row ──────────────────────────────────────────────────
        row_label = self._font_tiny.render("RACING DICE", True, (180, 160, 100))
        surface.blit(row_label, (cx - row_label.get_width() // 2, r.y + 30))

        total_w = len(CAMEL_COLORS) * self._TILE_W + (len(CAMEL_COLORS) - 1) * self._TILE_GAP
        start_x = cx - total_w // 2
        tile_y  = r.y + 48

        for i, color in enumerate(CAMEL_COLORS):
            tx = start_x + i * (self._TILE_W + self._TILE_GAP)
            self._draw_die_tile(surface, tx, tile_y, color, dice_remaining)

        # ── Separator ────────────────────────────────────────────────────────
        sep_y = tile_y + self._TILE_H + 20
        pygame.draw.line(surface, WOOD_MID, (r.x + 16, sep_y), (r.right - 16, sep_y), 1)

        # ── Grey die row ─────────────────────────────────────────────────────
        grey_label = self._font_tiny.render("GREY DICE  (moves black or white \u2190)", True, (200, 120, 120))
        surface.blit(grey_label, (cx - grey_label.get_width() // 2, sep_y + 10))

        grey_tile_y = sep_y + 26
        grey_tile_x = cx - self._TILE_W // 2
        self._draw_die_tile(surface, grey_tile_x, grey_tile_y, 'grey', dice_remaining)

        # ── Last roll result ─────────────────────────────────────────────────
        result_y = grey_tile_y + self._TILE_H + 22
        self._draw_last_roll(surface, r, result_y)

    # ─── Tile helper ─────────────────────────────────────────────────────────
    def _draw_die_tile(self, surface, tx, ty, color, dice_remaining):
        remaining = color in dice_remaining
        base_rgb  = CAMEL_COLOR_MAP.get(color, (128, 128, 128))

        # Pop animation: bounce upward slightly
        offset_y = 0
        if self._pop_active and self._pop_color == color:
            offset_y = int(-20 * math.sin(self._pop_progress * math.pi))

        rect = pygame.Rect(tx, ty + offset_y, self._TILE_W, self._TILE_H)

        if remaining:
            fill_color = base_rgb
            border_col = WHITE
            label_col  = WHITE
        else:
            fill_color = tuple(max(28, c // 3) for c in base_rgb)
            border_col = (80, 65, 50)
            label_col  = (130, 110, 80)

        pygame.draw.rect(surface, fill_color, rect, border_radius=7)
        pygame.draw.rect(surface, border_col, rect, width=2, border_radius=7)

        # Inner label: "?" if still in pyramid, rolled value if used
        if remaining:
            lbl = self._font_big.render("?", True, label_col)
        else:
            val = self._rolled.get(color)
            text = str(val) if val is not None else "\u2713"
            lbl = self._font_big.render(text, True, label_col)

        surface.blit(lbl, lbl.get_rect(center=rect.center))

        # Color initial below tile
        init = self._font_tiny.render(color[0].upper(), True,
                                      TEXT_LIGHT if remaining else (90, 75, 55))
        surface.blit(init, (rect.centerx - init.get_width() // 2,
                            rect.bottom + 5))

    # ─── Last roll banner ────────────────────────────────────────────────────
    def _draw_last_roll(self, surface, panel_rect, y):
        if not self._pop_result:
            hint = self._font_tiny.render("No roll yet this leg", True, (110, 90, 60))
            surface.blit(hint,
                         (panel_rect.centerx - hint.get_width() // 2, y))
            return

        die_color, value, is_crazy, camel_moved = self._pop_result
        arrow = "\u2190" if is_crazy else "\u2192"

        # Banner box
        bw, bh = panel_rect.width - 20, 44
        bx = panel_rect.x + 10
        banner = pygame.Rect(bx, y, bw, bh)
        pygame.draw.rect(surface, (50, 32, 10), banner, border_radius=8)
        pygame.draw.rect(surface, GOLD, banner, width=2, border_radius=8)

        # Color swatch
        swatch = pygame.Rect(bx + 8, banner.centery - 12, 24, 24)
        swatch_col = CAMEL_COLOR_MAP.get(die_color, (128, 128, 128))
        pygame.draw.rect(surface, swatch_col, swatch, border_radius=4)
        pygame.draw.rect(surface, WHITE, swatch, width=1, border_radius=4)

        # Text
        cx = panel_rect.centerx
        if is_crazy and camel_moved:
            line1 = f"GREY {arrow} {value}"
            line2 = f"moved {camel_moved.upper()}"
        else:
            line1 = f"{die_color.upper()} {arrow} {value}"
            line2 = "Last Roll"

        l1 = self._font_small.render(line1, True, GOLD)
        l2 = self._font_tiny.render(line2, True, TEXT_LIGHT)
        surface.blit(l1, (bx + 40, banner.y + 6))
        surface.blit(l2, (bx + 40, banner.y + 26))
