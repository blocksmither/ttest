from connectors import connectors

import datetime
import argparse
from distutils.util import strtobool


def reverse_pair(pair):
    tokens = 'USDC-WETH'.split("-")
    tokens.reverse()
    return "-".join(tokens)


swaps = [
    connectors.UniswapV2(),
    connectors.UniswapV3(),
    connectors.Sushiswap()
]

pairs = [
    'USDC-WETH'
]

rates = {}


def compare(connection_type='api', network='mainnet'):
    for pair in pairs:
        rates[pair] = {'prices': []}
        rates[reverse_pair(pair)] = {'prices': []}
        for swap in swaps:
            prices = swap.get_prices(pair, network, connection=connection_type)

            rates[pair]['prices'].append({'swap': swap.name, 'price': float(prices[0])})
            rates[reverse_pair(pair)]['prices'].append({'swap': swap.name, 'price': float(prices[1])})

    for pair, data in rates.items():
        data['max'] = max(data['prices'], key=lambda x: x['price'])
        data['min'] = min(data['prices'], key=lambda x: x['price'])

        print(pair)
        print(f"MAX: {data['max']['swap']}")
        print(f"MIN: {data['min']['swap']}")
        print(f"ARB: {data['max']['price'] / data['min']['price']}")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This script compares prices.
    """)
    parser.add_argument("-c", '--connection', default='api', choices=["api", "sdk"], help="Connection type")
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
