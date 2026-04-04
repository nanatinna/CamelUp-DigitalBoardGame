import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from game.game_logic import CamelUpGame
from game.models import CAMEL_COLORS, CRAZY_CAMEL_COLORS, ALL_CAMEL_COLORS, DICE_COLORS


class TestInitialisation(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_player_count(self):
        self.assertEqual(len(self.game.get_state().players), 2)

    def test_camel_count(self):
        # 5 racing + 2 crazy = 7
        self.assertEqual(len(self.game.get_state().camels), 7)

    def test_all_dice_available(self):
        # 6 dice: 5 racing + 1 grey die
        self.assertEqual(len(self.game.get_state().dice_remaining), 6)

    def test_racing_camels_on_tiles_1_to_3(self):
        for camel in self.game.get_state().camels:
            if not camel.is_crazy:
                self.assertIn(camel.position, [1, 2, 3],
                              f"{camel.color} starts on {camel.position}")

    def test_crazy_camels_on_tiles_14_to_16(self):
        for camel in self.game.get_state().camels:
            if camel.is_crazy:
                self.assertIn(camel.position, [14, 15, 16],
                              f"crazy {camel.color} starts on {camel.position}")

    def test_crazy_camel_colors(self):
        crazy = [c for c in self.game.get_state().camels if c.is_crazy]
        self.assertEqual(len(crazy), 2)
        crazy_colors = {c.color for c in crazy}
        self.assertEqual(crazy_colors, set(CRAZY_CAMEL_COLORS))

    def test_starting_coins(self):
        for p in self.game.get_state().players:
            self.assertEqual(p.coins, 3)

    def test_leg_bet_tiles_initialised(self):
        state = self.game.get_state()
        for color in CAMEL_COLORS:
            self.assertEqual(state.available_leg_bets[color], [5, 3, 2, 1])


class TestRollDice(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_reduces_dice_remaining(self):
        before = len(self.game.get_state().dice_remaining)
        self.game.roll_dice(0)
        self.assertEqual(len(self.game.get_state().dice_remaining), before - 1)

    def test_gives_player_one_coin(self):
        coins_before = self.game.get_state().players[0].coins
        self.game.roll_dice(0)
        self.assertEqual(self.game.get_state().players[0].coins, coins_before + 1)

    def test_result_keys(self):
        result = self.game.roll_dice(0)
        for key in ('color', 'steps', 'end_of_leg', 'new_position'):
            self.assertIn(key, result)

    def test_steps_in_range(self):
        result = self.game.roll_dice(0)
        self.assertIn(result['steps'], [1, 2, 3])

    def test_color_removed_from_remaining(self):
        result = self.game.roll_dice(0)
        self.assertNotIn(result['color'], self.game.get_state().dice_remaining)

    def test_all_five_racing_dice_trigger_end_of_leg(self):
        # Force only racing dice so the leg ends deterministically in 5 rolls
        self.game.state.dice_remaining = list(CAMEL_COLORS)
        end_of_leg_seen = False
        for _ in range(5):
            state = self.game.get_state()
            if not state.dice_remaining:
                break
            result = self.game.roll_dice(state.current_player_idx)
            if result.get('end_of_leg'):
                end_of_leg_seen = True
        # After exhausting all 5 racing dice, end_of_leg must have fired
        # (dice_remaining resets to 6 after leg ends)
        self.assertTrue(end_of_leg_seen or len(self.game.get_state().dice_remaining) == 6,
                        "end_of_leg should trigger after all 5 racing dice rolled")

    def test_crazy_dice_alone_do_not_end_leg(self):
        # Remove all racing dice — only the grey die remains
        self.game.state.dice_remaining = ['grey']
        result = self.game.roll_dice(0)
        # Rolling the grey die alone should NOT end the leg
        self.assertFalse(result.get('end_of_leg'),
                         "leg must not end when only the grey die is rolled")


class TestLegBetting(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_takes_highest_tile(self):
        color = CAMEL_COLORS[0]
        self.game.take_leg_bet(0, color)
        self.assertEqual(self.game.get_state().players[0].leg_bets[0].value, 5)

    def test_remaining_tiles_update(self):
        color = CAMEL_COLORS[0]
        self.game.take_leg_bet(0, color)
        self.assertEqual(self.game.get_state().available_leg_bets[color], [3, 2, 1])

    def test_returns_false_when_empty(self):
        color = CAMEL_COLORS[0]
        for _ in range(4):
            self.game.take_leg_bet(0, color)
        result = self.game.take_leg_bet(0, color)
        self.assertFalse(result)

    def test_player_gains_bet_tile(self):
        color = CAMEL_COLORS[1]
        self.game.take_leg_bet(0, color)
        self.assertEqual(len(self.game.get_state().players[0].leg_bets), 1)


class TestRaceBetting(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_adds_race_bet(self):
        self.game.place_race_bet(0, 'blue', 'winner')
        bets = self.game.get_state().players[0].race_bets
        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].camel_color, 'blue')
        self.assertEqual(bets[0].bet_type, 'winner')

    def test_multiple_race_bets(self):
        self.game.place_race_bet(0, 'blue', 'winner')
        self.game.place_race_bet(0, 'green', 'loser')
        self.assertEqual(len(self.game.get_state().players[0].race_bets), 2)


class TestDesertTile(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_valid_placement(self):
        result = self.game.place_desert_tile(0, 5, 'oasis')
        self.assertTrue(result)
        state = self.game.get_state()
        self.assertIn(5, state.desert_tiles)
        self.assertTrue(state.players[0].desert_tile_placed)

    def test_tile_1_invalid(self):
        self.assertFalse(self.game.place_desert_tile(0, 1, 'oasis'))

    def test_occupied_tile_invalid(self):
        state = self.game.get_state()
        occupied = state.camels[0].position
        self.assertFalse(self.game.place_desert_tile(0, occupied, 'oasis'))

    def test_cannot_place_twice_in_leg(self):
        self.game.place_desert_tile(0, 5, 'oasis')
        actions = self.game.get_valid_actions(0)
        self.assertNotIn('desert_tile', actions)


class TestStackingLogic(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def _isolate_two_racing_camels(self, tile: int):
        """Put camels[0] and [1] (racing) on *tile*, park everything else far away."""
        state = self.game.get_state()
        state.camels[0].position    = tile
        state.camels[0].stack_order = 0
        state.camels[1].position    = tile
        state.camels[1].stack_order = 1
        for i, c in enumerate(state.camels[2:], start=2):
            c.position    = 16
            c.stack_order = i   # unique so no stack conflicts
        return state.camels[0].color, state.camels[1].color

    def test_stack_carries_camels_above(self):
        c0_color, c1_color = self._isolate_two_racing_camels(4)
        self.game.move_camel(c0_color, 2)
        state = self.game.get_state()
        c0 = next(c for c in state.camels if c.color == c0_color)
        c1 = next(c for c in state.camels if c.color == c1_color)
        self.assertEqual(c0.position, 6)
        self.assertEqual(c1.position, 6)

    def test_upper_camel_does_not_carry_lower(self):
        c0_color, c1_color = self._isolate_two_racing_camels(4)
        # Move the TOP camel (stack_order=1) by 2 steps
        self.game.move_camel(c1_color, 2)
        state = self.game.get_state()
        c0 = next(c for c in state.camels if c.color == c0_color)
        c1 = next(c for c in state.camels if c.color == c1_color)
        # Bottom camel stays put, top camel moves
        self.assertEqual(c0.position, 4)
        self.assertEqual(c1.position, 6)


class TestCrazyCamelMechanics(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_crazy_camel_moves_backward(self):
        state = self.game.get_state()
        crazy = next(c for c in state.camels if c.is_crazy)
        # Park all other camels far away
        for c in state.camels:
            if c is not crazy:
                c.position = 8
                c.stack_order = 0
        crazy.position    = 10
        crazy.stack_order = 0
        self.game.move_camel(crazy.color, 2)
        self.assertEqual(crazy.position, 8)

    def test_crazy_camel_goes_under_existing_stack(self):
        state = self.game.get_state()
        crazy = next(c for c in state.camels if c.is_crazy)
        racing = next(c for c in state.camels if not c.is_crazy)
        # Park other camels far away
        for c in state.camels:
            if c is not crazy and c is not racing:
                c.position = 1
                c.stack_order = 0
        # Racing camel already on destination tile
        racing.position    = 8
        racing.stack_order = 0
        crazy.position     = 10
        crazy.stack_order  = 0
        self.game.move_camel(crazy.color, 2)  # crazy moves from 10 to 8
        # Crazy camel must be at the BOTTOM (stack_order < racing camel)
        self.assertEqual(crazy.position, 8)
        self.assertLess(crazy.stack_order, racing.stack_order)


class TestLegStandings(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def test_higher_position_ranks_first(self):
        state = self.game.get_state()
        state.camels[0].position    = 10
        state.camels[0].stack_order = 0
        state.camels[1].position    = 6
        state.camels[1].stack_order = 0
        for i, c in enumerate(state.camels[2:], start=2):
            c.position = 1
            c.stack_order = i  # unique, no conflicts

        standings = self.game.get_leg_standings()
        self.assertLess(standings.index(state.camels[0].color),
                        standings.index(state.camels[1].color))

    def test_higher_stack_ranks_first_on_same_tile(self):
        state = self.game.get_state()
        state.camels[0].position    = 8
        state.camels[0].stack_order = 0
        state.camels[1].position    = 8
        state.camels[1].stack_order = 1
        for i, c in enumerate(state.camels[2:], start=2):
            c.position = 1
            c.stack_order = i

        standings = self.game.get_leg_standings()
        self.assertLess(standings.index(state.camels[1].color),
                        standings.index(state.camels[0].color))

    def test_crazy_camels_excluded_from_standings(self):
        standings = self.game.get_leg_standings()
        for color in CRAZY_CAMEL_COLORS:
            self.assertNotIn(color, standings)


class TestAdvanceTurn(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob', 'Carol'])

    def test_cycles_through_players(self):
        self.assertEqual(self.game.get_state().current_player_idx, 0)
        self.game.advance_turn()
        self.assertEqual(self.game.get_state().current_player_idx, 1)
        self.game.advance_turn()
        self.assertEqual(self.game.get_state().current_player_idx, 2)
        self.game.advance_turn()
        self.assertEqual(self.game.get_state().current_player_idx, 0)

    def test_increments_turn_number(self):
        t0 = self.game.get_state().turn_number
        self.game.advance_turn()
        self.assertEqual(self.game.get_state().turn_number, t0 + 1)


class TestOasisMirageEffect(unittest.TestCase):
    def setUp(self):
        self.game = CamelUpGame(['Alice', 'Bob'])

    def _place_single_camel_at(self, color: str, position: int):
        state = self.game.get_state()
        target = next(c for c in state.camels if c.color == color)
        target.position    = position
        target.stack_order = 0
        for i, c in enumerate(state.camels):
            if c.color != color:
                c.position    = 2   # parked near start, not past finish
                c.stack_order = i

    def test_oasis_moves_extra_forward(self):
        self.game.place_desert_tile(0, 7, 'oasis')
        color = CAMEL_COLORS[0]
        self._place_single_camel_at(color, 5)
        self.game.move_camel(color, 2)   # would land on 7 → oasis → 8
        state = self.game.get_state()
        moved = next(c for c in state.camels if c.color == color)
        self.assertEqual(moved.position, 8)

    def test_mirage_moves_backward(self):
        self.game.place_desert_tile(0, 7, 'mirage')
        color = CAMEL_COLORS[0]
        self._place_single_camel_at(color, 5)
        self.game.move_camel(color, 2)   # would land on 7 → mirage → 6
        state = self.game.get_state()
        moved = next(c for c in state.camels if c.color == color)
        self.assertEqual(moved.position, 6)

    def test_oasis_owner_gets_coin(self):
        self.game.place_desert_tile(0, 7, 'oasis')
        state = self.game.get_state()
        coins_before = state.players[0].coins
        color = CAMEL_COLORS[0]
        self._place_single_camel_at(color, 5)
        self.game.move_camel(color, 2)
        state = self.game.get_state()
        self.assertEqual(state.players[0].coins, coins_before + 1)


if __name__ == '__main__':
    unittest.main()
