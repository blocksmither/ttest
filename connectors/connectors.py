from web3 import Web3
import requests
import json
import os
import math

web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/9165d99361774eb39d895e8623049a66'))


class BaseConnector():
    def get_prices(self, pair, connection='api'):
        if connection == "api":
            return self.get_prices_api(pair)
        elif connection == "sdk":
            return self.get_prices_sdk(pair)

    def get_prices_api(self, pair):
        # placeholder to be replaced by specific connector
        pass

    def get_prices_sdk(self, pair):
        # placeholder to be replaced by specific connector
        pass


class Sushiswap(BaseConnector):
    name = "Sushiswap"
    endpoint = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]


    PAIRMAP = {
        "USDC-WETH": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0"
    }

    def get_prices_api(self, pair):
        address = self.PAIRMAP[f"{pair}"]
        query = f"""query {{
          pair(id:"{address}") {{
            token0 {{
              symbol
              id
              decimals
            }}
            token1 {{
              symbol
              id
              decimals
            }}
            token0Price
            token1Price
          }}
        }}"""

        response = requests.post(self.endpoint, json={'query': query})
        response_json = response.json()

        return response_json['data']['pair']['token0Price'], response_json['data']['pair']['token1Price']

    def get_prices_sdk(self, pair):
        address = Web3.toChecksumAddress(self.PAIRMAP[f"{pair}"])
        contract = web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()

        price = _reserve0 / _reserve1 * math.pow(10, 12)
        return price, 1 / price


class UniswapV2(BaseConnector):
    name = "UniswapV2"
    endpoint = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    PAIRMAP = {
        "USDC-WETH": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
    }

    def get_prices_api(self, pair):
        address = self.PAIRMAP[f"{pair}"]
        query = f"""query {{
          pair(id:"{address}") {{
            token0 {{
              symbol
              id
              decimals
            }}
            token1 {{
              symbol
              id
              decimals
            }}
            token0Price
            token1Price
          }}
        }}"""

        response = requests.post(self.endpoint, json={'query': query})
        response_json = response.json()

        return response_json['data']['pair']['token0Price'], response_json['data']['pair']['token1Price']

    def get_prices_sdk(self, pair):
        address = Web3.toChecksumAddress(self.PAIRMAP[f"{pair}"])
        contract = web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()

        price = _reserve0 / _reserve1 * math.pow(10, 12)
        return price, 1 / price


class UniswapV3(BaseConnector):
    name = "UniswapV3"
    endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    with open(os.path.join(os.path.dirname(__file__), "abi", "IUniswapV3Pool.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    PAIRMAP = {
        "USDC-WETH": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    }

    def get_prices_api(self, pair):
        address = self.PAIRMAP[f"{pair}"]
        query = f"""query {{
          pool(id:"{address}") {{
            tick
            token0 {{
              symbol
              id
              decimals
            }}
            token1 {{
              symbol
              id
              decimals
            }}
            feeTier
            sqrtPrice
            token0Price
            token1Price
            liquidity
          }}
        }}"""

        response = requests.post(self.endpoint, json={'query': query})
        response_json = response.json()

        return response_json['data']['pool']['token0Price'], response_json['data']['pool']['token1Price']

    def get_prices_sdk(self, pair):
        address = Web3.toChecksumAddress(self.PAIRMAP[f"{pair}"])
        contract = web3.eth.contract(address=address, abi=self.abi)
        sqrtPriceX96 = contract.functions.slot0().call()[0]

        price = math.pow(2, 192) / math.pow(sqrtPriceX96, 2) * math.pow(10, 12)
        return price, 1 / price

