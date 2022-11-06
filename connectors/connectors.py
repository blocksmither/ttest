from web3 import Web3
from decimal import Decimal
import requests
import json
import os
import math
import yaml

with open('config.yaml') as file:
    config = yaml.safe_load(file)


class BaseConnector():
    web3 = 'unset'
    network = 'unset'

    def get_prices(self, pair, network, connection='api'):
        self.web3 = Web3(Web3.HTTPProvider(config['networks'][network]['web3Provider']))
        self.network = network
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

    def get_prices_api(self, pair):
        address = config['networks'][self.network]['pairs']['sushiswap'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['sushiswap'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()

        price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12
        return price, 1 / price


class UniswapV2(BaseConnector):
    name = "UniswapV2"
    endpoint = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    def get_prices_api(self, pair):
        address = config['networks'][self.network]['pairs']['uniswapv2'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['uniswapv2'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()

        price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12
        return price, 1 / price


class UniswapV3(BaseConnector):
    name = "UniswapV3"
    endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    with open(os.path.join(os.path.dirname(__file__), "abi", "IUniswapV3Pool.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    def get_prices_api(self, pair):
        address = config['networks'][self.network]['pairs']['uniswapv3'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['uniswapv3'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        sqrtPriceX96 = Decimal(contract.functions.slot0().call()[0])

        price = math.pow(2, 192) / math.pow(sqrtPriceX96, 2) * math.pow(10, 12)
        return price, 1 / price
