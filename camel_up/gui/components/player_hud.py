import pygame
from gui.theme import (
    WOOD_DARK, WOOD_MID, WOOD_LIGHT, TEXT_LIGHT, TEXT_DARK,
    GOLD, WHITE, load_font,
)


class PlayerHud:
    """Left panel: player list, coins, bets, and action buttons."""

    # (action_key, card_title, card_desc, icon_base_color)
    _ACTIONS = [
        ('roll',        'Take Pyramid Tile', 'Roll dice (+1 EP)',          (80,  80,  200)),
        ('leg_bet',     'Leg Betting',       'Bet leg leader (5/3/2 EP)',  (200, 160, 30)),
        ('desert_tile', 'Place Desert Tile', 'Oasis or Mirage (+1 EP)',    (40,  160, 60)),
        ('race_bet',    'Race Bet',          'Overall winner/loser',       (190, 60,  60)),
    ]

    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self._font       = None
        self._font_small = None
        self._font_title = None
        self._font_large = None
        self._font_desc  = None
        self.btn_rects:     dict = {}
        self.hovered_btn:   str | None = None
        self.disabled_btns: set = set()

    def _get_fonts(self):
        if self._font is None:
            self._font       = load_font(13)
            self._font_small = load_font(11)
            self._font_title = load_font(13)
            self._font_large = load_font(16)
            self._font_desc  = load_font(10)

    # --------------------------------------------------------------- events
    def handle_event(self, event: pygame.event.Event):
        """Returns action key string if a button is clicked, else None."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered_btn = None
            for name, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos) and name not in self.disabled_btns:
                    self.hovered_btn = name
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, rect in self.btn_rects.items():
                if rect.collidepoint(event.pos) and name not in self.disabled_btns:
                    return name
        return None

    # ─── Icon drawing helpers ───────────────────────────────────────────────

    def _draw_icon_bg(self, surface, rect, color):
        pygame.draw.rect(surface, color, rect, border_radius=6)
        darker = tuple(max(0, c - 50) for c in color)
        pygame.draw.rect(surface, darker, rect, width=2, border_radius=6)

    def _draw_die_icon(self, surface, rect, color):
        """Die face: square + 5 dots."""
        self._draw_icon_bg(surface, rect, color)
        cx, cy = rect.centerx, rect.centery
        dot = WHITE
        for dx, dy in [(-6, -6), (6, -6), (0, 0), (-6, 6), (6, 6)]:
            pygame.draw.circle(surface, dot, (cx + dx, cy + dy), 3)

    def _draw_trophy_icon(self, surface, rect, color):
        """Simple trophy cup."""
        self._draw_icon_bg(surface, rect, color)
        cx, cy = rect.centerx, rect.centery
        c = WHITE
        # Cup bowl (arc approximated by two lines + top curve)
        pygame.draw.arc(surface, c,
                        pygame.Rect(cx - 8, cy - 10, 16, 14), 3.14159, 0, 3)
        # Stem
        pygame.draw.line(surface, c, (cx, cy + 3), (cx, cy + 9), 2)
        # Base
        pygame.draw.line(surface, c, (cx - 6, cy + 9), (cx + 6, cy + 9), 2)
        # Handles
        pygame.draw.arc(surface, c, pygame.Rect(cx - 13, cy - 8, 8, 10),
                        1.0, 2.14, 2)
        pygame.draw.arc(surface, c, pygame.Rect(cx + 5, cy - 8, 8, 10),
                        1.0, 2.14, 2)

    def _draw_palm_icon(self, surface, rect, color):
        """Simplified palm tree."""
        self._draw_icon_bg(surface, rect, color)
        cx, cy = rect.centerx, rect.centery
        c = WHITE
        # Trunk
        pygame.draw.line(surface, c, (cx, cy + 9), (cx + 2, cy - 2), 2)
        # Left leaf
        pygame.draw.polygon(surface, c, [
            (cx, cy - 2), (cx - 9, cy - 8), (cx - 2, cy - 1)])
        # Right leaf
        pygame.draw.polygon(surface, c, [
            (cx + 2, cy - 2), (cx + 9, cy - 8), (cx + 3, cy - 1)])
        # Top leaf
        pygame.draw.polygon(surface, c, [
            (cx + 1, cy - 4), (cx - 4, cy - 11), (cx + 6, cy - 9)])

    def _draw_flag_icon(self, surface, rect, color):
        """Flagpole + waving flag."""
        self._draw_icon_bg(surface, rect, color)
        cx, cy = rect.centerx, rect.centery
        c = WHITE
        # Pole
        pygame.draw.line(surface, c, (cx - 4, cy + 9), (cx - 4, cy - 9), 2)
        # Flag triangle
        pygame.draw.polygon(surface, c, [
            (cx - 4, cy - 9), (cx + 8, cy - 4), (cx - 4, cy)])

    # --------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface, game_state, valid_actions: list):
        self._get_fonts()
        self.disabled_btns = set()

        pygame.draw.rect(surface, WOOD_DARK, self.rect)
        pygame.draw.rect(surface, WOOD_MID,  self.rect, width=2)

        # Panel title
        title = self._font_large.render("PLAYERS", True, GOLD)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 6))

        # Player rows
        py = self.rect.y + 30
        for i, player in enumerate(game_state.players):
            is_current = (i == game_state.current_player_idx)
            pr = pygame.Rect(self.rect.x + 4, py, self.rect.width - 8, 52)

            if is_current:
                pygame.draw.rect(surface, (80, 55, 22), pr, border_radius=6)
                pygame.draw.rect(surface, GOLD, pr, width=2, border_radius=6)
            else:
                pygame.draw.rect(surface, (50, 30, 10), pr, border_radius=6)
                pygame.draw.rect(surface, WOOD_MID, pr, width=1, border_radius=6)

            name_col = GOLD if is_current else TEXT_LIGHT
            surface.blit(self._font_title.render(player.name[:14], True, name_col),
                         (pr.x + 6, pr.y + 4))
            surface.blit(self._font.render(f"Coins: {player.coins}", True, GOLD),
                         (pr.x + 6, pr.y + 20))
            bets_txt = f"Leg: {len(player.leg_bets)}  Race: {len(player.race_bets)}"
            surface.blit(self._font_small.render(bets_txt, True, TEXT_LIGHT),
                         (pr.x + 6, pr.y + 36))
            if player.desert_tile:
                dtype = player.desert_tile.get('type', '?')
                label = "Oasis" if dtype == 'oasis' else "Mirage"
                di = self._font_small.render(label, True, (140, 220, 100))
                surface.blit(di, (pr.right - di.get_width() - 6, pr.y + 20))

            py += 58

        # ── Action buttons — card style ──────────────────────────────────────
        bx  = self.rect.x + 6
        by  = py + 12
        bw  = self.rect.width - 12   # 228 px
        bh  = 58
        gap = 8

        icon_size   = 36
        icon_pad    = 8   # gap between left edge and icon
        text_x_off  = icon_pad + icon_size + 8  # text starts here from button left

        icon_drawers = {
            'roll':        self._draw_die_icon,
            'leg_bet':     self._draw_trophy_icon,
            'desert_tile': self._draw_palm_icon,
            'race_bet':    self._draw_flag_icon,
        }

        self.btn_rects = {}
        for action, label, desc, icon_color in self._ACTIONS:
            br = pygame.Rect(bx, by, bw, bh)
            self.btn_rects[action] = br
            available = action in valid_actions
            if not available:
                self.disabled_btns.add(action)

            hovered = (self.hovered_btn == action and available)

            # Color scheme per state
            if not available:
                card_bg     = (30, 18,  8)
                card_border = (55, 38, 18)
                title_col   = (80, 65, 45)
                desc_col    = (60, 50, 35)
                _icon_color = tuple(max(20, c // 4) for c in icon_color)
            elif hovered:
                card_bg     = (90, 62, 28)
                card_border = GOLD
                title_col   = WHITE
                desc_col    = TEXT_LIGHT
                _icon_color = tuple(min(255, int(c * 1.2)) for c in icon_color)
            else:
                card_bg     = (52, 32, 12)
                card_border = (130, 100, 52)
                title_col   = TEXT_LIGHT
                desc_col    = (170, 148, 100)
                _icon_color = icon_color

            # Card background
            pygame.draw.rect(surface, card_bg, br, border_radius=10)
            pygame.draw.rect(surface, card_border, br, width=2, border_radius=10)

            # Left accent bar
            accent_rect = pygame.Rect(br.x + 2, br.y + 6, 3, br.height - 12)
            pygame.draw.rect(surface, _icon_color if available else card_border,
                             accent_rect, border_radius=2)

            # Icon box
            icon_rect = pygame.Rect(br.x + icon_pad, br.centery - icon_size // 2,
                                    icon_size, icon_size)
            draw_fn = icon_drawers.get(action)
            if draw_fn:
                draw_fn(surface, icon_rect, _icon_color)

            # Title text
            tx = br.x + text_x_off
            t_surf = self._font_title.render(label, True, title_col)
            surface.blit(t_surf, (tx, br.y + 13))

            # Description text
            d_surf = self._font_desc.render(desc, True, desc_col)
            surface.blit(d_surf, (tx, br.y + 33))

            by += bh + gap

        # Status info at bottom
        iy = self.rect.bottom - 46
        surface.blit(self._font_small.render(f"Leg: {game_state.leg_number}", True, TEXT_LIGHT),
                     (self.rect.x + 8, iy))
        surface.blit(self._font_small.render(f"Turn: {game_state.turn_number}", True, TEXT_LIGHT),
                     (self.rect.x + 8, iy + 16))
