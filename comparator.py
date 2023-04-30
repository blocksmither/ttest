from connectors import connectors
from swap import Pair


def compare(pairs, connection_type='sdk', network='mainnet', predicted: Pair = None):
    if len(pairs) < 2:
        raise Exception("Can't compare 1 or less options")
    data = {}
    swaps = {
        'UniswapV2': connectors.UniswapV2(network),
        'UniswapV3': connectors.UniswapV3(network),
        'Sushiswap': connectors.Sushiswap(network)
    }

    rates = []
    future_price = isinstance(predicted, Pair)
    for pair in pairs:
        if future_price and predicted.address == pair['id']:
            prices = [predicted.predicted_price]
        else:
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
    r_swap_args = {
        'inToken': pairs[0]['token1']['id'],
        'arbToken': pairs[0]['token0']['id'],
        'dexs': [data['max']['dex_fee'], data['min']['dex_fee']],
        'min': data['max'],
        'max': data['min'],
        'arb': data['max']['price'] / data['min']['price']
    }
    if swap_args['arbToken'].lower() == '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'.lower():
        return r_swap_args

    return swap_args
