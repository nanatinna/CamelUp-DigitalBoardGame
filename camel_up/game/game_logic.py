import random
import logging
from game.models import (
    GameState, Camel, Player, LegBetTile, RaceBet,
    CAMEL_COLORS, CRAZY_CAMEL_COLORS, ALL_CAMEL_COLORS, DICE_COLORS,
)

logger = logging.getLogger(__name__)


class CamelUpGame:
    """Camel Up 2.0 — 5 racing camels + 2 crazy camels (move backward)."""

    def __init__(self, player_names: list):
        players = [Player(name=name) for name in player_names]

        # 5 racing camels + 2 crazy camels
        camels = [Camel(color=c, is_crazy=False) for c in CAMEL_COLORS]
        camels += [Camel(color=c, is_crazy=True) for c in CRAZY_CAMEL_COLORS]

        # Only racing camels have leg-bet tiles
        available_leg_bets = {color: [5, 3, 2, 1] for color in CAMEL_COLORS}

        # 6 dice start in the pyramid (5 racing + 1 grey for crazy camels)
        self.state = GameState(
            players=players,
            camels=camels,
            available_leg_bets=available_leg_bets,
            dice_remaining=list(DICE_COLORS),
        )

        # Place racing camels randomly on tiles 1–3
        self._place_camels_at_start(CAMEL_COLORS, tile_range=(1, 3))

        # Place crazy camels randomly near the far end (tiles 14–16)
        self._place_camels_at_start(CRAZY_CAMEL_COLORS, tile_range=(14, 16))

    # ---------------------------------------------------------------- helpers
    def _place_camels_at_start(self, colors: list, tile_range: tuple):
        """Place camels from *colors* randomly within *tile_range* (inclusive)."""
        order = list(colors)
        random.shuffle(order)
        tile_counts: dict = {}
        for color in order:
            tile = random.randint(*tile_range)
            camel = self._get_camel_by_color(color)
            camel.position = tile
            tile_counts.setdefault(tile, 0)
            camel.stack_order = tile_counts[tile]
            tile_counts[tile] += 1

    def _get_camel_by_color(self, color: str) -> Camel:
        for camel in self.state.camels:
            if camel.color == color:
                return camel
        raise ValueError(f"Unknown camel color: {color}")

    def log_event(self, msg: str):
        self.state.event_log.append(msg)
        if len(self.state.event_log) > 50:
            self.state.event_log = self.state.event_log[-50:]

    # -------------------------------------------------------- public actions
    def get_valid_actions(self, player_idx: int) -> list:
        if self.state.game_over:
            return []
        player = self.state.players[player_idx]
        actions = ['roll']

        # Leg bet: at least one racing camel still has tiles
        if any(len(t) > 0 for t in self.state.available_leg_bets.values()):
            actions.append('leg_bet')

        # Race bet: always available
        actions.append('race_bet')

        # Desert tile: player hasn't placed one this leg
        if not player.desert_tile_placed:
            actions.append('desert_tile')

        return actions

    def roll_dice(self, player_idx: int) -> dict:
        if not self.state.dice_remaining:
            return {'color': '', 'steps': 0, 'end_of_leg': False, 'new_position': 0}

        die_color = random.choice(self.state.dice_remaining)
        steps = random.randint(1, 3)
        self.state.dice_remaining.remove(die_color)

        # Grey die: randomly pick one of the two crazy camels to move
        if die_color == 'grey':
            camel_color = random.choice(CRAZY_CAMEL_COLORS)
        else:
            camel_color = die_color

        move_result = self.move_camel(camel_color, steps)
        self.state.players[player_idx].coins += 1  # +1 coin for rolling

        end_of_leg = False
        # Leg ends when ALL 5 racing dice are exhausted (grey die may remain).
        if die_color in CAMEL_COLORS and not self.state.game_over:
            racing_left = [c for c in self.state.dice_remaining if c in CAMEL_COLORS]
            if not racing_left:
                self.end_leg()
                end_of_leg = True

        new_position = move_result['new_pos']
        camel = self._get_camel_by_color(camel_color)
        direction = "←" if camel.is_crazy else "→"
        die_info = f"[grey→{camel_color}] " if die_color == 'grey' else ""
        self.log_event(
            f"{self.state.players[player_idx].name} rolled {die_info}{die_color} "
            f"{direction}{steps} → tile {new_position}"
            + (f" [{move_result['desert_effect']}]" if move_result['desert_effect'] else "")
        )

        return {
            'color': die_color,        # die that was rolled ('grey' for crazy die)
            'camel_moved': camel_color, # actual camel that moved
            'steps': steps,
            'end_of_leg': end_of_leg,
            'new_position': new_position,
            'is_crazy': camel.is_crazy,
        }

    def move_camel(self, color: str, steps: int) -> dict:
        """
        Move a camel and its piggyback stack.

        Crazy camels move BACKWARD (position -= steps) and land UNDER any
        existing stack at the destination.  Racing camels move FORWARD and
        land ON TOP as in the original rules.
        """
        camel = self._get_camel_by_color(color)
        old_pos = camel.position

        # --- collect sub-stack (moving camel + all above it) ----------------
        same_tile = [c for c in self.state.camels if c.position == old_pos]
        same_tile.sort(key=lambda c: c.stack_order)
        sub_stack = [c for c in same_tile if c.stack_order >= camel.stack_order]

        # --- compute new position --------------------------------------------
        if camel.is_crazy:
            new_pos = old_pos - steps       # backward
        else:
            new_pos = old_pos + steps       # forward

        # --- desert tile effect ----------------------------------------------
        desert_effect = None
        tile_info = self.state.desert_tiles.get(new_pos)
        if tile_info is not None:
            dtype = tile_info['type']
            owner_idx = tile_info['owner_idx']
            self.state.players[owner_idx].coins += 1
            if dtype == 'oasis':
                new_pos += 1
                desert_effect = 'oasis'
            elif dtype == 'mirage':
                new_pos -= 1
                desert_effect = 'mirage'

        # Clamp: never below 1
        new_pos = max(1, new_pos)

        # --- destination stacking --------------------------------------------
        dest_camels = [
            c for c in self.state.camels
            if c.position == new_pos and c not in sub_stack
        ]

        if camel.is_crazy and dest_camels:
            # Crazy camel goes UNDER the existing stack.
            # Shift the existing camels upward to make room at the bottom.
            sub_size = len(sub_stack)
            for dc in dest_camels:
                dc.stack_order += sub_size
            base_order = 0
        elif dest_camels:
            # Racing camel goes ON TOP.
            base_order = max(c.stack_order for c in dest_camels) + 1
        else:
            base_order = 0

        # --- apply movement --------------------------------------------------
        sub_stack.sort(key=lambda c: c.stack_order)
        for i, c in enumerate(sub_stack):
            c.position = new_pos
            c.stack_order = base_order + i

        # --- win condition: only racing camels can end the race --------------
        if not camel.is_crazy and new_pos > 16:
            self.state.game_over = True
            self.score_race()

        return {
            'moved_camels': [c.color for c in sub_stack],
            'old_pos': old_pos,
            'new_pos': new_pos,
            'desert_effect': desert_effect,
        }

    def take_leg_bet(self, player_idx: int, camel_color: str) -> bool:
        """Take the highest remaining leg-bet tile for a RACING camel."""
        if camel_color not in CAMEL_COLORS:
            return False                         # cannot bet on crazy camels
        tiles = self.state.available_leg_bets.get(camel_color, [])
        if not tiles:
            return False
        value = tiles.pop(0)
        self.state.players[player_idx].leg_bets.append(
            LegBetTile(camel_color=camel_color, value=value)
        )
        self.log_event(
            f"{self.state.players[player_idx].name} took leg bet on "
            f"{camel_color} (worth {value})"
        )
        return True

    def place_race_bet(self, player_idx: int, color: str, bet_type: str) -> bool:
        """Place a secret overall-race winner/loser bet on a RACING camel."""
        if color not in CAMEL_COLORS:
            return False
        if bet_type not in ('winner', 'loser'):
            return False
        self.state.players[player_idx].race_bets.append(
            RaceBet(camel_color=color, bet_type=bet_type)
        )
        self.log_event(
            f"{self.state.players[player_idx].name} placed race {bet_type} bet on {color}"
        )
        return True

    def place_desert_tile(self, player_idx: int, tile_num: int, tile_type: str) -> bool:
        """
        Place an oasis (+1) or mirage (-1) desert tile.

        Rules (Camel Up 2.0):
        * Cannot place on tile 1
        * Cannot place on a tile occupied by a camel
        * Cannot place where a desert tile already exists
        * Cannot place adjacent (±1) to an existing desert tile
        """
        if tile_num < 2 or tile_num > 16:
            return False
        if any(c.position == tile_num for c in self.state.camels if c.position > 0):
            return False
        if tile_num in self.state.desert_tiles:
            return False
        # 2.0 rule: no adjacent desert tiles
        if (tile_num - 1) in self.state.desert_tiles:
            return False
        if (tile_num + 1) in self.state.desert_tiles:
            return False

        player = self.state.players[player_idx]
        if player.desert_tile_placed:
            return False

        self.state.desert_tiles[tile_num] = {'type': tile_type, 'owner_idx': player_idx}
        player.desert_tile_placed = True
        player.desert_tile = {'tile': tile_num, 'type': tile_type}
        self.log_event(f"{player.name} placed {tile_type} tile on tile {tile_num}")
        return True

    def end_leg(self):
        """Score leg bets, reset dice and desert tiles, start next leg."""
        standings = self.get_leg_standings()          # racing camels only
        first  = standings[0] if len(standings) > 0 else None
        second = standings[1] if len(standings) > 1 else None

        for player in self.state.players:
            for bet in player.leg_bets:
                if bet.camel_color == first:
                    player.coins += bet.value
                elif second and bet.camel_color == second:
                    player.coins += 1
                else:
                    player.coins -= 1
            player.leg_bets = []
            player.desert_tile_placed = False
            player.desert_tile = None

        # Reset all 6 dice
        self.state.dice_remaining = list(DICE_COLORS)
        self.state.available_leg_bets = {c: [5, 3, 2, 1] for c in CAMEL_COLORS}
        self.state.desert_tiles = {}
        self.state.leg_number += 1

        self.log_event(
            f"── Leg ended.  1st: {first}  2nd: {second}.  "
            f"Starting leg {self.state.leg_number}. ──"
        )

    def score_race(self):
        """Score all race (overall winner/loser) bets and declare game winner."""
        standings = self.get_leg_standings()          # racing camels only
        race_winner = standings[0]  if standings else None
        race_loser  = standings[-1] if standings else None

        payout = [8, 5, 3, 2, 1]

        def pay(idx: int) -> int:
            return payout[idx] if idx < len(payout) else 1

        winner_bets, loser_bets = [], []
        for player in self.state.players:
            for bet in player.race_bets:
                (winner_bets if bet.bet_type == 'winner' else loser_bets).append(
                    (player, bet)
                )

        correct_w = 0
        for player, bet in winner_bets:
            if bet.camel_color == race_winner:
                player.coins += pay(correct_w)
                correct_w += 1
            else:
                player.coins -= 1

        correct_l = 0
        for player, bet in loser_bets:
            if bet.camel_color == race_loser:
                player.coins += pay(correct_l)
                correct_l += 1
            else:
                player.coins -= 1

        best = max(self.state.players, key=lambda p: p.coins)
        self.state.winner   = best.name
        self.state.game_over = True

        self.log_event(
            f"🏆 Race over!  Race winner camel: {race_winner}  "
            f"Race loser camel: {race_loser}.  "
            f"Game winner: {best.name} ({best.coins} coins)."
        )

    def get_leg_standings(self) -> list:
        """
        Return RACING camel colours sorted by standing (best → worst).

        Tiebreak: higher stack_order = further ahead on the same tile.
        """
        racing = [c for c in self.state.camels if not c.is_crazy]
        sorted_camels = sorted(
            racing,
            key=lambda c: (c.position, c.stack_order),
            reverse=True,
        )
        return [c.color for c in sorted_camels]

    def advance_turn(self):
        n = len(self.state.players)
        self.state.current_player_idx = (self.state.current_player_idx + 1) % n
        self.state.turn_number += 1

    def get_state(self) -> GameState:
        return self.state
