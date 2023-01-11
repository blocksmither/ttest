import argparse
import datetime
import os
from distutils.util import strtobool

import yaml
from connectors import connectors


def reverse_pair(pair):
    tokens = 'USDC-WETH'.split("-")
    tokens.reverse()
    return "-".join(tokens)


pairs = [
    'USDC-WETH'
]

rates = {}

with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as file:
    config = yaml.safe_load(file)


def compare(connection_type='sdk', network='mainnet', return_swap_args=False):
    swaps = [
        connectors.UniswapV2(network),
        connectors.UniswapV3(network),
        connectors.Sushiswap(network)
    ]

    for pair in pairs:
        rates[pair] = {'prices': []}
        rates[reverse_pair(pair)] = {'prices': []}
        for swap in swaps:
            prices = swap.get_prices(pair, connection=connection_type)

            rates[pair]['prices'].append({'swap': swap.name, 'price': float(prices[0])})
            rates[reverse_pair(pair)]['prices'].append({'swap': swap.name, 'price': float(prices[1])})

    swap_args = {}
    for pair, data in rates.items():
        data['max'] = max(data['prices'], key=lambda x: x['price'])
        data['min'] = min(data['prices'], key=lambda x: x['price'])

        if return_swap_args:
            swap_args[pair] = {
                'inToken': config['networks'][network]['tokens'][pair.split("-")[0]],
                'arbToken': config['networks'][network]['tokens'][pair.split("-")[1]],
                'dexs': [data['min']['swap'], data['max']['swap']],
                'arb': data['max']['price'] / data['min']['price']
            }
        else:
            print(pair)
            print(f"MAX: {data['max']['swap']}")
            print(f"MIN: {data['min']['swap']}")
            print(f"ARB: {data['max']['price'] / data['min']['price']}")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    if return_swap_args:
        return swap_args


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This script compares prices.
    """)
    parser.add_argument("-c", '--connection', default='sdk', choices=["api", "sdk"], help="Connection type")
    parser.add_argument("-r", "--rates", default=False, choices=[True, False], type=strtobool, help="Show all rates at the end")
    parser.add_argument("-n", "--network", default='mainnet', choices=['mainnet', 'mainnet-fork', 'goerli'], help="Select mainnet or testnet network")

    args = parser.parse_args()
    TYPE = args.connection
    RATES = args.rates
    NETWORK = args.network.strip()

    if NETWORK in ['mainnet', 'mainnet-fork']:
        print(datetime.datetime.now())
        compare(connection_type=TYPE, network=NETWORK)
        if RATES:
            print(rates)
    else:
        raise Exception("Unsupported network provided! network=", NETWORK)
