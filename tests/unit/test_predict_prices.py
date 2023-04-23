import os
import unittest

import yaml
from connectors import connectors
from swap import RouterSwap
from web3 import Web3

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))) as f:
    config = yaml.safe_load(f)


class TestPredictPrices(unittest.TestCase):

    def setUp(self):
        self.w3 = Web3(Web3.HTTPProvider(
            config['networks']['mainnet']['web3Provider']))

    def test_predict_prices_v2(self):
        swap = connectors.UniswapV2('mainnet')

        # Taking out token0, injecting token1
        # predicted price should shift the price towards token0
        # current[t0] > predicted[t0]; current[t1] < predicted[t1]
        routerSwap = RouterSwap(
            token_in='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # token1
            token_in_amount=4471910857149137564,
            token_out='0x38A94e92A19E970c144DEd0B2DD47278CA11CC1F',  # token0
            token_out_amount=1954858848453030,
            router_address='0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            swap_method='swapExactTokensForTokens',
            router_name='uniswapv2',
            dex_name='uniswapv2'
        )

        pair_address = swap.get_pair(routerSwap.token_in, routerSwap.token_out)

        current_price = swap.get_prices_sdk(pair_address)
        predicted_price = swap.predict_price(pair_address, routerSwap)

        self.assertGreater(current_price[0], predicted_price[0])

    def test_predict_prices_v3(self):
        swap = connectors.UniswapV3('mainnet')

        # Taking out token0, injecting token1
        # predicted price should shift the price towards token0
        # current[t0] > predicted[t0]; current[t1] < predicted[t1]
        routerSwap = RouterSwap(
            token_in='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # token1
            token_in_amount=98000000000000000,
            token_out='0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39',  # token0
            token_out_amount=280291194084,
            router_address='0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
            swap_method='exactInputSingle',
            router_name='uniswapv302',
            dex_name='uniswapv3',
            fee="3000"
        )

        pair_address = swap.get_pair(routerSwap.token_in, routerSwap.token_out, fee=routerSwap.fee)

        current_price = swap.get_prices_sdk(pair_address)
        predicted_price = swap.predict_price(pair_address, routerSwap)

        self.assertGreater(current_price[0], predicted_price[0])
