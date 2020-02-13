import os
import time

# turn off pygame printing a message on import
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'off'
import pygame
import pygame.locals

from .minesweeper import GameVisualizer


class PyGameVisualizer(GameVisualizer):
    """Visualize a minesweeper game with PyGame"""
    TILE_SIZE = 16
    COLOR_GRAY = (189, 189, 189)
    TILES_FILENAME = os.path.join(os.path.dirname(__file__), 'tiles.png')
    TILE_HIDDEN = 9
    TILE_EXPLODED = 10
    TILE_BOMB = 11
    TILE_FLAG = 12
    WINDOW_NAME = 'Minesweeper'

    def __init__(self, pause=3, next_game_prompt=False):
        """
        Args:
            pause (int, str): How long to pause between moves in seconds or 'key' for pressing enter to continue.
            next_game_prompt (bool): Whether to ask the user to proceed to next game (or quit).
        """
        self.pause = pause
        self.next_game_prompt = next_game_prompt
        self.game_width = 0
        self.game_height = 0
        self.screen = None
        self.tiles = None

    def run(self, runner):
        game = runner.game
        self.game_width = game.width
        self.game_height = game.height

        pygame.init()
        pygame.mixer.quit()  # if we don't turn off sound, uses 100% cpu
        pygame.display.set_caption(self.WINDOW_NAME)
        screen_width = self.TILE_SIZE * self.game_width
        screen_height = self.TILE_SIZE * self.game_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.screen.fill(self.COLOR_GRAY)
        self.tiles = self._load_tiles()

        next(runner)
        self._draw(game)
        if isinstance(self.pause, str):
            print("Press any key for each move")
            pygame.event.clear()
            while not game.game_over:
                event = pygame.event.wait()
                if event.type == pygame.locals.KEYDOWN:
                    next(runner)
                    self._draw(game)
                elif event.type == pygame.locals.QUIT:
                    game.quit()
                    break
        else:
            while not game.game_over:
                time.sleep(self.pause)
                next(runner)
                self._draw(game)

        if self.next_game_prompt:
            print("Hit any key to continue...")
            while True:
                event = pygame.event.wait()
                if event.type in [pygame.locals.KEYDOWN, pygame.locals.QUIT]:
                    break

        pygame.quit()

    def _load_tiles(self):
        image = pygame.image.load(self.TILES_FILENAME).convert()
        image_width, image_height = image.get_size()
        tiles = []
        for tile_x in range(0, image_width // self.TILE_SIZE):
            rect = (tile_x * self.TILE_SIZE, 0, self.TILE_SIZE, self.TILE_SIZE)
            tiles.append(image.subsurface(rect))
        return tiles

    def _draw(self, game):
        for x in range(self.game_width):
            for y in range(self.game_height):
                if not game.exposed[x][y]:
                    if (x, y) in game.flags:
                        tile = self.tiles[self.TILE_FLAG]
                    else:
                        tile = self.tiles[self.TILE_HIDDEN]
                else:
                    if game.mines[x][y]:
                        tile = self.tiles[self.TILE_EXPLODED]
                    else:
                        tile = self.tiles[game.counts[x][y]]
                self.screen.blit(tile, (16 * x, 16 * y))
        pygame.display.flip()
