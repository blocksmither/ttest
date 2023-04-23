import json
import os

with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json')) as f:
    hashmap = json.load(f)


ROUTER_2_DEX = {
    'uniswapv2': 'UniswapV2',
    'sushiswap': 'Sushiswap',
    'uniswapv3': 'UniswapV3',
    'uniswapv302': 'UniswapV3',
}


def find_pairs(token1_address, token2_address=None, dex=None, alt_dex=None, fee=None):
    if token2_address:
        pair_addresses = "".join(sorted([token1_address.lower(), token2_address.lower()]))
    else:
        pair_addresses = token1_address.lower()

    try:
        results = hashmap[pair_addresses]
    except:
        raise Exception('Token pair not in the hashmap')

    if dex:
        results = [result for result in results if result['dex'] == dex]
    elif alt_dex:
        results = [result for result in results if result['dex'] != alt_dex]

    if fee:
        results = [result for result in results if result['feeTier'] == fee]

    return results
