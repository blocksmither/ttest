Installation
========
Python 3.10.9

Python package::

    pip install -r requirements.txt


TESTS
========
    $ python -m unittest


MEMPOOL READER
========
This script keeps track of the mempool and prints eveytime it reads a new transaction

    $ python mempool.py


TODO:

- better/cleaner code organization of new files and swap classes
- After arb opportunity detection, find a matching pair
  - Calculate optimal swap amount in arbitrage transaction
  - Test arbitrage on ganache mainnet fork
- handle more methods, including Uniswap V3 methods
- handle len(path)>2 (i.e. parse multiple swaps)
- estimate swap amounts (swaps specify an exact input or output amount, and only a max/min amount for the other side. Currently I use the max/min amount.  We can estimate the amount against the top of the last block)
- run faster by getting pair_address from hashmap if we already have it, and only call contract if we don't (then save to hashmap for later)
- Create logging levels ERR,INFO,DEBUG


Logic Steps:

1. Listen to mempool source  (blocknative)
2. Filter TX by calls to uniswapv2,v3 router, autorouter, or sushiswap
3. Filter for the swap function types (a few types per router) to find TX that skew the LP balances.
4. Look at swap tokenIn, tokenOut amounts, if either is > $threshold_percent then examine for arb 
5. find matching pairs on other dex or same dex.
6. Calculate optimal swap amount and potential arb profit and arb gas cost.  If bot holds token then use held tokens for arb swap, if not, borrow token and calculate borrow cost in profit calculation.
7. If arb profit > (gas cost + a%) then call arb multiswap, directly or bundle tx with other tx and send to manifold or mevboost relay.
