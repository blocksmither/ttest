import json
import os

with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'v2pair-1.json')) as f:
    v2pairs = json.load(f)

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

for pair in v3pairs["data"]["pools"]:
    pair['dex'] = 'UniswapV'
    try:
        hashmap[pair["token0"]["id"]].append(pair)
    except:
        hashmap[pair["token0"]["id"]] = [pair]

    try:
        hashmap[pair["token1"]["id"]].append(pair)
    except:
        hashmap[pair["token1"]["id"]] = [pair]


with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json'), 'w') as f:
    json.dump(hashmap, f, indent=2)
