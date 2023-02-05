import os
import unittest

import yaml
from connectors import connectors

from comparator import compare

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestCompare(unittest.TestCase):
    def setUp(self):
        self.network = 'mainnet'
        self.connectors = {
            'UniswapV2': connectors.UniswapV2(self.network),
            'UniswapV3': connectors.UniswapV3(self.network),
            'Sushiswap': connectors.Sushiswap(self.network)
        }
        self.pairs = [
            {
                'id': '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV2'
            },
            {
                'id': '0x397ff1542f962076d0bfe58ea045ffa2d347aca0',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'Sushiswap'
            },
            {
                'id': '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
                'feeTier': '500',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV3'
            },
            {
                'id': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',
                'feeTier': '3000',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV3'
            },
            {
                'id': '0xe0554a476a092703abdb3ef35c80e0d76d32939f',
                'feeTier': '100',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV3'
            },
            {
                'id': '0x7bea39867e4169dbe237d55c8242a8f2fcdcc387',
                'feeTier': '10000',
                'token0': {'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'symbol': 'USDC', 'decimals': '6'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV3'
            }
        ]

    def test_compare(self):
        swap_args = compare(self.pairs)

        self.assertIsNotNone(swap_args.get('inToken'))
        self.assertIsNotNone(swap_args.get('arbToken'))
        self.assertIsNotNone(swap_args.get('dexs'))
        self.assertIsNotNone(swap_args.get('arb'))

    def test_compare_one_option(self):
        pairs = [
            {
                'id': '0xbab761277f52fff80e35a961b4c63e95c733ddbf',
                'token0': {'id': '0x7d8d7c26179b7a6aebbf66a91c38ed92d5b4996b', 'symbol': 'FUND', 'decimals': '18'},
                'token1': {'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'symbol': 'WETH', 'decimals': '18'},
                'dex': 'UniswapV2'
            }
        ]
        with self.assertRaises(Exception):
            compare(pairs)
