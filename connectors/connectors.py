from db.db import Database

from web3 import Web3
from decimal import Decimal
import requests
import json
import os
import yaml
import datetime

with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml')) as file:
    config = yaml.safe_load(file)


db = Database()


class BaseConnector():
    web3 = 'unset'
    network = 'unset'

    def __init__(self, network):
        self.network = network

    def get_prices(self, pair, connection='sdk'):
        self.web3 = Web3(Web3.HTTPProvider(config['networks'][self.network]['web3Provider']))
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
        address = config['networks'][self.network]['pairs']['Sushiswap'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['Sushiswap'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()
        db.update(address, reserves0=_reserve0, reserves1=_reserve1)
        price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12
        return price, 1 / price

    def predict_price(self, pair, deltas):
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['Sushiswap'][pair])
        current_price = db.get(address)
        if current_price is None:
            print("Not current price available. Run watcher separetly to be able to predict.")
        else:
            print(current_price)
            now = datetime.datetime.now()
            tdelta = now - current_price[1]
            if tdelta.total_seconds() > 1:
                print("Last price saved is too old to make a prediction")
            else:
                memdeltas = {}
                for nbc in deltas:
                    if nbc['address'].lower() == address.lower():
                        for bc in nbc['balanceChanges']:
                            memdeltas[bc['asset']['symbol']] = bc['delta']

                _reserve0 = current_price[2]
                _reserve1 = current_price[3]
                price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12

                d_reserve0 = int(current_price[2]) + int(memdeltas[pair.split("-")[0]])
                d_reserve1 = int(current_price[3]) + int(memdeltas[pair.split("-")[1]])

                dprice = Decimal(d_reserve0) / Decimal(d_reserve1) * 10 ** 12

                print(f"Current price: {price}")
                print(f"Predicted price: {dprice}")


class UniswapV2(BaseConnector):
    name = "UniswapV2"
    endpoint = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    def get_prices_api(self, pair):
        address = config['networks'][self.network]['pairs']['UniswapV2'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['UniswapV2'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()
        db.update(address, reserves0=_reserve0, reserves1=_reserve1)
        price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12
        return price, 1 / price, _reserve0, _reserve1

    def predict_price(self, pair, deltas):
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['UniswapV2'][pair])
        current_price = db.get(address)
        if current_price is None:
            print("Not current price available. Run watcher separetly to be able to predict.")
        else:
            print(current_price)
            now = datetime.datetime.now()
            tdelta = now - current_price[1]
            if tdelta.total_seconds() > 1:
                print("Last price saved is too old to make a prediction")
            else:
                memdeltas = {}
                for nbc in deltas:
                    if nbc['address'].lower() == address.lower():
                        for bc in nbc['balanceChanges']:
                            memdeltas[bc['asset']['symbol']] = bc['delta']

                _reserve0 = current_price[2]
                _reserve1 = current_price[3]
                price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** 12

                d_reserve0 = int(current_price[2]) + int(memdeltas[pair.split("-")[0]])
                d_reserve1 = int(current_price[3]) + int(memdeltas[pair.split("-")[1]])

                dprice = Decimal(d_reserve0) / Decimal(d_reserve1) * 10 ** 12

                print(f"Current price: {price}")
                print(f"Predicted price: {dprice}")


class UniswapV3(BaseConnector):
    name = "UniswapV3"
    endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    with open(os.path.join(os.path.dirname(__file__), "abi", "IUniswapV3Pool.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]

    def get_prices_api(self, pair):
        address = config['networks'][self.network]['pairs']['UniswapV3'][pair]
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
        address = Web3.toChecksumAddress(config['networks'][self.network]['pairs']['UniswapV3'][pair])
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        sqrtPriceX96 = Decimal(contract.functions.slot0().call()[0])
        db.update(address, sqrtprice=sqrtPriceX96)
        price = 2 ** 192 / sqrtPriceX96 ** 2 * 10 ** 12
        return price, 1 / price

    def predict_price(self, pair):
        print("Not yet supported")
