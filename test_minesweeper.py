import unittest
from minesweeper import Game


class MineSweeperTestCase(unittest.TestCase):

    def test_init_counts(self):
        game = Game(4, 4, 4)
        board = [
            [True,  False, False, False],
            [False, False, True,  False],
            [False, False, True,  False],
            [False, True,  False, False]
            ]
        counts = [
            [0, 1, 1, 0],
            [1, 2, 1, 2],
            [0, 3, 2, 2],
            [1, 1, 2, 1]
        ]
        game.board = board
        game.counts = [[0 for y in xrange(4)] for x in xrange(4)]
        game._init_counts()
        self.assertEqual(counts, game.counts)