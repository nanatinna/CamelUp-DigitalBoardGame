import pygame
import pygame_gui

from gui.theme import (
    WOOD_DARK, WOOD_MID, GOLD, TEXT_LIGHT, WHITE, BLACK,
    WINDOW_W, WINDOW_H, generate_background_surface, load_font,
)
from storage.history import GameHistory


class EndScreen:
    """Victory screen: fade-in overlay, winner, scores, play-again / menu."""

    def __init__(self, app, game):
        self.app   = app
        self.game  = game
        self.state = game.get_state()
        self.ui_manager  = app.ui_manager
        self._background = None
        self._font_title = None
        self._font       = None
        self._font_small = None

        self._overlay_alpha = 0
        self._fade_done     = False

        # Save result
        try:
            duration = (pygame.time.get_ticks() - getattr(app, '_game_start_time', 0)) // 1000
            GameHistory().record_game(self.state, duration)
        except Exception:
            pass

        cx = WINDOW_W // 2
        self.replay_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx - 220, 690, 200, 48),
            text='Play Again',
            manager=self.ui_manager,
        )
        self.menu_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx + 20, 690, 200, 48),
            text='Main Menu',
            manager=self.ui_manager,
        )

    def _get_fonts(self):
        if self._font_title is None:
            self._font_title = load_font(52)
            self._font       = load_font(18)
            self._font_small = load_font(14)

    def _kill_ui(self):
        self.replay_btn.kill()
        self.menu_btn.kill()

    # --------------------------------------------------------------- events
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.replay_btn:
                self._kill_ui()
                self.app.start_new_game([p.name for p in self.state.players])
            elif event.ui_element == self.menu_btn:
                self._kill_ui()
                self.app.show_start_screen()

    # --------------------------------------------------------------- update
    def update(self, time_delta: float):
        if not self._fade_done:
            self._overlay_alpha = min(180, self._overlay_alpha + 6)
            if self._overlay_alpha >= 180:
                self._fade_done = True

    # --------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface):
        self._get_fonts()

        if self._background is None:
            self._background = generate_background_surface(WINDOW_W, WINDOW_H)
        surface.blit(self._background, (0, 0))

        # Dark fade overlay
        ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, self._overlay_alpha))
        surface.blit(ov, (0, 0))

        # Result panel
        pw, ph = 700, 560
        px = WINDOW_W  // 2 - pw // 2
        py = WINDOW_H  // 2 - ph // 2 - 30
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(surface, WOOD_DARK, panel, border_radius=16)
        pygame.draw.rect(surface, GOLD,      panel, width=3, border_radius=16)

        # Winner text
        winner = self.state.winner or "Unknown"
        sh = self._font_title.render(f"Winner: {winner}!", True, BLACK)
        ti = self._font_title.render(f"Winner: {winner}!", True, GOLD)
        tx = panel.centerx - ti.get_width() // 2
        surface.blit(sh, (tx + 2, py + 22))
        surface.blit(ti, (tx,     py + 20))

        # Scores table
        tx_l  = panel.x + 40
        ty    = py + 88
        cols  = [tx_l, tx_l + 80, tx_l + 320]
        for ci, hdr in enumerate(['Rank', 'Player', 'Final Coins']):
            surface.blit(self._font.render(hdr, True, GOLD), (cols[ci], ty))
        pygame.draw.line(surface, GOLD, (tx_l, ty + 26), (panel.right - 40, ty + 26), 2)

        sorted_p = sorted(self.state.players, key=lambda p: p.coins, reverse=True)
        for ri, player in enumerate(sorted_p):
            ry = ty + 36 + ri * 38
            rb = pygame.Rect(tx_l - 5, ry - 4, pw - 70, 32)
            pygame.draw.rect(surface, (70, 45, 15) if ri % 2 == 0 else (52, 33, 9), rb, border_radius=4)
            tc = GOLD if player.name == winner else TEXT_LIGHT
            surface.blit(self._font.render(f"#{ri + 1}",            True, tc), (cols[0], ry))
            surface.blit(self._font.render(player.name,             True, tc), (cols[1], ry))
            surface.blit(self._font.render(f"{player.coins} coins", True, tc), (cols[2], ry))

        stats_y = ty + 36 + len(sorted_p) * 38 + 12
        pygame.draw.line(surface, (139, 94, 60), (tx_l, stats_y),
                         (panel.right - 40, stats_y), 1)
        surface.blit(self._font_small.render(f"Total Legs: {self.state.leg_number}",  True, TEXT_LIGHT), (tx_l,       stats_y + 8))
        surface.blit(self._font_small.render(f"Total Turns: {self.state.turn_number}", True, TEXT_LIGHT), (tx_l + 200, stats_y + 8))
