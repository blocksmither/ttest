Installation
========
Python 3.6.8

Python package::

    pip install -r requirements.txt

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
This script keeps track of a price and prints everytime there is a change in price (It shows that changes in the SDK show faster and are more consistent)

    $ python watcher.py


MEMPOOL READER
========
This script keeps track of the mempool and prints eveytime it reads a new transaction

    $ python mempool.py


TODO:

    * Implement price prediction after transaction