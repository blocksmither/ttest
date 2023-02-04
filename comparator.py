import os

import yaml
from connectors import connectors

with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as file:
    config = yaml.safe_load(file)


def compare(pairs, connection_type='sdk', network='mainnet', return_swap_args=False):
    data = {}
    swaps = {
        'UniswapV2': connectors.UniswapV2(network),
        'UniswapV3': connectors.UniswapV3(network),
        'Sushiswap': connectors.Sushiswap(network)
    }

    rates = []
    for pair in pairs:
        prices = swaps[pair['dex']].get_prices(pair['id'], connection=connection_type)

        rates.append({'swap': pair['dex'], 'price': prices[0], 'id': pair['id'], 'fee': pair.get('feeTier', '3000')})

    data['max'] = max(rates, key=lambda x: x['price'])
    data['min'] = min(rates, key=lambda x: x['price'])

    if return_swap_args:
        swap_args = {
            'inToken': pairs[0]['token0']['id'],
            'arbToken': pairs[0]['token1']['id'],
            'dexs': [data['min']['id'], data['max']['id']],
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
