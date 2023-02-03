import json
import os
import unittest

from swap import RouterSwap, get_swap_blocknative


class TestGetSwapBlocknativeMulticall(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'blocknative_tx', 'multicall.json')))) as f:
            blocknative_data = json.load(f)
        self.subcall = blocknative_data['event']['contractCall']['subCalls'][0]
        self.params = self.subcall['data']['params']
        self.router_address = blocknative_data['event']['transaction']['to']
        self.blocknative_data = blocknative_data

    def test_get_swap_blocknative(self):
        automatic = get_swap_blocknative(self.subcall, self.router_address, self.blocknative_data)

        manual = RouterSwap(
            token_in='0x30D20208d987713f46DFD34EF128Bb16C404D10f',
            token_in_amount=1700000000000000000000,
            token_out='0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            token_out_amount=2167846973,
            router_address='0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
            swap_method='swapExactTokensForTokens',
            router_name='uniswapv302',
            dex_name='uniswapv2'
        )

        self.assertEqual(automatic, manual)

    def testExceptionRaisedForInvalidRouterAddress(self):
        with self.assertRaises(Exception):
            get_swap_blocknative(self.subcall, "invalid", self.blocknative_data)
