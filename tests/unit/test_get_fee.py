import os
import unittest

import yaml
from connectors import connectors
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetFee(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_get_fee(self):
        swap = connectors.UniswapV3('mainnet')

        pair_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'

        result = swap.get_pair_fee(pair_address)

        self.assertEqual(result, 0.0005)
