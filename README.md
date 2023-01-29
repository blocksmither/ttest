Installation
========
Python 3.10.9

Python package::

    pip install -r requirements.txt


TESTS
========
    $ python -m unittest


COMPARATOR
========
Help:

    $ python comparator.py -h

If you wish to run a the comparator connecting via API:

    $ python comparator.py

If you wish to run a the comparator connecting via SDK:

    $ python comparator.py -c sdk

If you wish see all the rates retrieved:

    $ python comparator.py -r true

To run a test on a fork mainnet chain, fork mainnet using brownie or ganache, and pass the network flag to comparator.py

    $ ganache-cli --fork https://mainnet.infura.io/v3/9165d99361774eb39d895e8623049a66 2>&1 1>ganache.log &&
    $ python comparator.py -c sdk -n mainnet-fork


WATCHER
========
This script keeps track of a price and prints everytime there is a change in price

    $ python watcher.py


MEMPOOL READER
========
This script keeps track of the mempool and prints eveytime it reads a new transaction

    $ python mempool.py


To predict price changes we have to run separetly the watcher and the mempool with the same variables

    $ python watcher.py -s UniswapV2
    $ python mempool.py -s UniswapV2


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
