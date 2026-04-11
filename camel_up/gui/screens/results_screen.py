import pygame
import pygame_gui
import math
from gui.theme import (
    WINDOW_W, WINDOW_H, WOOD_DARK, WOOD_MID, GOLD, TEXT_LIGHT, WHITE, BLACK,
    CAMEL_COLOR_MAP, load_font, generate_background_surface
)

# Color palette per specifications
COLOR_GOLD_TEXT = (200, 150, 12)      # #C8960C - Deep gold for positive coins
COLOR_RED_TEXT = (192, 57, 43)        # #C0392B - Deep red for negative coins
COLOR_BRIGHT_GOLD = (255, 215, 0)     # #FFD700 - Bright gold for winner name
COLOR_OFF_WHITE = (245, 230, 200)     # #F5E6C8 - Off-white text
COLOR_DARK_BROWN = (59, 31, 10)       # #3B1F0A - Dark brown for text
COLOR_CARD_BG = (45, 27, 14)          # #2C1A0E - Dark parchment card background
COLOR_CARD_BORDER = (200, 150, 12)    # #C8960C - Golden border
COLOR_DIVIDER = (61, 43, 26)          # Slightly lighter for alternating rows
COLOR_DIVIDER_LINE = (200, 150, 12)   # Gold at 40% opacity will be handled in drawing


class ResultsScreen:
    """End-game results screen showing winner and detailed coin breakdown per player."""

    def __init__(self, app, game):
        self.app = app
        self.game = game
        self.state = game.get_state()
        self.ui_manager = app.ui_manager
        self._background = None
        self._fonts = {}
        self._scroll_offset = 0
        self._start_time = pygame.time.get_ticks()

        # UI buttons for replay and menu
        cx = WINDOW_W // 2
        self.replay_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx - 220, WINDOW_H - 60, 200, 48),
            text='Play Again',
            manager=self.ui_manager,
        )
        self.menu_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(cx + 20, WINDOW_H - 60, 200, 48),
            text='Main Menu',
            manager=self.ui_manager,
        )

    def _get_font(self, size: int):
        """Cache fonts by size."""
        if size not in self._fonts:
            self._fonts[size] = load_font(size)
        return self._fonts[size]

    def _coin_color(self, amount: int) -> tuple:
        """Return color based on coin amount."""
        if amount > 0:
            return COLOR_GOLD_TEXT  # Gold for gains
        elif amount < 0:
            return COLOR_RED_TEXT   # Deep red for losses
        else:
            return COLOR_OFF_WHITE  # Off-white for zero

    def _get_source_icon_and_label(self, source: str) -> tuple:
        """Return emoji icon and readable label for coin source."""
        sources = {
            'dice_roll': ('🎲', 'Dice Roll Bonus'),
            'desert_tile': ('🏜️', 'Desert Tile Income'),
            'leg_bet': ('🏆', 'Leg Bets'),
            'race_winner': ('👑', 'Race Winner Bet'),
            'race_loser': ('💀', 'Race Loser Bet'),
        }
        return sources.get(source, ('📋', source.replace('_', ' ').title()))

    def _calculate_coin_summary(self) -> list:
        """
        Aggregate coin log by source for each player.
        Returns list of dicts with aggregated totals per source type.
        """
        player_summaries = []
        for player in self.state.players:
            summary = {
                'player': player,
                'total': player.coins,
                'sources': {}
            }

            # Aggregate coin_log by source
            for entry in player.coin_log:
                source = entry['source']
                amount = entry['amount']
                if source not in summary['sources']:
                    summary['sources'][source] = 0
                summary['sources'][source] += amount

            player_summaries.append(summary)

        # Sort by total coins descending
        player_summaries.sort(key=lambda x: x['total'], reverse=True)
        return player_summaries

    def _get_placement_badge(self, rank: int) -> str:
        """Return placement emoji and label for badge."""
        badges = {
            1: ('👑', '1ST'),
            2: ('🥈', '2ND'),
            3: ('🥉', '3RD'),
        }
        if rank in badges:
            return badges[rank]
        return ('', f'{rank}TH')

    def handle_event(self, event: pygame.event.Event):
        """Handle input (buttons or any key/click to close)."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.replay_btn:
                self.replay_btn.kill()
                self.menu_btn.kill()
                self.app.start_new_game([p.name for p in self.state.players])
            elif event.ui_element == self.menu_btn:
                self.replay_btn.kill()
                self.menu_btn.kill()
                self.app.show_start_screen()
        return None

    def update(self, time_delta: float):
        """Update animations."""
        pass

    def draw(self, surface: pygame.Surface):
        """Draw the entire results screen."""
        # Background
        if self._background is None:
            self._background = generate_background_surface(WINDOW_W, WINDOW_H)
        surface.blit(self._background, (0, 0))

        # Draw title bar
        pygame.draw.rect(surface, WOOD_DARK, pygame.Rect(0, 0, WINDOW_W, 80))
        pygame.draw.rect(surface, WOOD_MID, pygame.Rect(0, 0, WINDOW_W, 80), width=2)

        title_font = self._get_font(48)
        title = title_font.render("GAME OVER", True, GOLD)
        surface.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 20))

        # Get sorted player summaries
        summaries = self._calculate_coin_summary()
        if not summaries:
            return

        # Draw winner banner
        self._draw_winner_banner(surface, summaries[0])

        # Draw player result cards (centered and responsive)
        self._draw_player_cards(surface, summaries)

    def _draw_winner_banner(self, surface: pygame.Surface, winner_summary: dict):
        """Draw the winner announcement at the top."""
        player = winner_summary['player']
        total_coins = winner_summary['total']

        # Winner banner background
        banner_h = 110
        banner_x = 50
        banner_y = 100
        banner_w = WINDOW_W - 100
        banner_rect = pygame.Rect(banner_x, banner_y, banner_w, banner_h)

        pygame.draw.rect(surface, (80, 60, 30), banner_rect)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, banner_rect, width=3)

        # Winner text with crown emoji
        winner_font = self._get_font(36)
        winner_text = f"👑 {player.name.upper()} WINS!"
        winner_surf = winner_font.render(winner_text, True, COLOR_BRIGHT_GOLD)
        winner_x = banner_x + (banner_w - winner_surf.get_width()) // 2
        surface.blit(winner_surf, (winner_x, banner_y + 15))

        # Coin amount
        coin_font = self._get_font(24)
        coin_text = f"{total_coins} coins"
        coin_surf = coin_font.render(coin_text, True, COLOR_GOLD_TEXT)
        coin_x = banner_x + (banner_w - coin_surf.get_width()) // 2
        surface.blit(coin_surf, (coin_x, banner_y + 60))

    def _draw_player_cards(self, surface: pygame.Surface, summaries: list):
        """Draw individual player result cards centered and responsive."""
        num_players = len(summaries)
        card_width = 280
        card_height = 180  # Reduced to prevent overlap with buttons
        gap = 16

        # Determine grid layout
        if num_players <= 2:
            cols = num_players
            rows = 1
        elif num_players == 3:
            cols = 3
            rows = 1
        else:  # 4+
            cols = 2
            rows = (num_players + 1) // 2

        # Calculate total width needed
        total_width = cols * card_width + (cols - 1) * gap
        start_x = (WINDOW_W - total_width) // 2
        start_y = 240

        row_height = card_height + gap

        for idx, summary in enumerate(summaries):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (card_width + gap)
            y = start_y + row * row_height

            # Remove the cutoff check to show all players
            placement = idx + 1  # 1st, 2nd, 3rd, etc.
            self._draw_player_card(surface, x, y, card_width, card_height, summary, placement)

    def _draw_player_card(self, surface: pygame.Surface, x: int, y: int, w: int, h: int,
                          summary: dict, placement: int):
        """Draw a single player result card with placement badge."""
        player = summary['player']
        total_coins = summary['total']
        sources = summary['sources']

        # Card background
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, COLOR_CARD_BG, card_rect)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, card_rect, width=2)

        # --- Card header area: name + coins + badge (with padding)
        header_padding_left = 16
        header_padding_right = 70  # Space reserved for badge
        header_padding_top = 12
        header_padding_bottom = 8

        # Player name (18px, bright gold, bold)
        name_font = self._get_font(18)
        name_surf = name_font.render(player.name.upper(), True, COLOR_BRIGHT_GOLD)
        surface.blit(name_surf, (x + header_padding_left, y + header_padding_top))

        # Total coins (15px, gold color)
        coins_font = self._get_font(15)
        coins_text = f"{total_coins}"
        coins_surf = coins_font.render(coins_text, True, COLOR_GOLD_TEXT)
        surface.blit(coins_surf, (x + header_padding_left, y + header_padding_top + 24))

        # Placement badge (52x52px, top-right corner)
        badge_x = x + w - 52 - 8
        badge_y = y + 12
        self._draw_placement_badge(surface, badge_x, badge_y, placement, size=52)

        # Divider line at 40% opacity (below header)
        header_bottom = y + header_padding_top + 52 + header_padding_bottom
        divider_color = tuple(int(c * 0.4) for c in COLOR_CARD_BORDER)
        pygame.draw.line(surface, divider_color, (x + 12, header_bottom), (x + w - 12, header_bottom), 1)

        # --- Breakdown rows area (with padding)
        breakdown_padding_top = 8
        breakdown_padding_left = 16
        breakdown_padding_right = 16
        breakdown_y = header_bottom + breakdown_padding_top
        line_height = 22
        source_idx = 0

        # Order sources logically
        source_order = ['dice_roll', 'leg_bet', 'race_winner', 'race_loser', 'desert_tile']
        for source in source_order:
            if source not in sources:
                continue

            amount = sources[source]

            # Skip zero amounts
            if amount == 0:
                continue

            # Alternating background for rows (subtle)
            if source_idx % 2 == 1:
                row_rect = pygame.Rect(x + 2, breakdown_y - 2, w - 4, line_height)
                pygame.draw.rect(surface, COLOR_DIVIDER, row_rect)

            icon, label = self._get_source_icon_and_label(source)
            color = self._coin_color(amount)

            # Category label (off-white, 13px)
            label_font = self._get_font(13)
            label_text = f"{icon} {label}"
            label_surf = label_font.render(label_text, True, COLOR_OFF_WHITE)
            surface.blit(label_surf, (x + breakdown_padding_left, breakdown_y))

            # Amount (with sign, 13px, appropriate color)
            sign = "+" if amount >= 0 else "−"
            amount_text = f"{sign}{abs(amount)}"
            amount_surf = label_font.render(amount_text, True, color)
            surface.blit(amount_surf, (x + w - breakdown_padding_right - amount_surf.get_width(), breakdown_y))

            breakdown_y += line_height
            source_idx += 1

    def _draw_placement_badge(self, surface: pygame.Surface, x: int, y: int, placement: int, size: int = 55):
        """Draw placement badge in corner with drop shadow and placement-specific colors."""
        # Badge dimensions
        badge_size = size
        shadow_offset = 2 if size > 52 else 1

        # Determine badge color and text color based on placement
        if placement == 1:
            bg_color = (200, 150, 12)      # Gold #C8960C
            text_color = (59, 31, 10)      # Dark brown #2C1A0E
            badge_text = "1ST"
        elif placement == 2:
            bg_color = (168, 168, 168)     # Silver-grey #A8A8A8
            text_color = (26, 26, 26)      # Dark #1A1A1A
            badge_text = "2ND"
        elif placement == 3:
            bg_color = (205, 127, 50)      # Bronze #CD7F32
            text_color = (26, 26, 26)      # Dark #1A1A1A
            badge_text = "3RD"
        else:
            bg_color = (61, 43, 26)        # Dark #3D2B1A
            text_color = (160, 120, 16)    # Muted gold #A07810
            badge_text = f"{placement}TH"

        # Draw drop shadow
        shadow_rect = pygame.Rect(x + shadow_offset, y + shadow_offset, badge_size, badge_size)
        pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=5)

        # Draw badge background
        badge_rect = pygame.Rect(x, y, badge_size, badge_size)
        pygame.draw.rect(surface, bg_color, badge_rect, border_radius=5)
        pygame.draw.rect(surface, text_color, badge_rect, width=2, border_radius=5)

        # Draw text centered in badge (15px font for 52px badge)
        badge_font_size = 15 if size <= 52 else 18
        text_font = self._get_font(badge_font_size)
        text_surf = text_font.render(badge_text, True, text_color)
        text_x = x + (badge_size - text_surf.get_width()) // 2
        text_y = y + (badge_size - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))
