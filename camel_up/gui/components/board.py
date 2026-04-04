import os
import pygame
import math
from typing import Dict, List, Optional, Tuple

from gui.theme import (
    BLACK, SAND_LIGHT, SAND_DARK, WOOD_DARK, WOOD_MID, WOOD_LIGHT,
    TEXT_DARK, TEXT_LIGHT, GOLD, CAMEL_COLOR_MAP,
    CAMEL_W, CAMEL_H, CAMEL_STACK_OFFSET, TILE_SIZE,
    CENTER_W, MAIN_H, WHITE, RED, load_font,
)
from gui.components.camel_sprite import CamelSprite
from game.models import CAMEL_COLORS, CRAZY_CAMEL_COLORS, ALL_CAMEL_COLORS


class Board:
    """Renders the 16-tile oval desert race track with stacked camels."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tile_positions: Dict[int, Tuple[int, int]] = self._calculate_tile_positions()
        # Sprites for all 7 camels (5 racing + 2 crazy)
        self.camel_sprites: Dict[str, CamelSprite] = {
            color: CamelSprite(color) for color in ALL_CAMEL_COLORS
        }
        self._font_small = None
        self._font_medium = None
        self._tile_select_mode = False
        self._valid_tiles: List[int] = []
        self._hovered_tile: Optional[int] = None
        self._bg_image = None   # game_background.png scaled to board size

    # ---------------------------------------------------------- board image
    def _get_bg_image(self):
        if self._bg_image is None:
            try:
                img_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'assets', 'images', 'game_background.png'
                )
                raw = pygame.image.load(img_path).convert()
                self._bg_image = pygame.transform.smoothscale(raw, (self.width, self.height))
            except Exception:
                self._bg_image = False  # draw solid fill as fallback

    # ------------------------------------------------------------------ fonts
    def _get_fonts(self):
        if self._font_small is None:
            try:
                _cinzel = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'assets', 'fonts', 'Cinzel-Bold.otf'
                )
                self._font_small = pygame.font.Font(_cinzel, 16)
            except Exception:
                self._font_small = pygame.font.SysFont('arial', 16, bold=True)
            self._font_medium = load_font(13)

    # -------------------------------------------------------- tile positions
    def _calculate_tile_positions(self) -> Dict[int, Tuple[int, int]]:
        """
        Positions matched to game_background.png (numbered stone tiles).

        Layout — 5-3-5-3, corners at tiles 1 / 5 / 9 / 13:
          Top    (1→5):   left  to right   (5 tiles, corners included)
          Right  (6→8):   top   to bottom  (3 interior, 4 equal steps)
          Bottom (9→13):  right to left    (5 tiles, corners included)
          Left  (14→16):  bottom to top    (3 interior, 4 equal steps)
          Tile 16 = FINISH (top of left column)
        """
        w, h = self.width, self.height

        # Proportional offsets of tile centres inside the board image
        LEFT   = 0.110
        RIGHT  = 0.890
        TOP    = 0.110
        BOTTOM = 0.890

        lx = self.x + round(LEFT   * w)   # left-column x
        rx = self.x + round(RIGHT  * w)   # right-column x
        ty = self.y + round(TOP    * h)   # top-row y
        by = self.y + round(BOTTOM * h)   # bottom-row y

        hs = rx - lx   # horizontal span corner-to-corner
        vs = by - ty   # vertical span corner-to-corner

        positions: Dict[int, Tuple[int, int]] = {}

        # Top row: tiles 1-5  (i = 0..4, step = hs/4)
        for i, tile in enumerate(range(1, 6)):
            positions[tile] = (round(lx + i * hs / 4), ty)

        # Right column: tiles 6-8  (steps 1-3 out of 4)
        for i, tile in enumerate(range(6, 9)):
            positions[tile] = (rx, round(ty + (i + 1) * vs / 4))

        # Bottom row: tiles 9-13  (i = 0..4, step = hs/4, rightmost first)
        for i, tile in enumerate(range(9, 14)):
            positions[tile] = (round(rx - i * hs / 4), by)

        # Left column: tiles 14-16  (steps 1-3 out of 4, counting from bottom)
        for i, tile in enumerate(range(14, 17)):
            positions[tile] = (lx, round(by - (i + 1) * vs / 4))

        return positions

    # --------------------------------------------------------------- helpers
    def get_tile_rect(self, tile_num: int) -> pygame.Rect:
        cx, cy = self.tile_positions.get(tile_num, (0, 0))
        return pygame.Rect(cx - TILE_SIZE // 2, cy - TILE_SIZE // 2, TILE_SIZE, TILE_SIZE)

    def set_tile_select_mode(self, active: bool, valid_tiles: List[int] = None):
        self._tile_select_mode = active
        self._valid_tiles = valid_tiles or []
        if not active:
            self._hovered_tile = None

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        if not self._tile_select_mode:
            self._hovered_tile = None
            return
        self._hovered_tile = None
        for tile_num in self._valid_tiles:
            if self.get_tile_rect(tile_num).collidepoint(mouse_pos):
                self._hovered_tile = tile_num
                break

    def get_clicked_tile(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        for tile_num in self._valid_tiles:
            if self.get_tile_rect(tile_num).collidepoint(mouse_pos):
                return tile_num
        return None

    def animate_camel_move(self, color: str, new_tile: int):
        if new_tile in self.tile_positions:
            target = self.tile_positions[new_tile]
            sprite = self.camel_sprites[color]
            start = sprite.pos if sprite.pos != (0.0, 0.0) else (float(target[0]), float(target[1]))
            sprite.start_animation(start, (float(target[0]), float(target[1])))

    @property
    def is_animating(self) -> bool:
        return any(s.is_animating for s in self.camel_sprites.values())

    def update(self):
        for sprite in self.camel_sprites.values():
            sprite.update()

    # --------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface, game_state):
        self._get_fonts()
        self._get_bg_image()

        # Board background image (or solid fallback)
        if self._bg_image:
            surface.blit(self._bg_image, (self.x, self.y))
        else:
            board_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(surface, SAND_LIGHT, board_rect, border_radius=12)
            pygame.draw.rect(surface, WOOD_MID, board_rect, width=3, border_radius=12)
            self._draw_track_path(surface)

        # Tiles
        for tile_num in range(1, 17):
            self._draw_tile(surface, tile_num, game_state)

        # Camels
        self._draw_all_camels(surface, game_state)

    def _draw_track_path(self, surface: pygame.Surface):
        """Background image provides the track; nothing to draw here."""
        pass

    def _draw_tile(self, surface: pygame.Surface, tile_num: int, game_state):
        if tile_num not in self.tile_positions:
            return
        rect = self.get_tile_rect(tile_num)

        if self._tile_select_mode and tile_num in self._valid_tiles:
            fill   = (180, 230, 160) if self._hovered_tile != tile_num else (130, 205, 110)
            border = (40, 160, 40)
            pygame.draw.rect(surface, fill, rect, border_radius=10)
            pygame.draw.rect(surface, border, rect, width=3, border_radius=10)


        # Desert marker
        if game_state:
            dt = game_state.desert_tiles.get(tile_num)
            if dt:
                dtype = dt.get('type', dt) if isinstance(dt, dict) else dt
                if dtype == 'oasis':
                    self._draw_oasis_icon(surface, rect)
                elif dtype == 'mirage':
                    self._draw_mirage_icon(surface, rect)

        # Finish-line marker on tile 16
        # if tile_num == 16:
        #     fin = self._font_small.render("Finish", True, BLACK)
        #     surface.blit(fin, (rect.x + 2, rect.bottom - 25))

    def _draw_oasis_icon(self, surface: pygame.Surface, r: pygame.Rect):
        cx, cy = r.centerx, r.centery + 6
        pygame.draw.rect(surface, (120, 80, 30), pygame.Rect(cx - 2, cy - 6, 4, 10))
        pygame.draw.circle(surface, (34, 139, 34), (cx, cy - 10), 7)
        pygame.draw.circle(surface, (34, 139, 34), (cx - 6, cy - 6), 5)
        pygame.draw.circle(surface, (34, 139, 34), (cx + 6, cy - 6), 5)
        lbl = self._font_small.render("+1", True, (0, 140, 0))
        surface.blit(lbl, (cx - 6, cy + 4))

    def _draw_mirage_icon(self, surface: pygame.Surface, r: pygame.Rect):
        cx, cy = r.centerx, r.centery + 8
        pts = [(cx - 10 + i, cy + int(math.sin(i * 0.7) * 3)) for i in range(20)]
        if len(pts) > 1:
            pygame.draw.lines(surface, RED, False, pts, 2)
        lbl = self._font_small.render("-1", True, RED)
        surface.blit(lbl, (cx - 6, cy + 5))

    def _draw_all_camels(self, surface: pygame.Surface, game_state):
        if not game_state:
            return

        tile_camels: Dict[int, list] = {}
        for camel in game_state.camels:
            if camel.position > 0:
                tile_camels.setdefault(camel.position, []).append(camel)

        for tile_num, camels in tile_camels.items():
            if tile_num not in self.tile_positions:
                continue
            camels_sorted = sorted(camels, key=lambda c: c.stack_order)
            tile_rect = self.get_tile_rect(tile_num)
            n = len(camels_sorted)
            stack_h = CAMEL_H + (n - 1) * CAMEL_STACK_OFFSET
            base_x = tile_rect.centerx - CAMEL_W // 2
            base_y = tile_rect.centery - stack_h // 2 + (n - 1) * CAMEL_STACK_OFFSET

            for i, camel in enumerate(camels_sorted):
                dx = base_x
                dy = base_y - i * CAMEL_STACK_OFFSET
                sprite = self.camel_sprites[camel.color]
                if sprite.is_animating:
                    sprite.draw(surface)
                else:
                    sprite.draw(surface, dx, dy)
                    sprite.pos = (float(dx), float(dy))
                    sprite.target_pos = sprite.pos

                # Draw ← indicator on crazy camels so the player can see direction
                if camel.is_crazy and not sprite.is_animating:
                    arrow_surf = self._font_small.render("←", True, (240, 90, 90))
                    surface.blit(arrow_surf, (dx + CAMEL_W - 2, dy - 2))
