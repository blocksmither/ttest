from connectors import connectors


def compare(pairs, connection_type='sdk', network='mainnet'):
    if len(pairs) < 2:
        raise Exception("Can't compare 1 or less options")
    data = {}
    swaps = {
        'UniswapV2': connectors.UniswapV2(network),
        'UniswapV3': connectors.UniswapV3(network),
        'Sushiswap': connectors.Sushiswap(network)
    }

    rates = []
    for pair in pairs:
        prices = swaps[pair['dex']].get_prices(pair['id'], connection=connection_type)

        if pair['dex'] == 'UniswapV3':
            dex_fee = f"UniswapV3-{pair['feeTier']}"
        else:
            dex_fee = pair['dex']
        rates.append(
            {
                'swap': pair['dex'],
                'price': prices[0],
                'id': pair['id'],
                'fee': pair.get('feeTier', '3000'),
                'dex_fee': dex_fee
            }
        )

    data['max'] = max(rates, key=lambda x: x['price'])
    data['min'] = min(rates, key=lambda x: x['price'])

    swap_args = {
        'inToken': pairs[0]['token0']['id'],
        'arbToken': pairs[0]['token1']['id'],
        'dexs': [data['min']['dex_fee'], data['max']['dex_fee']],
        'min': data['min'],
        'max': data['max'],
        'arb': data['max']['price'] / data['min']['price']
    }

    return swap_args
