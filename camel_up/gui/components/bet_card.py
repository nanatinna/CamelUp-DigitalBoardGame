import pygame
from gui.theme import (
    PARCHMENT, PARCHMENT_DARK, TEXT_DARK, WOOD_DARK, WOOD_MID,
    GOLD, CAMEL_COLOR_MAP, WHITE, load_font,
)
from game.models import CAMEL_COLORS


class BetCard:
    """Right-panel widget showing available leg-betting tiles for each camel."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._font = None
        self._font_small = None
        self._font_title = None
        self.hovered_color = None
        self.selected_color = None
        self.interactive = False
        self.callback = None          # callable(color: str)

    def _get_fonts(self):
        if self._font is None:
            self._font       = load_font(13)
            self._font_small = load_font(11)
            self._font_title = load_font(15)

    # -------------------------------------------------------------- geometry
    def _card_rect(self, idx: int) -> pygame.Rect:
        card_h  = 44
        padding = 4
        y = self.rect.y + 30 + idx * (card_h + padding)
        return pygame.Rect(self.rect.x + 4, y, self.rect.width - 8, card_h)

    def _color_at(self, pos: tuple, available: dict):
        for idx, color in enumerate(CAMEL_COLORS):
            if self._card_rect(idx).collidepoint(pos) and available.get(color):
                return color
        return None

    # --------------------------------------------------------------- events
    def handle_event(self, event: pygame.event.Event, available_leg_bets: dict):
        if not self.interactive:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            color = self._color_at(event.pos, available_leg_bets)
            if color:
                self.selected_color = color
                if self.callback:
                    self.callback(color)
        elif event.type == pygame.MOUSEMOTION:
            self.hovered_color = self._color_at(event.pos, available_leg_bets)

    # --------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface, available_leg_bets: dict):
        self._get_fonts()

        pygame.draw.rect(surface, WOOD_DARK, self.rect, border_radius=8)
        pygame.draw.rect(surface, (139, 94, 60), self.rect, width=2, border_radius=8)

        title = self._font_title.render("LEG BETS", True, GOLD)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 6))

        for idx, color in enumerate(CAMEL_COLORS):
            card_rect = self._card_rect(idx)
            tiles = available_leg_bets.get(color, [])

            is_empty    = len(tiles) == 0
            is_hovered  = self.hovered_color == color and self.interactive and not is_empty
            is_selected = self.selected_color == color

            if is_empty:
                bg_col     = (50, 40, 30)
                text_col   = (100, 85, 60)
                border_col = (70, 55, 35)
            elif is_selected:
                bg_col     = (200, 170, 90)
                text_col   = TEXT_DARK
                border_col = GOLD
            elif is_hovered:
                bg_col     = (220, 200, 150)
                text_col   = TEXT_DARK
                border_col = PARCHMENT_DARK
            else:
                bg_col     = PARCHMENT
                text_col   = TEXT_DARK
                border_col = PARCHMENT_DARK

            pygame.draw.rect(surface, bg_col,     card_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, card_rect, width=2, border_radius=6)

            # Camel colour swatch
            swatch = pygame.Rect(card_rect.x + 6, card_rect.y + 8, 28, 28)
            pygame.draw.rect(surface, CAMEL_COLOR_MAP.get(color, (128, 128, 128)), swatch, border_radius=5)
            pygame.draw.rect(surface, WHITE, swatch, width=1, border_radius=5)
            letter = self._font.render(color[0].upper(), True, WHITE)
            surface.blit(letter, letter.get_rect(center=swatch.center))

            # Name
            surface.blit(self._font.render(color.capitalize(), True, text_col),
                         (card_rect.x + 42, card_rect.y + 6))

            # Tile values
            if tiles:
                vals = " / ".join(str(v) for v in tiles)
                vals_surf = self._font_small.render(f"Tiles: {vals}", True, text_col)
            else:
                vals_surf = self._font_small.render("All taken", True, (150, 120, 80))
            surface.blit(vals_surf, (card_rect.x + 42, card_rect.y + 22))

            # Next payout
            if tiles:
                pay = self._font_title.render(str(tiles[0]), True, TEXT_DARK)
                surface.blit(pay, (card_rect.right - 28, card_rect.centery - 8))
