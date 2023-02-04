from connectors import connectors


def compare(pairs, connection_type='sdk', network='mainnet'):
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

    swap_args = {
        'inToken': pairs[0]['token0']['id'],
        'arbToken': pairs[0]['token1']['id'],
        'dexs': [data['min']['id'], data['max']['id']],
        'arb': data['max']['price'] / data['min']['price']
    }

    return swap_args
