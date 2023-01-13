Installation
========
Python 3.7.3

Python package::

    pip install -r requirements.txt


LINKGRAPHER
=========

Install `neo4j` and start neo4j service before running `linkgrapher.py` according to installation instructions for your OS.  
Enable remote connection to neo4j. You can view neo4j page to visualize graphs at http://localhost:7474.

`linkgrapher_query.py` is used to create a graph database with each node being a pair or pool and edge relationships linking nodes if they share the same ERC20 Token

- Node
  - id (Address of pool or pair)
  - token0 (Address of token0)
  - token0symbol (Shortform symbol of token0)
  - token1 (Address of token1)
  - token1symbol (Shortform symbol of token1)

Finding pools is done using subgraph. Queries to subgraph are limited and fully building all graphs may require queries which are not free. Therefore it doesn't make sense to query multiple times. Also it's difficult to share the graph database between us. Instead the raw json format result from subgraph is saved into local files.

A separate function reads the json files and creates the neo4j graphs with `linkgrapher_database.py`

Finding linked pairs example:

`find_shared_token_pairs('0x0002bc7e2db8df0f26b6db17e1f5e661cb07ebcb','0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')`

Will return an array of pair addresses that use WETH token (0xc02a)

TODO:
 * Find better way to query pairs than subgraph because subgraph results are limited and cost to query all pairs
   * If subgraph is used, write logic to paginate queries and save results, so queries do not need to be repeated as they cost
 * Add logic to only create new relationship edges so graph DB can be updated. Current logic will duplicate relationship edges.
 * Create new relationship `IDENTICAL_PAIR` type when both tokens match. [(P1.token0 = P2.token0 or P2.token1) and (P1.token1 = P2.token0 or P2.token1)]
   * If using Bitwise logic:
   * (P1.token0 & P2.token0 = A), (P1.token0 & P2.token1 = B), (P1.token1 & P2.token0 = C), (P1.token1 & P2.token1 = D)
   * isIdenticalBool = AD | BC 
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

    * Try swapping on testnet
