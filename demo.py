import logging
import minesweeper as ms

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

num_games = 1
config = ms.GameConfig()
ai = ms.RandomAI()
viz = ms.PyGameVisualizer(pause='key')
result = ms.run_games(config, num_games, ai, viz).pop()
if result.victory:
    print('Victory!')
else:
    print('Boom!')
print('Game lasted {0} moves'.format(result.num_moves))
