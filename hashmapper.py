import json
import os

import requests


def query_v2_pairs():
    all_pairs = {'data': {'pairs': []}}
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    for i in range(5):
        query = f"""
        query {{
            pairs(first: 1000, skip: {i * 1000}, orderBy: reserveETH, orderDirection: desc) {{
                id
                token0 {{
                    id
                    symbol
                    decimals
                }}
                token1 {{
                    id
                    symbol
                    decimals
                }}
            }}
        }}
        """

        payload = {"query": query}
        v2pairs = requests.post(url, json=payload).json()

        all_pairs['data']['pairs'] += v2pairs['data']['pairs']

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'v2pair-1.json'), 'w') as f:
        json.dump(all_pairs, f, indent=2)


def query_sushi_pairs():
    all_pairs = {'data': {'pairs': []}}
    url = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    for i in range(5):
        query = f"""
        query {{
            pairs(first: 1000, skip: {i * 1000}, orderBy: reserveETH, orderDirection: desc) {{
                id
                token0 {{
                    id
                    symbol
                    decimals
                }}
                token1 {{
                    id
                    symbol
                    decimals
                }}
            }}
        }}
        """

        payload = {"query": query}
        sushipairs = requests.post(url, json=payload).json()

        all_pairs['data']['pairs'] += sushipairs['data']['pairs']

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'sushipair-1.json'), 'w') as f:
        json.dump(all_pairs, f, indent=2)


def query_v3_pools():
    all_pairs = {'data': {'pools': []}}
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    for i in range(5):
        query = f"""
        query {{
        pools(first: 1000, skip: {i * 1000},orderBy: liquidity, orderDirection: desc) {{
            id
            token0 {{
            id
            symbol
            }}
            token1 {{
            id
            symbol
            }}
        }}
        }}
        """
        payload = {"query": query}
        v3pools = requests.post(url, json=payload).json()

        all_pairs['data']['pools'] += v3pools['data']['pools']

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'v3pool-1.json'), 'w') as f:
        json.dump(all_pairs, f, indent=2)


def build_hashmap_json():
    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'v2pair-1.json')) as f:
        v2pairs = json.load(f)

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'sushipair-1.json')) as f:
        sushipairs = json.load(f)

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'v3pool-1.json')) as f:
        v3pairs = json.load(f)

    hashmap = {}

    for pair in v2pairs["data"]["pairs"]:
        pair['dex'] = 'UniswapV2'
        try:
            hashmap[pair["token0"]["id"]].append(pair)
        except:
            hashmap[pair["token0"]["id"]] = [pair]

        try:
            hashmap[pair["token1"]["id"]].append(pair)
        except:
            hashmap[pair["token1"]["id"]] = [pair]

        pair_addresses = "".join(sorted([pair["token0"]["id"], pair["token1"]["id"]]))
        try:
            hashmap[pair_addresses].append(pair)
        except:
            hashmap[pair_addresses] = [pair]

    for pair in sushipairs["data"]["pairs"]:
        pair['dex'] = 'Sushiswap'
        try:
            hashmap[pair["token0"]["id"]].append(pair)
        except:
            hashmap[pair["token0"]["id"]] = [pair]

        try:
            hashmap[pair["token1"]["id"]].append(pair)
        except:
            hashmap[pair["token1"]["id"]] = [pair]

        pair_addresses = "".join(sorted([pair["token0"]["id"], pair["token1"]["id"]]))
        try:
            hashmap[pair_addresses].append(pair)
        except:
            hashmap[pair_addresses] = [pair]

    for pair in v3pairs["data"]["pools"]:
        pair['dex'] = 'UniswapV3'
        try:
            hashmap[pair["token0"]["id"]].append(pair)
        except:
            hashmap[pair["token0"]["id"]] = [pair]

        try:
            hashmap[pair["token1"]["id"]].append(pair)
        except:
            hashmap[pair["token1"]["id"]] = [pair]

        pair_addresses = "".join(sorted([pair["token0"]["id"], pair["token1"]["id"]]))
        try:
            hashmap[pair_addresses].append(pair)
        except:
            hashmap[pair_addresses] = [pair]

    with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json'), 'w') as f:
        json.dump(hashmap, f, indent=2)


if __name__ == "__main__":
    query_v2_pairs()
    query_v3_pools()
    query_sushi_pairs()

    build_hashmap_json()
