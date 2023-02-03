import json
import os
import unittest

from swap import RouterSwap, get_swap_blocknative


class TestGetSwapBlocknativeSinglecall(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'blocknative_tx', 'singlecall.json')))) as f:
            blocknative_data = json.load(f)
        self.subcall = {'data': blocknative_data['event']['contractCall']}
        self.params = self.subcall['data']['params']
        self.router_address = blocknative_data['event']['transaction']['to']
        self.blocknative_data = blocknative_data

    def test_get_swap_blocknative(self):
        automatic = get_swap_blocknative(self.subcall, self.router_address, self.blocknative_data)

        manual = RouterSwap(
            token_in='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            token_in_amount=4471910857149137564,
            token_out='0x38A94e92A19E970c144DEd0B2DD47278CA11CC1F',
            token_out_amount=1954858848453030,
            router_address='0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            swap_method='swapExactTokensForTokens',
            router_name='uniswapv2',
            dex_name='uniswapv2'
        )

        self.assertEqual(automatic, manual)
