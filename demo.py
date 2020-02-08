import minesweeper as ms


num_games = 1
config = ms.GameConfig()
ai = ms.RandomAI()
viz = ms.GameVisualizer('key')
results = ms.run_games(config, 1, ai, viz)
if results[0].success:
    print('Success!')
else:
    print('Boom!')
print('Game lasted {0} moves'.format(results[0].num_moves))
