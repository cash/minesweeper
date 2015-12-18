import random
from abc import ABCMeta, abstractmethod


class GameConfig(object):
    def __init__(self, width=8, height=8, num_mines=10):
        self.width = width
        self.height = height
        self.num_mines = num_mines


class Game(object):
    def __init__(self, config):
        self.width = config.width
        self.height = config.height
        self.num_mines = config.num_mines
        self.board = [[False for y in xrange(self.height)] for x in xrange(self.width)]
        self.exposed = [[False for y in xrange(self.height)] for x in xrange(self.width)]
        self.counts = [[0 for y in xrange(self.height)] for x in xrange(self.width)]
        self.num_moves = 0
        self.num_safe_squares = self.width * self.height - self.num_mines
        self.num_exposed_squares = 0
        self.explosion = False

        self._place_mines()
        self._init_counts()

    def select(self, x, y):
        """
        Select a square to expose. Coordinates are zero based.
        If the square has already been selected, returns None.
        Returns a Result object with success/failure and a list of squares
        exposed.
        """
        if self._is_outside_board(x, y):
            raise ValueError('Position ({0},{1}) is outside the board'.format(x, y))
        if self.explosion:
            raise ValueError('Game is already over')
        if self.exposed[x][y]:
            return None
        self.num_moves += 1
        if self.board[x][y]:
            self.explosion = True
            return MoveResult(True)
        return MoveResult(False, self._update_board(x, y))

    def get_state(self):
        """
        Get the current state of the game
        None means not exposed and the rest are counts
        This does not contain the exploded mine if one exploded.
        """
        state = [[None for y in xrange(self.height)] for x in xrange(self.width)]
        for x in xrange(self.width):
            for y in xrange(self.height):
                if self.exposed[x][y]:
                    state[x][y] = self.counts[x][y]
        return state

    def is_game_over(self):
        return self.explosion or self.num_exposed_squares == self.num_safe_squares

    def _place_mines(self):
        mines = set()
        while len(mines) < self.num_mines:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            mines.add((x, y))
        for coords in mines:
            self.board[coords[0]][coords[1]] = True

    def _init_counts(self):
        """Calculates how many neighboring squares have minds for all squares"""
        for x in xrange(self.width):
            for y in xrange(self.height):
                for x_offset in [-1, 0, 1]:
                    for y_offset in [-1, 0, 1]:
                        if x_offset != 0 or y_offset != 0:
                            if not self._is_outside_board(x + x_offset, y + y_offset):
                                self.counts[x][y] += int(self.board[x + x_offset][y + y_offset])

    def _update_board(self, x, y):
        """
        Finds all the squares to expose based on a selection

        This uses an 8 neighbor region growing algorithm to expand the board if
        the chosen square is not a neighbor to a mine.
        """
        self._expose_square(x, y)
        squares = [Position(x, y, self.counts[x][y])]
        if self.counts[x][y] != 0:
            return squares

        stack = [(x, y)]
        while len(stack) > 0:
            (x, y) = stack.pop()
            for x_offset in [-1, 0, 1]:
                for y_offset in [-1, 0, 1]:
                    if x_offset != 0 or y_offset != 0:
                        new_x = x + x_offset
                        new_y = y + y_offset
                        if not self._is_outside_board(new_x, new_y):
                            if not self.exposed[new_x][new_y]:
                                self._expose_square(new_x, new_y)
                                squares.append(Position(new_x, new_y, self.counts[new_x][new_y]))
                                if self._test_count(new_x, new_y):
                                    stack.append((new_x, new_y))
        return squares

    def _expose_square(self, x, y):
        self.exposed[x][y] = True
        self.num_exposed_squares += 1

    def _test_count(self, x, y):
        """Does this square have a count of zero?"""
        return self.counts[x][y] == 0

    def _is_outside_board(self, x, y):
        if x < 0 or x == self.width:
            return True
        if y < 0 or y == self.height:
            return True
        return False


class Position(object):
    def __init__(self, x, y, num_neighbors):
        self.x = x
        self.y = y
        self.num_bomb_neighbors = num_neighbors

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.num_bomb_neighbors == other.num_bomb_neighbors


class MoveResult(object):
    def __init__(self, explosion, new_squares=[]):
        self.explosion = explosion
        self.new_squares = new_squares

    def __eq__(self, other):
        if self.explosion != other.explosion:
            return False
        return set(self.new_squares) == set(other.new_squares)


class GameResult(object):
    def __init__(self, success, num_moves):
        self.success = success
        self.num_moves = num_moves


class GameAI(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def init(self, config):
        """
        Initialize an AI to play a new game
        config is a GameConfig object
        return is void
        """
        pass

    @abstractmethod
    def next(self):
        """
        Returns the next move as a tuple of (x,y)
        """
        pass

    @abstractmethod
    def update(self, result):
        """
        Notify the AI of the result of the previous move
        result is a MoveResult object
        return is void
        """
        pass


def run_games(config, num_games, ai):
    results = []
    for x in xrange(num_games):
        game = Game(config)
        ai.init(config)
        while not game.is_game_over():
            coords = ai.next()
            result = game.select(*coords)
            if result is None:
                continue
            if not result.explosion:
                ai.update(result)
        results.append(GameResult(not game.explosion, game.num_moves))
    return results
