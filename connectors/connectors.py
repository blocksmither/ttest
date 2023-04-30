import json
import os
from decimal import Decimal

import requests
import yaml
from connectors.sqrtpricemath import SqrtPriceMath
from swap import RouterSwap
from web3 import Web3

with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml')) as file:
    config = yaml.safe_load(file)


EMPTY_PAIR = '0x0000000000000000000000000000000000000000'


class BaseConnector():
    web3 = 'unset'
    network = 'unset'
    with open(os.path.join(os.path.dirname(__file__), '..', 'interfaces', 'erc20', 'abi.json'), 'r') as f:
        erc20_abi = f.read().rstrip()

    def __init__(self, network):
        self.network = network
        self.web3 = Web3(Web3.HTTPProvider(config['networks'][self.network]['web3Provider']))

    def get_prices(self, pair, connection='sdk'):
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

    def get_token0(self, pair_address):
        pair_contract = self.web3.eth.contract(
            address=Web3.toChecksumAddress(pair_address),
            abi=self.abi
        )
        token0 = pair_contract.functions.token0().call()

        return token0

    def get_token1(self, pair_address):
        pair_contract = self.web3.eth.contract(
            address=Web3.toChecksumAddress(pair_address),
            abi=self.abi
        )
        token1 = pair_contract.functions.token1().call()

        return token1

    def get_tokens(self, pair_address):
        return self.get_token0(pair_address), self.get_token1(pair_address)

    def get_token_decimals(self, address):
        address = Web3.toChecksumAddress(address)
        token_contract = self.web3.eth.contract(
            address=Web3.toChecksumAddress(address),
            abi=self.erc20_abi
        )
        decimals = token_contract.functions.decimals().call()

        return decimals

    def get_tokens_decimals(self, address):
        token0, token1 = self.get_tokens(address)
        return self.get_token_decimals(token0), self.get_token_decimals(token1)

    def get_token_symbol(self, address):
        address = Web3.toChecksumAddress(address)
        token_contract = self.web3.eth.contract(
            address=Web3.toChecksumAddress(address),
            abi=self.erc20_abi
        )
        symbol = token_contract.functions.symbol().call()

        return symbol

    def get_tokens_symbols(self, address):
        token0, token1 = self.get_tokens(address)
        return self.get_token_symbol(token0), self.get_token_symbol(token1)


class UniswapV2(BaseConnector):
    name = "UniswapV2"
    endpoint = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswapv2"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]
    with open(os.path.join(os.path.dirname(__file__), '..', 'interfaces', 'uniswapv2', 'factory.abi'), 'r') as f:
        factory_abi = f.read().rstrip()

    def get_pair_decimals(self, address):
        query = f"""query {{
          pair(id:"{address}") {{
            token0 {{
              decimals
            }}
            token1 {{
              decimals
            }}
          }}
        }}"""

        response = requests.post(self.endpoint, json={'query': query})
        response_json = response.json()

        try:
            return (
                response_json['data']['pair']['token0']['decimals'],
                response_json['data']['pair']['token1']['decimals'],
            )
        except:
            return self.get_tokens_decimals(address)

    def get_prices_api(self, address):
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
            reserve0
            reserve1
          }}
        }}"""

        response = requests.post(self.endpoint, json={'query': query})
        response_json = response.json()

        return (
            Decimal(response_json['data']['pair']['token0Price']),
            Decimal(response_json['data']['pair']['token1Price']),
            Decimal(response_json['data']['pair']['reserve0']),
            Decimal(response_json['data']['pair']['reserve1'])
        )

    def get_prices_sdk(self, pair):
        address = Web3.toChecksumAddress(pair)
        decimals = self.get_pair_decimals(pair)
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        _reserve0, _reserve1, _blockTimestampLast = contract.functions.getReserves().call()

        price = Decimal(_reserve0) / Decimal(_reserve1) * 10 ** (abs(int(decimals[0]) - int(decimals[1])))
        return price, 1 / price, Decimal(_reserve0) / (10 ** int(decimals[0])), Decimal(_reserve1) / (10 ** int(decimals[1]))

    def predict_price(self, pair, swap: RouterSwap):
        decimals = self.get_pair_decimals(pair)
        reserves = self.get_pair_reserves(pair)
        token0, token1 = self.get_tokens(pair)

        if token0.lower() == swap.token_in.lower():
            d_reserve0 = reserves['token0'] + swap.token_in_amount
            d_reserve1 = reserves['token1'] - swap.token_out_amount
        else:
            d_reserve0 = reserves['token0'] - swap.token_out_amount
            d_reserve1 = reserves['token1'] + swap.token_in_amount

        price = Decimal(d_reserve0) / Decimal(d_reserve1) * 10 ** (abs(int(decimals[0]) - int(decimals[1])))
        return price, 1 / price, Decimal(d_reserve0) / (10 ** int(decimals[0])), Decimal(d_reserve1) / (10 ** int(decimals[1]))

    def get_pair(self, token_in, token_out, **kwargs):
        factory_address = Web3.toChecksumAddress(config['networks'][self.network]['exchangeFactories'][self.name])

        factory_contract = self.web3.eth.contract(
            address=factory_address,
            abi=self.factory_abi
        )
        pair_address = factory_contract.functions.getPair(
            token_in,
            token_out
        ).call()
        return pair_address

    def get_pair_reserves(self, pair_address):
        pair_contract = self.web3.eth.contract(
            address=Web3.toChecksumAddress(pair_address),
            abi=self.abi
        )

        token0_reserve, token1_reserve, last_block_timestamp = pair_contract.functions.getReserves().call()

        return {"token0": int(token0_reserve), "token1": int(token1_reserve)}


class Sushiswap(UniswapV2):
    name = "Sushiswap"
    endpoint = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    with open(os.path.join(os.path.dirname(__file__), "abi", "UniswapV2Pair.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]
    with open(os.path.join(os.path.dirname(__file__), '..', 'interfaces', 'sushiswap', 'factory.abi'), 'r') as f:
        factory_abi = f.read().rstrip()


class UniswapV3(BaseConnector):
    name = "UniswapV3"
    endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    with open(os.path.join(os.path.dirname(__file__), "abi", "IUniswapV3Pool.json")) as f:
        info_json = json.load(f)
    abi = info_json["abi"]
    with open(os.path.join(os.path.dirname(__file__), '..', 'interfaces', 'uniswapv3', 'factory.abi'), 'r') as f:
        factory_abi = f.read().rstrip()

    def get_pair_decimals(self, address):
        try:
            query = f"""query {{
            pool(id:"{address}") {{
                token0 {{
                decimals
                }}
                token1 {{
                decimals
                }}
            }}
            }}"""

            response = requests.post(self.endpoint, json={'query': query})
            response_json = response.json()

            return (
                response_json['data']['pool']['token0']['decimals'],
                response_json['data']['pool']['token1']['decimals'],
            )
        except:
            return self.get_tokens_decimals(address)

    def get_prices_api(self, address):
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

        return (
            Decimal(response_json['data']['pool']['token0Price']),
            Decimal(response_json['data']['pool']['token1Price']),
            int(response_json['data']['pool']['feeTier']),
            int(response_json['data']['pool']['sqrtPrice']),
            int(response_json['data']['pool']['liquidity']),
        )

    def get_prices_sdk(self, pair):
        address = Web3.toChecksumAddress(pair)
        decimals = self.get_pair_decimals(pair)
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        fee = contract.functions.fee().call()
        slot0 = contract.functions.slot0().call()
        liquidity = contract.functions.liquidity().call()
        sqrtPriceX96 = Decimal(slot0[0])

        price = 2 ** 192 / sqrtPriceX96 ** 2 * 10 ** (abs(int(decimals[0]) - int(decimals[1])))
        return price, 1 / price, fee, slot0[0], liquidity

    def get_pair_fee(self, pair):
        address = Web3.toChecksumAddress(pair)
        contract = self.web3.eth.contract(address=address, abi=self.abi)
        fee = contract.functions.fee().call()
        return fee / (10 ** 6)

    def predict_price(self, pair, swap: RouterSwap):
        current_price = self.get_prices_sdk(pair)

        token0 = self.get_token0(pair)

        if token0.lower() == swap.token_in.lower():
            amount = swap.token_in_amount
            add = True
        else:
            amount = swap.token_out_amount
            add = False

        dprice = SqrtPriceMath.getNextSqrtPriceFromAmount0RoundingUp(
            int(current_price[3]),
            int(current_price[4]),
            amount,
            add
        )

        decimals = self.get_tokens_decimals(pair)
        dprice = 2 ** 192 / Decimal(dprice) ** 2 * 10 ** (abs(int(decimals[0]) - int(decimals[1])))

        return dprice, 1 / dprice

    def get_pair(self, token_in, token_out, fee=None):
        factory_address = Web3.toChecksumAddress(config['networks'][self.network]['exchangeFactories']['UniswapV3'])

        factory_contract = self.web3.eth.contract(
            address=factory_address,
            abi=self.factory_abi
        )
        pair_list = []
        if fee:
            fees = [int(fee)]
        else:
            fees = [100, 500, 3000, 10000]
        for pool_fee in fees:
            pair_address = factory_contract.functions.getPool(
                token_in,
                token_out,
                pool_fee
            ).call()
            if pair_address != EMPTY_PAIR:
                pair_list.append(pair_address)

        return pair_list[0]

    def get_pair_reserves(self, pair_address):
        # Dummy data to be homogenic with V2
        return {"token0": 1, "token1": 1}
