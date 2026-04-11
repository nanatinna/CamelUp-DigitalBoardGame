import pygame
import pygame_gui
import os

from gui.theme import (
    SAND_LIGHT, WOOD_DARK, WOOD_MID, TEXT_LIGHT, TEXT_DARK,
    GOLD, PARCHMENT_DARK, WINDOW_W, WINDOW_H,
    generate_background_surface, load_font,
)
from storage.database import get_leaderboard, init_db


class StartScreen:
    """Title / lobby screen with player-count selector, name inputs, leaderboard."""

    _DEFAULT_NAMES = ['Alice', 'Bob', 'Carol', 'Dave']

    def __init__(self, app):
        self.app = app
        self.ui_manager  = app.ui_manager
        self._background = None
        self._logo       = None
        self._font_title = None
        self._font_sub   = None
        self._font       = None
        self._font_small = None

        self.player_count  = 2
        self.count_buttons: dict = {}
        self.name_entries:  list = []
        self.start_button        = None
        self.htp_button          = None   # How to Play
        self.leaderboard_data    = []
        self._show_htp           = False  # overlay visible?
        self._htp_close_btn      = None

        self._setup_ui()

    # ---------------------------------------------------------------- setup
    def _setup_ui(self):
        try:
            init_db()
            self.leaderboard_data = get_leaderboard(10)
        except Exception:
            self.leaderboard_data = []

        cx = WINDOW_W // 2

        # Player-count toggle buttons
        for i, count in enumerate([2, 3, 4]):
            bx = cx - 110 + i * 80
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(bx, 320, 60, 36),
                text=str(count),
                manager=self.ui_manager,
            )
            self.count_buttons[count] = btn

        # Name-entry fields
        for i in range(4):
            entry = pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(cx - 120, 380 + i * 50, 240, 36),
                manager=self.ui_manager,
            )
            entry.set_text(self._DEFAULT_NAMES[i])
            self.name_entries.append(entry)

        # Start button
        self.start_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx - 100, 600, 200, 48),
            text='START GAME',
            manager=self.ui_manager,
        )

        # How to Play button
        self.htp_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx - 100, 658, 200, 36),
            text='HOW TO PLAY',
            manager=self.ui_manager,
        )

        self._refresh_entries()

    def _refresh_entries(self):
        for i, entry in enumerate(self.name_entries):
            if i < self.player_count:
                entry.show()
            else:
                entry.hide()

    # ---------------------------------------------------------------- logo
    def _get_logo(self):
        if self._logo is None:
            try:
                logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'images', 'logo.png')
                img = pygame.image.load(logo_path).convert_alpha()
                w, h = img.get_size()
                max_w, max_h = 520, 210
                scale = min(max_w / w, max_h / h)
                self._logo = pygame.transform.smoothscale(
                    img, (int(w * scale), int(h * scale)))
            except Exception:
                self._logo = False

    # ---------------------------------------------------------------- fonts
    def _get_fonts(self):
        if self._font_title is None:
            self._font_title = load_font(56)
            self._font_sub   = load_font(24)
            self._font       = load_font(16)
            self._font_small = load_font(13)

    # --------------------------------------------------------------- events
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame_gui.UI_BUTTON_PRESSED:
            return

        # How-to-play close button
        if self._htp_close_btn and event.ui_element == self._htp_close_btn:
            self._close_htp()
            return

        # Ignore other inputs while overlay is open
        if self._show_htp:
            return

        for count, btn in self.count_buttons.items():
            if event.ui_element == btn:
                self.player_count = count
                self._refresh_entries()
                return

        if event.ui_element == self.start_button:
            self._start_game()
        elif event.ui_element == self.htp_button:
            self._open_htp()

    def _get_names(self):
        names = []
        for i in range(self.player_count):
            t = self.name_entries[i].get_text().strip()
            names.append(t or f"Player {i + 1}")
        return names

    def _start_game(self):
        names = self._get_names()
        self._kill_ui()
        self.app.start_new_game(names)

    def _all_main_ui(self):
        """Yield every main-screen UI element."""
        yield from self.count_buttons.values()
        yield from self.name_entries
        if self.start_button:
            yield self.start_button
        if self.htp_button:
            yield self.htp_button

    def _open_htp(self):
        self._show_htp = True
        # Hide all main UI so nothing bleeds through the overlay
        for el in self._all_main_ui():
            el.hide()
        cx, cy = WINDOW_W // 2, WINDOW_H // 2
        self._htp_close_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx - 80, cy + 230, 160, 40),
            text='CLOSE',
            manager=self.ui_manager,
        )

    def _close_htp(self):
        self._show_htp = False
        if self._htp_close_btn:
            self._htp_close_btn.kill()
            self._htp_close_btn = None
        # Restore main UI
        for el in self._all_main_ui():
            el.show()
        # Re-apply visibility rules for name entries
        self._refresh_entries()

    def _kill_ui(self):
        self._close_htp()
        for btn in self.count_buttons.values():
            btn.kill()
        for e in self.name_entries:
            e.kill()
        if self.start_button:
            self.start_button.kill()
        if self.htp_button:
            self.htp_button.kill()

    # --------------------------------------------------------------- update
    def update(self, time_delta: float):
        pass

    # --------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface):
        self._get_fonts()
        self._get_logo()

        if self._background is None:
            self._background = generate_background_surface(WINDOW_W, WINDOW_H)
        surface.blit(self._background, (0, 0))

        cx = WINDOW_W // 2

        # Logo / Title
        if self._logo:
            lx = cx - self._logo.get_width() // 2
            surface.blit(self._logo, (lx, 55))
            logo_bottom = 55 + self._logo.get_height()
        else:
            shadow = self._font_title.render("CAMEL UP", True, (40, 20, 5))
            title  = self._font_title.render("CAMEL UP", True, GOLD)
            tx = cx - title.get_width() // 2
            surface.blit(shadow, (tx + 3, 103))
            surface.blit(title,  (tx, 100))
            logo_bottom = 168

        # Sub-title
        sub = self._font_sub.render("The Desert Racing Game", True, TEXT_DARK)
        surface.blit(sub, (cx - sub.get_width() // 2, logo_bottom - 30))

        # Count label
        cl = self._font.render("Number of Players:", True, TEXT_DARK)
        surface.blit(cl, (cx - cl.get_width() // 2, 296))

        # Gold ring around selected count
        for count, btn in self.count_buttons.items():
            if count == self.player_count:
                pygame.draw.rect(surface, GOLD, btn.rect.inflate(6, 6), width=3, border_radius=10)

        # Name field labels
        for i in range(self.player_count):
            lbl = self._font.render(f"Player {i + 1}:", True, TEXT_DARK)
            surface.blit(lbl, (cx - 200, 388 + i * 50))

        # Leaderboard panel (left side)
        ROW_H   = 28
        MAX_ROWS = 8
        lx, lw  = 42, 326
        ly      = 270
        lh      = 58 + MAX_ROWS * ROW_H + 10   # title + header + rows + padding

        lb_bg = pygame.Rect(lx, ly, lw, lh)
        pygame.draw.rect(surface, WOOD_DARK, lb_bg, border_radius=10)
        pygame.draw.rect(surface, WOOD_MID,  lb_bg, width=2, border_radius=10)

        # Title
        lb_title = self._font.render("TOP PLAYERS", True, GOLD)
        surface.blit(lb_title, (lx + lw // 2 - lb_title.get_width() // 2, ly + 10))

        # Title underline
        pygame.draw.line(surface, GOLD,
                         (lx + 14, ly + 30), (lx + lw - 14, ly + 30), 1)

        # Column positions: rank | name | wins | avg
        cx0 = lx + 10   # rank
        cx1 = lx + 38   # name
        cx2 = lx + 210  # wins
        cx3 = lx + 272  # avg

        # Column headers
        hy = ly + 36
        for col_x, hdr in [(cx0, '#'), (cx1, 'Player'), (cx2, 'Wins'), (cx3, 'Avg')]:
            h = self._font_small.render(hdr, True, (200, 175, 110))
            surface.blit(h, (col_x, hy))

        # Header separator
        pygame.draw.line(surface, WOOD_MID,
                         (lx + 14, hy + 18), (lx + lw - 14, hy + 18), 1)

        if self.leaderboard_data:
            rank_colors = [
                (212, 175, 55),   # gold  — 1st
                (180, 180, 180),  # silver — 2nd
                (180, 120, 60),   # bronze — 3rd
            ]
            for ri, row in enumerate(self.leaderboard_data[:MAX_ROWS]):
                ry = hy + 22 + ri * ROW_H

                # Alternating row tint
                if ri % 2 == 0:
                    row_bg = pygame.Rect(lx + 4, ry - 2, lw - 8, ROW_H - 2)
                    pygame.draw.rect(surface, (75, 48, 18), row_bg, border_radius=4)

                rc = rank_colors[ri] if ri < 3 else TEXT_LIGHT

                # Rank number
                rank_surf = self._font_small.render(str(ri + 1), True, rc)
                surface.blit(rank_surf, (cx0, ry + 4))

                # Name
                name_surf = self._font_small.render(
                    str(row.get('player_name', ''))[:18], True, rc)
                surface.blit(name_surf, (cx1, ry + 4))

                # Wins
                wins_surf = self._font_small.render(str(row.get('wins', '')), True, rc)
                surface.blit(wins_surf, (cx2, ry + 4))

                # Avg
                avg_surf = self._font_small.render(
                    f"{row.get('avg_score', 0):.1f}", True, rc)
                surface.blit(avg_surf, (cx3, ry + 4))

                # Row separator line (skip after last row)
                if ri < min(MAX_ROWS, len(self.leaderboard_data)) - 1:
                    sep_y = ry + ROW_H - 2
                    pygame.draw.line(surface, (90, 62, 28),
                                     (lx + 14, sep_y), (lx + lw - 14, sep_y), 1)
        else:
            nd = self._font_small.render("No games played yet.", True, TEXT_LIGHT)
            surface.blit(nd, (lx + 20, hy + 30))

        # How-to-play overlay (drawn on top of everything)
        if self._show_htp:
            self._draw_htp_overlay(surface)

    # --------------------------------------------------- how-to-play overlay
    _HTP_LINES = [
        ("CAMEL UP — HOW TO PLAY", True),
        ("", False),
        ("GOAL: Have the most coins when the race ends.", False),
        ("", False),
        ("ON YOUR TURN, CHOOSE ONE ACTION:", True),
        ("  Roll Dice  — draw a die, move that camel, earn 1 coin.", False),
        ("  Leg Bet    — take a tile betting on this leg's 1st or 2nd place camel.", False),
        ("  Race Bet   — secretly bet on the overall race winner or loser.", False),
        ("  Desert Tile— place an Oasis (+1 step) or Mirage (-1 step) on any", False),
        ("               empty, non-adjacent tile.  Earn 1 coin when triggered.", False),
        ("", False),
        ("CAMELS & DICE:", True),
        ("  Green / Purple / Yellow / Blue / Red — racing camels (move forward).", False),
        ("  Black / White — crazy camels (move BACKWARD).", False),
        ("  Grey die — moves either Black or White at random.", False),
        ("  A leg ends when all 5 racing dice are used.", False),
        ("", False),
        ("STACKING:", True),
        ("  Moving camel carries all camels on top of it.", False),
        ("  Crazy camels land UNDER existing stacks.", False),
        ("", False),
        ("RACE END: A racing camel passes tile 16.  Race bets are scored.", False),
    ]

    def _draw_htp_overlay(self, surface: pygame.Surface):
        # Dim the background
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Panel
        pw, ph = 760, 510
        px = (WINDOW_W - pw) // 2
        py = (WINDOW_H - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(surface, (61, 31, 10), panel, border_radius=14)
        pygame.draw.rect(surface, GOLD, panel, width=2, border_radius=14)

        y = py + 18
        for text, is_header in self._HTP_LINES:
            if not text:
                y += 6
                continue
            font  = self._font if not is_header else self._font_small
            color = GOLD if is_header else TEXT_LIGHT
            surf  = font.render(text, True, color)
            surface.blit(surf, (px + 24, y))
            y += surf.get_height() + (5 if is_header else 3)
