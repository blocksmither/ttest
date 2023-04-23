import os
import unittest

import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetDecimals(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_get_decimals(self):
        swap = connectors.UniswapV2('mainnet')

        token_address = '0xEC4A1c7A4e9Fdc7cc621b548a931c92BC08a679A'
        result = swap.get_token_decimals(token_address)
        self.assertEqual(result, 10)

        token_address = '0x72E5390EDb7727E3d4e3436451DADafF675dBCC0'
        result = swap.get_token_decimals(token_address)
        self.assertEqual(result, 12)

        token_address = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
        result = swap.get_token_decimals(token_address)
        self.assertEqual(result, 18)

        token_address = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
        result = swap.get_token_decimals(token_address)
        self.assertEqual(result, 6)
        
        
