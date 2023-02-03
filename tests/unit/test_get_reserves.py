import os
import unittest

import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetV2PairReserves(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_get_v2_pair_reserves(self):
        swap = connectors.UniswapV2('mainnet')

        pair_address = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'

        result = swap.get_pair_reserves(pair_address)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['token0'], int)
        self.assertIsInstance(result['token1'], int)
