import requests
import json


def query_v2_pairs():
    # Query the UniswapV2 API for the first 100 liquidity pool pairs
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    query = """
    query {
      pairs(first: 100) {
        id
        token0 {
          id
          symbol
        }
        token1 {
          id
          symbol
        }
      }
    }
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    v2pairs = requests.post(url, json=payload, headers=headers).json()
    
    with open('./pairpages/v2pair-1.json', 'w') as f:
        json.dump(v2pairs,f,indent=2)
    
def query_v3_pools():
    # Query the UniswapV2 API for the first 100 liquidity pool pairs
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    query = """
    query {
      pools(first: 100) {
        id
        token0 {
          id
          symbol
        }
        token1 {
          id
          symbol
        }
      }
    }
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    v3pools = requests.post(url, json=payload, headers=headers).json()
    
    with open('./pairpages/v3pool-1.json', 'w') as f:
        json.dump(v3pools,f,indent=2)

query_v2_pairs()
query_v3_pools()

