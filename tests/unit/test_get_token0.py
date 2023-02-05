import os
import unittest

import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetToken0(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_get_token0(self):
        expected = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        swap = connectors.UniswapV2('mainnet')

        pair_address = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'

        result = swap.get_token0(pair_address)

        self.assertEqual(result, expected)

    def test_sushi_get_token0(self):
        expected = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        swap = connectors.Sushiswap('mainnet')

        pair_address = '0x397ff1542f962076d0bfe58ea045ffa2d347aca0'

        result = swap.get_token0(pair_address)

        self.assertEqual(result, expected)

    def test_v3_get_token0(self):
        expected = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        swap = connectors.UniswapV3('mainnet')

        pair_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'

        result = swap.get_token0(pair_address)

        self.assertEqual(result, expected)
