import json
import os

with open(os.path.join(os.path.dirname(__file__), 'pairpages', 'hashmap.json')) as f:
    hashmap = json.load(f)


def find_shared_token_pairs(token_address):
    results = hashmap[token_address]
    # Extract the pair IDs from the results
    pair_ids = [result["id"] for result in results]
    return pair_ids


pairs = find_shared_token_pairs('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')
print(len(pairs))
