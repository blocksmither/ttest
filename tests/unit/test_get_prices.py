import os
import unittest

import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetPrices(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_get_prices_v2(self):
        swap = connectors.UniswapV2('mainnet')

        pair_address = '0xe6c78983b07a07e0523b57e18aa23d3ae2519e05'

        result_sdk = swap.get_prices(pair_address)

        self.assertEqual(len(result_sdk), 4)

        result_api = swap.get_prices(pair_address, connection='api')

        diff = sum(tuple(abs(a_i - b_i) for a_i, b_i in zip(result_sdk, result_api)))

        self.assertLessEqual(diff, 100)

    def test_get_prices_sushi(self):
        swap = connectors.Sushiswap('mainnet')

        pair_address = '0x397ff1542f962076d0bfe58ea045ffa2d347aca0'

        result_sdk = swap.get_prices(pair_address)

        self.assertEqual(len(result_sdk), 4)

        result_api = swap.get_prices(pair_address, connection='api')

        diff = sum(tuple(abs(a_i - b_i) for a_i, b_i in zip(result_sdk, result_api)))

        self.assertLessEqual(diff, 100)

    def test_get_prices_v3(self):
        swap = connectors.UniswapV3('mainnet')

        pair_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'

        result_sdk = swap.get_prices(pair_address)

        self.assertEqual(len(result_sdk), 5)

        result_api = swap.get_prices(pair_address, connection='api')

        self.assertLessEqual(abs(result_sdk[0] - result_api[0]), 10)
        self.assertLessEqual(abs(result_sdk[1] - result_api[1]), 10)
        self.assertEqual(result_sdk[2], result_api[2])
