import json
import os
import unittest

import yaml
from swap import RouterSwap, get_swap_blocknative

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestGetSwapBlocknative(unittest.TestCase):

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
            token_in=self.params['path'][0],
            token_in_amount=int(self.params['amountIn']),
            token_out=self.params['path'][1],
            token_out_amount=int(self.params['amountOutMin']),
            router_name='uniswapv302',
            swap_method='swapExactTokensForTokens',
            router_address=self.router_address,
            dex_name='uniswapv2'
        )

        self.assertEqual(automatic, manual)

    def testExceptionRaisedForInvalidRouterAddress(self):
        with self.assertRaises(Exception):
            get_swap_blocknative(self.subcall, "invalid", self.blocknative_data)


if __name__ == "__main__":
    unittest.main()
