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

    def test_connector_sushi_get_pair(self):
        expected = '0x397ff1542f962076d0bfe58ea045ffa2d347aca0'

        swap = connectors.Sushiswap('mainnet')

        pair_address = swap.get_pair(self.token_in, self.token_out)

        self.assertEqual(pair_address.lower(), expected.lower())

    def test_connector_v3_get_pair(self):
        expected = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'

        swap = connectors.UniswapV3('mainnet')

        pair_address = swap.get_pair(self.token_in, self.token_out)

        self.assertEqual(pair_address.lower(), expected.lower())

    def test_find_pairs(self):
        pair_address = hutil.find_pairs(self.token_in)

        self.assertTrue(len(pair_address) > 0)

    def test_find_pair_fee(self):
        expected = '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
        pair_address = hutil.find_pairs(self.token_in, self.token_out, dex='UniswapV3', fee="3000")

        self.assertEqual(pair_address[0]['id'].lower(), expected.lower())

    def test_find_pairs_failed(self):
        with self.assertRaises(Exception):
            hutil.find_pairs("dasdas")

    def test_find_pairs_alt_dex(self):
        pairs = hutil.find_pairs(self.token_in, self.token_out, alt_dex='UniswapV2')

        for pair in pairs:
            self.assertTrue(pair['dex'] != 'UniswapV2')

    def test_find_pairs_not_in_hash(self):
        expected = [
            {
                'id': '0x457862DbB4E43281720e84D62Eb0Ca5914Bf857A',
                'token0': {'id': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'symbol': 'WETH', 'decimals': 18},
                'token1': {'id': '0xC30d724E3E370dfCEC3b5705CE4AF2B23D6e2E49', 'symbol': 'YEET', 'decimals': 18},
                'dex': 'UniswapV2'
            },
            {
                'id': '0x0000000000000000000000000000000000000000',
                'token0': {'id': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'symbol': 'WETH', 'decimals': 18},
                'token1': {'id': '0xC30d724E3E370dfCEC3b5705CE4AF2B23D6e2E49', 'symbol': 'YEET', 'decimals': 18},
                'dex': 'Sushiswap'
            }
        ]

        pairs = hutil.get_alt_pairs(self.token_in, '0xC30d724E3E370dfCEC3b5705CE4AF2B23D6e2E49')
        self.assertEqual(pairs, expected)
