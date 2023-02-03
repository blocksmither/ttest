import os
import unittest

import yaml
from web3 import Web3
from swap import get_v2_pair

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetV2Pair(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))
        self.token_in = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        self.token_out = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

    def test_uniswapv2(self):
        router_name = 'uniswapv2'
        pair_address = get_v2_pair(self.w3, self.token_in, self.token_out, router_name)

        expected = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'

        self.assertEqual(pair_address.lower(), expected.lower())