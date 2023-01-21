import argparse
import datetime
import json
import os
from web3 import Web3
from decimal import Decimal

import brownie
import websocket
import yaml
from connectors import connectors
from comparator import compare
from swap import parse_swap_tx_blocknative, get_v2_pair, get_v2_pair_reserves


def symbol_dec(symbol):
    dec = {
        "USDC": 6,
        "WETH": 18
    }
    return dec[symbol]


class MempoolReader():
    with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as file:
        config = yaml.safe_load(file)

    def __init__(self, pair, swap, network, threshold):
        self.pair = pair
        self.swap = swap
        self.network = network
        self.connector = eval(f"connectors.{swap}('{network}')")
        self.address1 = self.config['networks'][self.network]['exchangeRouters']['UniswapV2']
        self.address2 = self.config['networks'][self.network]['exchangeRouters']['UniswapV3']
        self.address3 = self.config['networks'][self.network]['exchangeRouters']['UniswapV302']
        self.address4 = self.config['networks'][self.network]['exchangeRouters']['Sushiswap']
        self.wsapp = websocket.WebSocketApp(
            "wss://api.blocknative.com/v0", on_open=self.on_open, on_message=self.on_message)
        self.solBotProject = brownie.project.load('./solidity')
        self.solBotProject.load_config()
        self.w3 = Web3(Web3.HTTPProvider(
            self.config['networks'][self.network]['web3Provider']))
        self.check_threshold = threshold

    @property
    def mempool_network(self):
        networks = {
            'mainnet': 'main',
            'goerli': 'goerli'
        }
        return networks[self.network]

    def on_message(self, wsapp, message):
        event = json.loads(message)
        try:
            swaps = parse_swap_tx_blocknative(event)
            for swap in swaps:
                print(swap)
                if swap.dex_name == 'uniswapv2' or swap.dex_name == 'uniswapv302' or swap.dex_name == 'sushiswap':
                    pair_address = get_v2_pair(
                        self.w3, swap.token_in, swap.token_out, swap.dex_name)
                    reserves = get_v2_pair_reserves(
                        self.w3, pair_address, swap.dex_name)
                    if (swap.token_in_amount / reserves['token0'] > self.check_threshold
                            or swap.token_out_amount / reserves['token1'] > self.check_threshold):
                        print(
                            "Possible Arbitrage opportunity swap amount is greater than treshold ", self.check_treshold)
                        try:
                            brownie.network.connect(network='mainnet-fork', launch_rpc=True)
                            solidityBot = self.solBotProject.Bot.deploy({'from': brownie.accounts[0]})
                            solidityBot.depositETH({'from': brownie.accounts[0], 'value': 10e18})
                            balances = solidityBot.getBalances()
                            print(balances)
                            # Call solidityBot.multiswap({'from': accounts[0])
                            swap_args = compare(network=self.network, return_swap_args=True)
                            solidityBot.multiSwap(
                                swap_args['WETH-USDC']['inToken'],
                                swap_args['WETH-USDC']['arbToken'],
                                1e18,
                                swap_args['WETH-USDC']['dexs'],
                                False,
                                {'from': brownie.accounts[0]}
                            )
                            balances = solidityBot.getBalances()
                            print(balances)
                            brownie.network.disconnect()
                        except Exception as e:
                            print('Failed to test bot on ganache fork')
                            print(e)

        except Exception as e:
            pass

    def on_open(self, wsapp):
        data = {
            "categoryCode": "initialize",
            "eventCode": "checkDappId",
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "cf6aaedd-10c1-45bd-8970-be4ee9544d9e",
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))

        data = {
            "categoryCode": "accountAddress",
            "eventCode": "watch",
            "account": {
                "address": self.address1,
            },
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "cf6aaedd-10c1-45bd-8970-be4ee9544d9e",
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))

        data = {
            "categoryCode": "accountAddress",
            "eventCode": "watch",
            "account": {
                "address": self.address2,
            },
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "cf6aaedd-10c1-45bd-8970-be4ee9544d9e",
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))

        data = {
            "categoryCode": "accountAddress",
            "eventCode": "watch",
            "account": {
                "address": self.address3,
            },
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "cf6aaedd-10c1-45bd-8970-be4ee9544d9e",
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))

        data = {
            "categoryCode": "accountAddress",
            "eventCode": "watch",
            "account": {
                "address": self.address4,
            },
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "cf6aaedd-10c1-45bd-8970-be4ee9544d9e",
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))
    def start(self):
        print("Reading mempool of:")
        print(f"Network: {self.network}")
        print(f"Address: {self.address1}")
        print(f"Address: {self.address2}")
        print(f"Address: {self.address3}")
        print(f"Address: {self.address4}")
        self.wsapp.run_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This script prints transactions in the mempool
    """)
    parser.add_argument("-s", '--swap', default='UniswapV3',
                        choices=["Sushiswap", "UniswapV2", "UniswapV3"], help="Swap")
    parser.add_argument("-n", "--network", default='mainnet',
                        choices=['mainnet', 'goerli'], help="Select mainnet or testnet network")
    parser.add_argument("-t", "--threshold", default=0.01,
                        help="Threshold amount for possible arbitrage, should typically be 0.01 or greater")

    args = parser.parse_args()
    SWAP = args.swap
    NETWORK = args.network.strip()
    THRESHOLD = float(args.threshold)

    reader = MempoolReader('USDC-WETH', SWAP, NETWORK, THRESHOLD)
    reader.start()
