import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from game.models import GameState, Player, Camel, LegBetTile, RaceBet, CAMEL_COLORS, ALL_CAMEL_COLORS, DICE_COLORS


class TestCamel(unittest.TestCase):
    def test_defaults(self):
        c = Camel(color='blue')
        self.assertEqual(c.position, 0)
        self.assertEqual(c.stack_order, 0)

    def test_camel_colors(self):
        self.assertEqual(CAMEL_COLORS, ['green', 'purple', 'yellow', 'blue', 'red'])


class TestPlayer(unittest.TestCase):
    def test_defaults(self):
        p = Player(name='Test')
        self.assertEqual(p.coins, 3)
        self.assertEqual(p.leg_bets, [])
        self.assertEqual(p.race_bets, [])
        self.assertIsNone(p.desert_tile)
        self.assertFalse(p.desert_tile_placed)

    def test_leg_bets_independent(self):
        p1 = Player(name='P1')
        p2 = Player(name='P2')
        p1.leg_bets.append(LegBetTile('blue', 5))
        self.assertEqual(len(p2.leg_bets), 0)

    def test_race_bets_independent(self):
        p1 = Player(name='P1')
        p2 = Player(name='P2')
        p1.race_bets.append(RaceBet('green', 'winner'))
        self.assertEqual(len(p2.race_bets), 0)


class TestLegBetTile(unittest.TestCase):
    def test_creation(self):
        t = LegBetTile(camel_color='green', value=5)
        self.assertEqual(t.camel_color, 'green')
        self.assertEqual(t.value, 5)


class TestRaceBet(unittest.TestCase):
    def test_creation(self):
        b = RaceBet(camel_color='orange', bet_type='winner')
        self.assertEqual(b.camel_color, 'orange')
        self.assertEqual(b.bet_type, 'winner')


class TestGameState(unittest.TestCase):
    def test_event_log_independent(self):
        gs1 = GameState(players=[], camels=[])
        gs2 = GameState(players=[], camels=[])
        gs1.event_log.append('test')
        self.assertEqual(len(gs2.event_log), 0)

    def test_desert_tiles_independent(self):
        gs1 = GameState(players=[], camels=[])
        gs2 = GameState(players=[], camels=[])
        gs1.desert_tiles[5] = {'type': 'oasis', 'owner_idx': 0}
        self.assertEqual(len(gs2.desert_tiles), 0)

    def test_dice_remaining_default(self):
        # 6 dice: 5 racing + 1 grey die
        gs = GameState(players=[], camels=[])
        self.assertEqual(gs.dice_remaining, list(DICE_COLORS))


if __name__ == '__main__':
    unittest.main()
