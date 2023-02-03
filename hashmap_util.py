import json
import os

with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json')) as f:
    hashmap = json.load(f)


def find_pairs_given_token(token_address):
    try:
        results = hashmap[token_address.lower()]
    except:
        raise Exception('Token not in the hashmap')
    pair_ids = [result["id"] for result in results]
    return pair_ids


def find_pairs_given_pair(token1_address, token2_address):
    pair_addresses = "".join(sorted([token1_address.lower(), token2_address.lower()]))
    try:
        results = hashmap[pair_addresses]
    except:
        raise Exception('Token pair not in the hashmap')
    pair_ids = [result["id"] for result in results]
    return pair_ids
