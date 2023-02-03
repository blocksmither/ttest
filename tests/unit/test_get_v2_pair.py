import os
import unittest

import hashmap_util as hutil
import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetV2Pair(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))
        self.token_in = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        self.token_out = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'

    def test_uniswapv2_and_find_pairs_given_pair(self):
        swap = connectors.UniswapV2('mainnet')

        pair_address = swap.get_pair(self.token_in, self.token_out)

        pair_address2 = hutil.find_pairs(self.token_in, self.token_out, dex='UniswapV2')[0]['id']

        self.assertEqual(pair_address.lower(), pair_address2.lower())

    def test_connector_get_pair(self):
        expected = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'

        swap = connectors.UniswapV2('mainnet')

        pair_address = swap.get_pair(self.token_in, self.token_out)

        self.assertEqual(pair_address.lower(), expected.lower())

    def test_find_pairs(self):
        pair_address = hutil.find_pairs(self.token_in)

        self.assertTrue(len(pair_address) > 0)

    def test_find_pairs_failed(self):
        with self.assertRaises(Exception):
            hutil.find_pairs("dasdas")

    def test_find_pairs_alt_dex(self):
        pairs = hutil.find_pairs(self.token_in, self.token_out, alt_dex='UniswapV2')

        for pair in pairs:
            self.assertTrue(pair['dex'] != 'UniswapV2')
