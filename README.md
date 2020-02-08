[![Build Status](https://travis-ci.org/cash/minesweeper.svg?branch=master)](https://travis-ci.org/cash/minesweeper) [![Coverage Status](https://coveralls.io/repos/cash/minesweeper/badge.svg?branch=master&service=github)](https://coveralls.io/github/cash/minesweeper?branch=master)

Minesweeper Engine
==================
This is a minesweeper implementation in python. It is not an interactive game,
but an engine for evaluating game AI algorithms. Versions made for interactive
playing tend to not place any mines until the player has selected the first
square and may layout the mines to guarantee success if the player is perfect.
This implementation does neither.

Installing
---------------
Python 3.5 or greater is required for this code.
The dependencies are installed through pip:

```
pip install -r requirements.txt
```

Running a demo
---------------
The `demo.py` script runs a single game using a random bot.

```
python demo.py
```

Building your AI
------------------
An AI must implement the ```GameAI``` interface with three methods: `reset()`, `next()`, 
and `update()`. `reset()` should clear any state of the AI and is called before starting
a new game. It receives as a parameter the game configuration which includes the
width and height of the board and the number of mines. `next()` is called for each move
and should return the x and y coordinates of the next move as a tuple. The coordinates
are zero-based. `update()` is called after the move has been processed and receives the 
result of the move.

An AI that randomly selects each move would look like the following:

```python
import random
import minesweeper as ms

class RandomAI(ms.GameAI):
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
```

Running a game
----------------
The minesweeper module contains a run function that accepts the game configuration, 
number of games, and the AI.

```python
import minesweeper as ms

num_games = 100
config = ms.GameConfig(width=50, height=50, num_mines=20)
ai = MyAI()
results = ms.run_games(config, num_games, ai)
```


Running with a visualizer
---------------------------
A visualizer is included to help debug and improve an AI. You can step through
each move with either a timed delay or pressing the enter key. This is selected
during construction:

```python
viz = ms.PyGameVisualizer(pause=2)
```
or
```python
viz = ms.PyGameVisualizer(pause='key')
```

The visualizer is then passed to the run function:

```python
results = ms.run_games(config, num_games, ai, viz)
```

Standard game sizes
-------------------------
Classic Microsoft Minesweeper had 3 standard game sizes:
 * Beginner: 8 x 8 with 10 mines
 * Intermediate: 16 x 16 with 40 mines
 * Expert: 30 x 16 with 99 mines
