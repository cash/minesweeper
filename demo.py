import logging
import minesweeper as ms

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

num_games = 1
config = ms.GameConfig()
ai = ms.RandomAI()
viz = ms.PyGameVisualizer(pause=1, next_game_prompt=True)
result = ms.run_games(config, num_games, ai, viz).pop()
print('Game lasted {0} moves'.format(result.num_moves))
