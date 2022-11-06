from connectors import connectors

import datetime
import argparse


def watcher(swap, network):
    swap = eval(f"connectors.{swap}()")
    price_api = swap.get_prices('USDC-WETH', network, connection='api')
    price_sdk = swap.get_prices('USDC-WETH', network, connection='sdk')

    current = {
        'api': price_api[0],
        'sdk': price_sdk[0]
    }

    print(datetime.datetime.now())
    print(swap.name)
    print(f"Current API: {current['api']}")
    print(f"Current SDK: {current['sdk']}")
    while True:
        shout = False
        price_api = swap.get_prices('USDC-WETH', network, connection='api')
        if current['api'] != price_api[0]:
            current['api'] = price_api[0]
            shout = True
        price_sdk = swap.get_prices('USDC-WETH', network, connection='sdk')
        if current['sdk'] != price_sdk[0]:
            current['sdk'] = price_sdk[0]
            shout = True
        if shout:
            print(datetime.datetime.now())
            print(swap.name)
            print(f"Current API: {current['api']}")
            print(f"Current SDK: {current['sdk']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This script keeps track of prices and prints when there is a change.
    """)
    parser.add_argument("-s", '--swap', default='UniswapV3', choices=["Sushiswap", "UniswapV2", "UniswapV3"], help="Swap")
    parser.add_argument("-n", "--network", default='mainnet', choices=['mainnet', 'mainnet-fork', 'goerli'], help="Select mainnet or testnet network")

    args = parser.parse_args()
    SWAP = args.swap
    NETWORK = args.network.strip()

    watcher(SWAP, NETWORK)
