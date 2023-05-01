import json
import os

from connectors import connectors
from db.db import Database

with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json')) as f:
    hashmap = json.load(f)


ROUTER_2_DEX = {
    'uniswapv2': 'UniswapV2',
    'sushiswap': 'Sushiswap',
    'uniswapv3': 'UniswapV3',
    'uniswapv302': 'UniswapV3',
}

DB = Database()


def store(results):
    for result in results:
        DB.update(
            result["id"],
            result["dex"],
            result["token0"]["id"],
            result["token0"]["symbol"],
            result["token0"]["decimals"],
            result["token1"]["id"],
            result["token1"]["symbol"],
            result["token1"]["decimals"],
            pair_fee=result.get('feeTier')
        )


def update_hash():
    stored_pairs = DB.get_all()
    for pair in stored_pairs:
        result = {
            "id": pair[0].lower(),
            "token0": {
                "id": pair[3].lower(),
                "symbol": pair[4],
                "decimals": pair[5]
            },
            "token1": {
                "id": pair[6].lower(),
                "symbol": pair[7],
                "decimals": pair[8]
            },
            "dex": pair[2]
        }
        if pair[1] != 'None':
            result["feeTier"] = pair[1]
        try:
            hashmap[result["token0"]["id"]] = list(set(hashmap[result["token0"]["id"]]).add(result))
        except:
            hashmap[result["token0"]["id"]] = [result]
        try:
            hashmap[result["token1"]["id"]] = list(set(hashmap[result["token1"]["id"]]).add(result))
        except:
            hashmap[result["token1"]["id"]] = [result]
        pair_addresses = "".join(sorted([result["token0"]["id"], result["token1"]["id"]]))
        try:
            hashmap[pair_addresses] = list(set(hashmap[pair_addresses]).add(result))
        except:
            hashmap[pair_addresses] = [result]

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json'), 'w') as f:
        json.dump(hashmap, f, indent=2)

    DB.drop_database()
    DB.create_database()


def find_pairs(token1_address, token2_address=None, dex=None, alt_dex=None, fee=None):
    if token2_address:
        pair_addresses = "".join(sorted([token1_address.lower(), token2_address.lower()]))
    else:
        pair_addresses = token1_address.lower()

    try:
        results = hashmap[pair_addresses]
        if len(results) <= 1:
            results = get_alt_pairs(token1_address, token2_address)
            store(results)
    except:
        # Token pair not in the hashmap
        results = get_alt_pairs(token1_address, token2_address)
        store(results)

    if dex:
        results = [result for result in results if result['dex'] == dex]
    elif alt_dex:
        results = [result for result in results if result['dex'] != alt_dex]

    if fee:
        results = [result for result in results if result['feeTier'] == fee]

    return results


def get_alt_pairs(token1_address, token2_address):
    dex_list = [
        'uniswapv3',
        'uniswapv2',
        'sushiswap'
    ]

    EMPTY_PAIR = '0x0000000000000000000000000000000000000000'

    symbols = False
    decimals = False
    fee = False
    pairs = []
    for dex in dex_list:
        if dex == 'uniswapv3':
            for pool_fee in [100, 500, 3000, 10000]:
                try:
                    pair_address = connectors.UniswapV3('mainnet').get_pair(
                        token1_address,
                        token2_address,
                        fee=pool_fee
                    )
                    if not decimals:
                        decimals = connectors.UniswapV3('mainnet').get_tokens_decimals(pair_address)
                    if not symbols:
                        symbols = connectors.UniswapV3('mainnet').get_tokens_symbols(pair_address)
                    fee = str(int(connectors.UniswapV3('mainnet').get_pair_fee(pair_address) * (10 ** 6)))
                    if pair_address != EMPTY_PAIR:
                        tokens = connectors.UniswapV3('mainnet').get_tokens(pair_address)
                        pairs.append({
                            "id": pair_address,
                            "feeTier": fee,
                            "token0": {
                                "id": tokens[0],
                                "symbol": symbols[0],
                                "decimals": decimals[0],
                            },
                            "token1": {
                                "id": tokens[1],
                                "symbol": symbols[1],
                                "decimals": decimals[1]
                            },
                            "dex": "UniswapV3"
                        })
                except:
                    pass
        elif dex == 'uniswapv2':
            try:
                pair_address = connectors.UniswapV2('mainnet').get_pair(
                    token1_address,
                    token2_address
                )
                if not decimals:
                    decimals = connectors.UniswapV2('mainnet').get_tokens_decimals(pair_address)
                if not symbols:
                    symbols = connectors.UniswapV2('mainnet').get_tokens_symbols(pair_address)
                if pair_address != EMPTY_PAIR:
                    tokens = connectors.UniswapV2('mainnet').get_tokens(pair_address)
                    pairs.append({
                        "id": pair_address,
                        "token0": {
                            "id": tokens[0],
                            "symbol": symbols[0],
                            "decimals": decimals[0]
                        },
                        "token1": {
                            "id": tokens[1],
                            "symbol": symbols[1],
                            "decimals": decimals[1]
                        },
                        "dex": "UniswapV2"
                    })
            except:
                pass
        elif dex == 'sushiswap':
            try:
                pair_address = connectors.Sushiswap('mainnet').get_pair(
                    token1_address,
                    token2_address
                )
                if not decimals:
                    decimals = connectors.Sushiswap('mainnet').get_tokens_decimals(pair_address)
                if not symbols:
                    symbols = connectors.Sushiswap('mainnet').get_tokens_symbols(pair_address)

                if pair_address != EMPTY_PAIR:
                    tokens = connectors.Sushiswap('mainnet').get_tokens(pair_address)
                    pairs.append({
                        "id": pair_address,
                        "token0": {
                            "id": tokens[0],
                            "symbol": symbols[0],
                            "decimals": decimals[0]
                        },
                        "token1": {
                            "id": tokens[1],
                            "symbol": symbols[1],
                            "decimals": decimals[1]
                        },
                        "dex": "Sushiswap"
                    })
            except:
                pass

    return pairs
