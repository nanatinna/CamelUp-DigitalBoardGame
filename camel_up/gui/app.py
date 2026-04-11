import sys
import os
import logging
import pygame
import pygame_gui

from game.utils      import setup_logging
from storage.database import init_db

logger = logging.getLogger(__name__)

_THEME_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'theme.json')


class App:
    """Top-level application: pygame loop, screen manager."""

    def __init__(self):
        setup_logging()
        pygame.init()
        pygame.display.set_caption("Camel Up")
        self.screen = pygame.display.set_mode((1280, 800))
        self.clock  = pygame.time.Clock()

        try:
            self.ui_manager = pygame_gui.UIManager((1280, 800), _THEME_PATH)
        except Exception as e:
            logger.warning(f"Could not load theme ({e}); using default.")
            self.ui_manager = pygame_gui.UIManager((1280, 800))

        self.current_screen    = None
        self.game              = None
        self._game_start_time  = 0

        try:
            init_db()
        except Exception as e:
            logger.error(f"DB init failed: {e}")

    # --------------------------------------------------------------- screen transitions
    def show_start_screen(self):
        from gui.screens.start_screen import StartScreen
        self.ui_manager.clear_and_reset()
        self.current_screen = StartScreen(self)

    def start_new_game(self, player_names: list):
        from game.game_logic          import CamelUpGame
        from gui.screens.game_screen  import GameScreen
        self.ui_manager.clear_and_reset()
        self.game = CamelUpGame(player_names)
        self._game_start_time = pygame.time.get_ticks()
        self.current_screen = GameScreen(self, self.game)

    def show_end_screen(self, game):
        from gui.screens.end_screen import EndScreen
        self.ui_manager.clear_and_reset()
        self.current_screen = EndScreen(self, game)

    # --------------------------------------------------------------- quit
    def quit(self):
        pygame.quit()
        sys.exit(0)

    # --------------------------------------------------------------- main loop
    def run(self):
        self.show_start_screen()
        while True:
            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                try:
                    self.ui_manager.process_events(event)
                    if self.current_screen:
                        self.current_screen.handle_event(event)
                except Exception as e:
                    logger.error(f"Event error: {e}", exc_info=True)

            try:
                if self.current_screen:
                    self.current_screen.update(time_delta)
                self.ui_manager.update(time_delta)
            except Exception as e:
                logger.error(f"Update error: {e}", exc_info=True)

            try:
                self.screen.fill((0, 0, 0))
                if self.current_screen:
                    self.current_screen.draw(self.screen)
                self.ui_manager.draw_ui(self.screen)
                pygame.display.flip()
            except Exception as e:
                logger.error(f"Draw error: {e}", exc_info=True)
