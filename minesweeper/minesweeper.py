import abc
import copy
import enum
import itertools
import logging
import random

logger = logging.getLogger(__name__)


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
    QUIT = 4


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
    """

    def __init__(self, config, mines=None):
        """
        Args:
            config (GameConfig): Configuration for this game.
            mines (list, optional): Optional mine positions.
        """
        self.width = config.width
        self.height = config.height
        self.num_mines = config.num_mines
        self.num_moves = 0
        self._num_exposed_squares = 0
        self._explosion = False
        self._quit = False
        self._num_safe_squares = self.width * self.height - self.num_mines
        self.exposed = [[False for y in range(self.height)] for x in range(self.width)]
        self.counts = [[0 for y in range(self.height)] for x in range(self.width)]
        self._flags = {}

        if mines:
            self.mines = copy.deepcopy(mines)
        else:
            self.mines = [[False for y in range(self.height)] for x in range(self.width)]
            self._place_mines()
        self._init_counts()
        logger.info("Game initialized")

    @property
    def flags(self):
        """set: set of (x,y) tuples for flag positions"""
        return self._flags

    @flags.setter
    def flags(self, flags):
        self._flags = set(flags)

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
        if not self.game_over:
            status = GameStatus.PLAYING
        elif self._quit:
            status = GameStatus.QUIT
        elif self._explosion:
            status = GameStatus.DEFEAT
        else:
            status = GameStatus.VICTORY
        return status

    @property
    def game_over(self):
        """bool: Is the game over"""
        return self._explosion or self._quit or \
               self._num_exposed_squares == self._num_safe_squares

    @property
    def result(self):
        """GameResult: information about the game result"""
        if not self.game_over:
            raise ValueError('Game is not over')
        return GameResult(self.status == GameStatus.VICTORY, self.num_moves)

    def quit(self):
        """Quit a game"""
        logger.info("Quitting")
        self._quit = True

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
        logger.info("Player has picked %d, %d", x, y)
        if self._is_outside_board(x, y):
            raise ValueError('Position ({},{}) is outside the board'.format(x, y))
        if self._explosion:
            raise ValueError('Game is already over')
        if self.exposed[x][y]:
            raise ValueError('Position already exposed')
        self.num_moves += 1
        # must call update before accessing the status
        squares = self._update(x, y)
        logger.info("%d squares are revealed", len(squares))
        return MoveResult(self.status, squares)

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
            for dx, dy in itertools.product([-1, 0, 1], repeat=2):
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = x + dx, y + dy
                if not self._is_outside_board(new_x, new_y):
                    if not self.exposed[new_x][new_y]:
                        self._expose_square(new_x, new_y)
                        squares.append(Square(new_x, new_y, self.counts[new_x][new_y]))
                        if self._test_if_count_0(new_x, new_y):
                            stack.append((new_x, new_y))
        return squares

    def _expose_square(self, x, y):
        self.exposed[x][y] = True
        self._num_exposed_squares += 1

    def _test_if_count_0(self, x, y):
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

    @property
    def flags(self):
        """list: Get a list of guessed mine locations

        The locations are x,y tuples.
        This is for display only. Override if desired.
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
        return x, y

    def update(self, result):
        for position in result.new_squares:
            self.exposed_squares.add((position.x, position.y))


class GameVisualizer(abc.ABC):
    """Game visualization base class"""

    @abc.abstractmethod
    def run(self, runner):
        """Run a game and display visualization

        Args:
            runner (Runner): Game runner (iterator).
        """
        pass


class Runner:
    """Game Runner as iterator

    Attributes:
        game (Game): Minesweeper game
        ai (GameAI): Minesweeper AI
    """
    def __init__(self, game, ai):
        self.game = game
        self.ai = ai

    def __iter__(self):
        """Returns an iterator"""
        return self

    def __next__(self):
        """Advances the game one move"""
        if not self.game.game_over:
            coordinates = self.ai.next()
            result = self.game.select(*coordinates)
            self.ai.update(result)
            if result.status == GameStatus.PLAYING:
                self.game.flags = self.ai.flags
            else:
                logger.info("Game is over")
        else:
            raise StopIteration()


def run_games(config, num_games, ai, viz=None):
    """ Run a set of games to evaluate an AI

    Args:
        config (GameConfig): Parameters of the game.
        num_games (int): Number of games.
        ai (GameAI): The AI
        viz (GameVisualizer, optional): Visualizer

    Returns:
        list: List of GameResult objects
    """
    results = []
    for n in range(num_games):
        logger.info("Starting game %d", n + 1)
        ai.reset(config)
        game = Game(config)
        runner = Runner(game, ai)
        if viz:
            viz.run(runner)
        else:
            for _ in runner:
                pass
        results.append(game.result)
    return results
