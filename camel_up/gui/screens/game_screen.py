import pygame
import pygame_gui

from gui.theme import (
    WOOD_DARK, WOOD_MID, TEXT_LIGHT, GOLD, WHITE, BLACK,
    WINDOW_W, WINDOW_H, TOP_BAR_H, BOTTOM_BAR_H,
    LEFT_PANEL_W, RIGHT_PANEL_W, CENTER_W, MAIN_H,
    CAMEL_COLOR_MAP, generate_background_surface, load_font,
)
from gui.components.board       import Board
from gui.components.player_hud  import PlayerHud
from gui.components.bet_card    import BetCard
from gui.components.dice_pyramid import DicePyramid
from gui.components.event_log   import EventLog
from game.game_logic             import CamelUpGame
from game.models                 import CAMEL_COLORS


class GameScreen:
    """Main gameplay screen: board, hud, betting panels, event log."""

    def __init__(self, app, game: CamelUpGame):
        self.app  = app
        self.game = game
        self.ui_manager  = app.ui_manager
        self._background = None
        self._font_bar   = None

        # Layout shortcuts
        cx  = LEFT_PANEL_W
        rx  = LEFT_PANEL_W + CENTER_W
        cy  = TOP_BAR_H
        bot = TOP_BAR_H + MAIN_H

        self.board       = Board(cx, cy, CENTER_W, MAIN_H)
        self.player_hud  = PlayerHud(0, cy, LEFT_PANEL_W, MAIN_H)
        self.bet_card    = BetCard(rx, cy, RIGHT_PANEL_W, MAIN_H // 2)
        self.dice_pyramid = DicePyramid(rx, cy + MAIN_H // 2, RIGHT_PANEL_W, MAIN_H // 2)
        self.event_log   = EventLog(0, bot, WINDOW_W, BOTTOM_BAR_H)

        # Bet overlay state
        self._bet_overlay      = False
        self._bet_type         = None    # 'leg' or 'race'
        self._race_step        = 0       # 0=pick camel, 1=pick winner/loser
        self._race_color       = None
        self._overlay_btns:    dict = {}
        self._overlay_type_btns: dict = {}

        # Tile placement state
        self._tile_mode        = False
        self._tile_type        = None
        self._tile_type_overlay = False

        self.game_start_time = pygame.time.get_ticks()
        self._logo = None

    # ---------------------------------------------------------------- logo
    def _get_logo(self):
        if self._logo is None:
            try:
                img = pygame.image.load('assets/images/logo.png').convert_alpha()
                w, h = img.get_size()
                new_h = TOP_BAR_H - 6
                self._logo = pygame.transform.smoothscale(
                    img, (int(w * new_h / h), new_h))
            except Exception:
                self._logo = False

    # ---------------------------------------------------------------- fonts
    def _get_fonts(self):
        if self._font_bar is None:
            self._font_bar = load_font(16)

    # --------------------------------------------------------------- events
    def handle_event(self, event: pygame.event.Event):
        # Bet overlay has exclusive focus
        if self._bet_overlay:
            self._handle_bet_event(event)
            return

        # Tile-type chooser overlay
        if self._tile_type_overlay:
            self._handle_tile_type_event(event)
            return

        # Tile placement mode
        if self._tile_mode:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tile = self.board.get_clicked_tile(event.pos)
                if tile:
                    self._commit_tile(tile)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel_tile_mode()
            elif event.type == pygame.MOUSEMOTION:
                self.board.handle_mouse_motion(event.pos)
            return

        self.event_log.handle_event(event)

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            state   = self.game.get_state()
            valid   = self.game.get_valid_actions(state.current_player_idx)
            action  = self.player_hud.handle_event(event)
            if action:
                self._dispatch_action(action, valid)

    # -------------------------------------------------------------- actions
    def _dispatch_action(self, action: str, valid: list):
        if action not in valid:
            return
        if action == 'roll':
            self._do_roll()
        elif action == 'leg_bet':
            self._bet_overlay = True
            self._bet_type    = 'leg'
        elif action == 'race_bet':
            self._bet_overlay = True
            self._bet_type    = 'race'
            self._race_step   = 0
            self._race_color  = None
        elif action == 'desert_tile':
            self._tile_type_overlay = True

    def _do_roll(self):
        state  = self.game.get_state()
        result = self.game.roll_dice(state.current_player_idx)
        die_color    = result['color']
        camel_moved  = result.get('camel_moved', die_color)
        steps        = result['steps']
        new_pos      = result.get('new_position', 0)
        self.board.animate_camel_move(camel_moved, new_pos)
        self.dice_pyramid.animate_roll(die_color, steps, camel_moved)
        if not self.game.get_state().game_over:
            self.game.advance_turn()
        self._post_action()
        if self.game.get_state().game_over:
            self.app.show_end_screen(self.game)

    def _post_action(self):
        pass

    # --------------------------------------------------------- bet overlay
    def _handle_bet_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._bet_overlay = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        mx, my = event.pos
        state  = self.game.get_state()

        if self._bet_type == 'leg':
            for color, rect in self._overlay_btns.items():
                if rect.collidepoint(mx, my) and state.available_leg_bets.get(color):
                    self.game.take_leg_bet(state.current_player_idx, color)
                    self.game.advance_turn()
                    self._post_action()
                    self._bet_overlay = False
                    return

        elif self._bet_type == 'race':
            if self._race_step == 0:
                for color, rect in self._overlay_btns.items():
                    if rect.collidepoint(mx, my):
                        self._race_color = color
                        self._race_step  = 1
                        return
            else:
                for btype, rect in self._overlay_type_btns.items():
                    if rect.collidepoint(mx, my):
                        self.game.place_race_bet(state.current_player_idx,
                                                  self._race_color, btype)
                        self.game.advance_turn()
                        self._post_action()
                        self._bet_overlay = False
                        return

        # Click outside panel = cancel
        if not self._overlay_panel_rect().collidepoint(mx, my):
            self._bet_overlay = False

    def _overlay_panel_rect(self) -> pygame.Rect:
        w, h = 420, 340
        return pygame.Rect(WINDOW_W // 2 - w // 2, WINDOW_H // 2 - h // 2, w, h)

    # ------------------------------------------------------- tile placement
    def _handle_tile_type_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._tile_type_overlay = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        mx, my = event.pos
        cx, cy = WINDOW_W // 2, WINDOW_H // 2
        oasis_r  = pygame.Rect(cx - 135, cy - 45, 125, 50)
        mirage_r = pygame.Rect(cx + 10,  cy - 45, 125, 50)
        cancel_r = pygame.Rect(cx - 65,  cy + 18, 130, 36)
        if oasis_r.collidepoint(mx, my):
            self._tile_type = 'oasis'
            self._tile_type_overlay = False
            self._enter_tile_mode()
        elif mirage_r.collidepoint(mx, my):
            self._tile_type = 'mirage'
            self._tile_type_overlay = False
            self._enter_tile_mode()
        elif cancel_r.collidepoint(mx, my):
            self._tile_type_overlay = False

    def _enter_tile_mode(self):
        self._tile_mode = True
        state = self.game.get_state()
        occupied = {c.position for c in state.camels if c.position > 0}
        dt = state.desert_tiles
        # 2.0 rule: cannot place adjacent to an existing desert tile
        valid = [
            t for t in range(2, 17)
            if t not in occupied
            and t not in dt
            and (t - 1) not in dt
            and (t + 1) not in dt
        ]
        self.board.set_tile_select_mode(True, valid)

    def _commit_tile(self, tile_num: int):
        state   = self.game.get_state()
        success = self.game.place_desert_tile(state.current_player_idx,
                                               tile_num, self._tile_type)
        if success:
            self.game.advance_turn()
            self._post_action()
        self._cancel_tile_mode()

    def _cancel_tile_mode(self):
        self._tile_mode = False
        self._tile_type = None
        self.board.set_tile_select_mode(False)

    # --------------------------------------------------------------- update
    def update(self, time_delta: float):
        self.board.update()
        self.dice_pyramid.update()

    # --------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface):
        self._get_fonts()
        self._get_logo()

        if self._background is None:
            self._background = generate_background_surface(WINDOW_W, WINDOW_H)
        surface.blit(self._background, (0, 0))

        state = self.game.get_state()

        # Top bar
        pygame.draw.rect(surface, WOOD_DARK, pygame.Rect(0, 0, WINDOW_W, TOP_BAR_H))
        pygame.draw.rect(surface, WOOD_MID,  pygame.Rect(0, 0, WINDOW_W, TOP_BAR_H), width=2)

        if self._tile_mode:
            inst = self._font_bar.render(
                "Click a highlighted tile to place — ESC to cancel", True, GOLD)
            surface.blit(inst, (WINDOW_W // 2 - inst.get_width() // 2, 10))
        else:
            if self._logo:
                surface.blit(self._logo, (8, (TOP_BAR_H - self._logo.get_height()) // 2))
            else:
                surface.blit(self._font_bar.render("CAMEL UP", True, GOLD), (12, 10))
            leg = self._font_bar.render(f"Leg {state.leg_number}", True, TEXT_LIGHT)
            surface.blit(leg, (WINDOW_W // 2 - leg.get_width() // 2, 10))
            cp  = state.players[state.current_player_idx]
            trn = self._font_bar.render(f"Turn: {cp.name}", True, TEXT_LIGHT)
            surface.blit(trn, (WINDOW_W - trn.get_width() - 12, 10))

        # Main components
        valid = self.game.get_valid_actions(state.current_player_idx)
        self.player_hud.draw(surface, state, valid)
        self.board.draw(surface, state)
        self.bet_card.draw(surface, state.available_leg_bets)
        self.dice_pyramid.draw(surface, state.dice_remaining)
        self.event_log.draw(surface, state.event_log)

        # Overlays
        if self._bet_overlay:
            self._draw_bet_overlay(surface, state)
        if self._tile_type_overlay:
            self._draw_tile_type_overlay(surface)

    # --------------------------------------------------- overlay rendering
    def _draw_bet_overlay(self, surface: pygame.Surface, state):
        ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        surface.blit(ov, (0, 0))

        panel = self._overlay_panel_rect()
        pygame.draw.rect(surface, WOOD_DARK, panel, border_radius=12)
        pygame.draw.rect(surface, GOLD,      panel, width=3, border_radius=12)

        fn  = load_font(16)
        fsm = load_font(13)

        self._overlay_btns      = {}
        self._overlay_type_btns = {}

        if self._bet_type == 'leg':
            t = fn.render("Leg Bet — Choose a Camel", True, GOLD)
            surface.blit(t, (panel.centerx - t.get_width() // 2, panel.y + 12))
            for idx, color in enumerate(CAMEL_COLORS):
                r = pygame.Rect(panel.x + 18, panel.y + 46 + idx * 50, panel.width - 36, 42)
                self._overlay_btns[color] = r
                tiles = state.available_leg_bets.get(color, [])
                avail = bool(tiles)
                bg  = (90, 60, 28) if avail else (38, 26, 12)
                bc  = GOLD         if avail else (70, 55, 30)
                pygame.draw.rect(surface, bg, r, border_radius=8)
                pygame.draw.rect(surface, bc, r, width=2, border_radius=8)
                sw = pygame.Rect(r.x + 8, r.centery - 12, 24, 24)
                pygame.draw.rect(surface, CAMEL_COLOR_MAP.get(color, (128,128,128)), sw, border_radius=4)
                tc = TEXT_LIGHT if avail else (100, 80, 50)
                pay = f"  Next: {tiles[0]}" if tiles else "  No tiles"
                lbl = fsm.render(f"{color.capitalize()}{pay}", True, tc)
                surface.blit(lbl, (r.x + 38, r.centery - 8))

        elif self._bet_type == 'race':
            if self._race_step == 0:
                t = fn.render("Race Bet — Choose a Camel", True, GOLD)
                surface.blit(t, (panel.centerx - t.get_width() // 2, panel.y + 12))
                for idx, color in enumerate(CAMEL_COLORS):
                    r = pygame.Rect(panel.x + 18, panel.y + 46 + idx * 50, panel.width - 36, 42)
                    self._overlay_btns[color] = r
                    pygame.draw.rect(surface, (90, 60, 28), r, border_radius=8)
                    pygame.draw.rect(surface, GOLD, r, width=2, border_radius=8)
                    sw = pygame.Rect(r.x + 8, r.centery - 12, 24, 24)
                    pygame.draw.rect(surface, CAMEL_COLOR_MAP.get(color, (128,128,128)), sw, border_radius=4)
                    lbl = fsm.render(color.capitalize(), True, TEXT_LIGHT)
                    surface.blit(lbl, (r.x + 38, r.centery - 8))
            else:
                t = fn.render(f"Race Bet: {self._race_color.capitalize()} — Win or Lose?", True, GOLD)
                surface.blit(t, (panel.centerx - t.get_width() // 2, panel.y + 12))
                for bi, btype in enumerate(['winner', 'loser']):
                    br = pygame.Rect(panel.x + 20 + bi * 190, panel.centery - 35, 170, 64)
                    self._overlay_type_btns[btype] = br
                    col = (40, 140, 40) if btype == 'winner' else (140, 40, 40)
                    pygame.draw.rect(surface, col, br, border_radius=10)
                    pygame.draw.rect(surface, GOLD, br, width=2, border_radius=10)
                    lb = fn.render(btype.upper(), True, WHITE)
                    surface.blit(lb, (br.centerx - lb.get_width() // 2,
                                      br.centery - lb.get_height() // 2))

        hint = fsm.render("ESC or click outside to cancel", True, (140, 120, 80))
        surface.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 20))

    def _draw_tile_type_overlay(self, surface: pygame.Surface):
        ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        surface.blit(ov, (0, 0))

        panel = pygame.Rect(WINDOW_W // 2 - 170, WINDOW_H // 2 - 90, 340, 175)
        pygame.draw.rect(surface, WOOD_DARK, panel, border_radius=12)
        pygame.draw.rect(surface, GOLD,      panel, width=3, border_radius=12)

        fn  = load_font(16)
        fsm = load_font(13)

        t = fn.render("Choose Desert Tile Type", True, GOLD)
        surface.blit(t, (panel.centerx - t.get_width() // 2, panel.y + 12))

        cx, cy = WINDOW_W // 2, WINDOW_H // 2
        oasis_r  = pygame.Rect(cx - 135, cy - 45, 125, 50)
        mirage_r = pygame.Rect(cx + 10,  cy - 45, 125, 50)
        cancel_r = pygame.Rect(cx - 65,  cy + 18, 130, 36)

        pygame.draw.rect(surface, (30, 120, 40), oasis_r, border_radius=8)
        pygame.draw.rect(surface, GOLD, oasis_r, width=2, border_radius=8)
        ol = fn.render("Oasis  +1", True, WHITE)
        surface.blit(ol, (oasis_r.centerx - ol.get_width() // 2,
                           oasis_r.centery - ol.get_height() // 2))

        pygame.draw.rect(surface, (130, 35, 35), mirage_r, border_radius=8)
        pygame.draw.rect(surface, GOLD, mirage_r, width=2, border_radius=8)
        ml = fn.render("Mirage  -1", True, WHITE)
        surface.blit(ml, (mirage_r.centerx - ml.get_width() // 2,
                           mirage_r.centery - ml.get_height() // 2))

        pygame.draw.rect(surface, WOOD_MID, cancel_r, border_radius=8)
        pygame.draw.rect(surface, (196, 169, 109), cancel_r, width=2, border_radius=8)
        cl = fsm.render("Cancel", True, TEXT_LIGHT)
        surface.blit(cl, (cancel_r.centerx - cl.get_width() // 2,
                           cancel_r.centery - cl.get_height() // 2))
