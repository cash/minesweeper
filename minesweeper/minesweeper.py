import abc
import enum
import itertools
import random


class GameConfig:
    """Minesweeper game configuration

    Attributes:
        width (int): Width of the board.
        height (int): Height of the board.
        num_mines (int): Number of mines for the game.
    """
    def __init__(self, width=8, height=8, num_mines=10):
        self.width = width
        self.height = height
        self.num_mines = num_mines


class GameStatus (enum.Enum):
    """Game status enum"""
    PLAYING = 1
    VICTORY = 2
    DEFEAT = 3


class GameResult:
    """Result of a single minesweeper game

    Attributes:
        victory (bool): Whether the player won.
        num_moves (int): Number of moves in the game.
    """
    def __init__(self, victory, num_moves):
        self.victory = victory
        self.num_moves = num_moves


class Square:
    """Square information

    Attributes:
        x (int): Zero-based x position.
        y (int): Zero-based y position.
        num_mines (int): Number of mines in neighboring squares.
    """
    def __init__(self, x, y, num_mines):
        self.x = x
        self.y = y
        self.num_mines = num_mines

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y and self.num_mines == other.num_mines
        return NotImplemented

    def __hash__(self):
        return hash((self.x, self.y, self.num_mines))


class MoveResult:
    """Result of a square selection

    Attributes:
        status (GameStatus): Status of the current game.
        new_squares (set): The set of Square objects exposed by the selection.
    """
    def __init__(self, status, new_squares=()):
        self.status = status
        self.new_squares = set(new_squares)


class Game:
    """Minesweeper game engine

    The board uses zero-based indexing of [x][y].

    Attributes:
        width (int): Width of the board.
        height (int): Height of the board.
        num_mines (int): Number of mines.
        num_moves (int): Number of moves made by the player.
        mines (list): 2d list of booleans indicating mine locations.
        exposed (list): 2d list of booleans indicating exposed squares.
        counts (list): 2d list of integer counts of neighboring mines.
        flags (set): set of (x,y) tuples for flag positions.
    """

    def __init__(self, config):
        self.width = config.width
        self.height = config.height
        self.num_mines = config.num_mines
        self.num_moves = 0
        self._num_exposed_squares = 0
        self._explosion = False
        self._num_safe_squares = self.width * self.height - self.num_mines
        self.mines = [[False for y in range(self.height)] for x in range(self.width)]
        self.exposed = [[False for y in range(self.height)] for x in range(self.width)]
        self.counts = [[0 for y in range(self.height)] for x in range(self.width)]
        self.flags = {}

        self._place_mines()
        self._init_counts()

    @property
    def state(self):
        """list: 2d list of the state of the board from the player's perspective

        None means not exposed and the rest are counts of neighboring mines.
        """
        state = [[None for y in range(self.height)] for x in range(self.width)]
        for x, y in itertools.product(range(self.width), range(self.height)):
            if self.exposed[x][y]:
                state[x][y] = self.counts[x][y]
        return state

    @property
    def status(self):
        """GameStatus: Current status of the game"""
        status = GameStatus.PLAYING
        if self.game_over:
            status = GameStatus.DEFEAT if self._explosion else GameStatus.VICTORY
        return status

    @property
    def game_over(self):
        """bool: Is the game over"""
        return self._explosion or self._num_exposed_squares == self._num_safe_squares

    @property
    def result(self):
        """GameResult: information about the game result"""
        if not self.game_over:
            raise ValueError('Game is not over')
        return GameResult(not self._explosion, self.num_moves)

    def select(self, x, y):
        """Select a square to expose.

        Args:
            x (int): Zero-based x position.
            y (int): Zero-based y position.

        Returns:
            MoveResult: Did a mine explode and list of squares exposed.

        Raises:
            ValueError: if game over, squared already selected, or position off the board
        """
        if self._is_outside_board(x, y):
            raise ValueError('Position ({},{}) is outside the board'.format(x, y))
        if self._explosion:
            raise ValueError('Game is already over')
        if self.exposed[x][y]:
            raise ValueError('Position already exposed')
        self.num_moves += 1
        # must call update before accessing the status
        squares = self._update(x, y)
        return MoveResult(self.status, squares)

    def set_flags(self, flags):
        self.flags = flags

    def _place_mines(self):
        locations = set()
        while len(locations) < self.num_mines:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            locations.add((x, y))
        for location in locations:
            self.mines[location[0]][location[1]] = True

    def _init_counts(self):
        """Calculates how many neighboring squares have mines for all squares"""
        for x, y in itertools.product(range(self.width), range(self.height)):
            for dx, dy in itertools.product([-1, 0, 1], repeat=2):
                if dx == 0 and dy == 0:
                    continue
                if not self._is_outside_board(x + dx, y + dy):
                    self.counts[x][y] += self.mines[x + dx][y + dy]

    def _update(self, x, y):
        """Update the state of the game

        Finds all the squares to expose based on a selection.
        This uses an 8 neighbor region growing algorithm to expand the board if
        the chosen square is not a neighbor to a mine.
        Returns a list of squares that have been exposed.
        """
        self._expose_square(x, y)
        squares = [Square(x, y, self.counts[x][y])]
        if self.mines[x][y]:
            self._explosion = True
            return squares
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
                                squares.append(Square(new_x, new_y, self.counts[new_x][new_y]))
                                if self._test_count(new_x, new_y):
                                    stack.append((new_x, new_y))
        return squares

    def _expose_square(self, x, y):
        self.exposed[x][y] = True
        self._num_exposed_squares += 1

    def _test_count(self, x, y):
        """Does this square have a count of zero?"""
        return self.counts[x][y] == 0

    def _is_outside_board(self, x, y):
        if x < 0 or x >= self.width:
            return True
        if y < 0 or y >= self.height:
            return True
        return False


class GameAI(abc.ABC):
    """Minesweeper AI Base class"""

    @abc.abstractmethod
    def reset(self, config):
        """Reset an AI to play a new game

        Args:
            config (GameConfig): game configuration
        """
        pass

    @abc.abstractmethod
    def next(self):
        """Get the next move from the AI

        Returns:
            tuple: x,y position with zero-based index
        """
        pass

    @abc.abstractmethod
    def update(self, result):
        """Notify the AI of the result of the move

        Args:
            result (MoveResult): Information about the move.
        """
        pass

    def flags(self):
        """Get a list of guessed mine locations

        This is for display only. Override if desired.

        Returns:
            list: List 2d tuples with x,y positions
        """
        return []


class RandomAI(GameAI):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.exposed_squares = set()

    def reset(self, config):
        self.width = config.width
        self.height = config.height
        self.exposed_squares.clear()

    def next(self):
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.exposed_squares:
                break
        print('selecting point ({0},{1})'.format(x, y))
        return x, y

    def update(self, result):
        for position in result.new_squares:
            self.exposed_squares.add((position.x, position.y))


class GameVisualizer(abc.ABC):
    """Game visualization base class"""

    @abc.abstractmethod
    def start(self, game):
        """Start visualizing a new game

        Args:
            game (Game): Minesweeper game object.
        """
        pass

    @abc.abstractmethod
    def update(self, game):
        """Update the display

        Args:
            game (Game): Minesweeper game object.
        """
        pass

    @abc.abstractmethod
    def finish(self, game):
        """Complete the visualization of a game

        Args:
            game (Game): Minesweeper game object.
        """
        pass


def run_games(config, num_games, ai, viz=None):
    """ Run a set of games to evaluate an AI

    Args:
        config (GameConfig): Parameters of the game.
        num_games (int): Number of games.
        ai (GameAI): The AI
        viz (, optional): Visualizer

    Returns:
        list: List of GameResult objects
    """
    results = []
    for x in range(num_games):
        game = Game(config)
        ai.reset(config)
        if viz: viz.start(game)
        while not game.game_over:
            coords = ai.next()
            result = game.select(*coords)
            ai.update(result)
            if result.status == GameStatus.PLAYING:
                game.set_flags(ai.flags())
            if viz: viz.update(game)
        if viz: viz.finish(game)
        results.append(game.result)
    return results
