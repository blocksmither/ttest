import argparse
import datetime
import json
import os

import brownie
import hashmap_util as hutil
import websocket
import yaml
from connectors import connectors
from swap import (Pair, UnparsableSwapMethodException,
                  UnparsableTransactionException, get_alt_pairs,
                  parse_swap_tx_blocknative)
from web3 import Web3

from comparator import compare


def symbol_dec(symbol):
    dec = {
        "USDC": 6,
        "WETH": 18
    }
    return dec[symbol]


class MempoolReader():
    with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as file:
        config = yaml.safe_load(file)

    def __init__(self, network, threshold, test):
        self.network = network
        self.connectors = {
            'UniswapV2': connectors.UniswapV2(network),
            'UniswapV3': connectors.UniswapV3(network),
            'Sushiswap': connectors.Sushiswap(network)
        }
        self.address1 = self.config['networks'][self.network]['exchangeRouters']['UniswapV2']
        self.address2 = self.config['networks'][self.network]['exchangeRouters']['UniswapV3']
        self.address3 = self.config['networks'][self.network]['exchangeRouters']['UniswapV302']
        self.address4 = self.config['networks'][self.network]['exchangeRouters']['Sushiswap']
        self.wsapp = websocket.WebSocketApp(
            "wss://api.blocknative.com/v0", on_open=self.on_open, on_message=self.on_message)
        self.solBotProject = brownie.project.load(os.path.join(os.path.dirname(__file__), 'solidity'))
        self.solBotProject.load_config()
        self.w3 = Web3(Web3.HTTPProvider(
            self.config['networks'][self.network]['web3Provider']))
        self.check_threshold = threshold
        self.test_mode = test

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
                if swap.router_name in ['uniswapv2', 'uniswapv302', 'sushiswap']:
                    try:
                        pair_address = hutil.find_pairs(
                            swap.token_in,
                            swap.token_out,
                            dex=hutil.ROUTER_2_DEX[swap.router_name]
                        )[0]['id']
                    except:
                        # not in hashmap
                        pair_address = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_pair(
                            swap.token_in,
                            swap.token_out
                        )
                    reserves = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_pair_reserves(
                        pair_address
                    )
                    pair_token0 = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_token0(
                        pair_address
                    )
                    if swap.dex_name == 'uniswapv2':
                        pair_factory = self.config['networks']['mainnet']['exchangeFactories']['UniswapV2']
                        pair_fee = 0.003
                    elif swap.dex_name == 'uniswapv3':
                        pair_factory = self.config['networks']['mainnet']['exchangeFactories']['UniswapV3']
                    elif swap.dex_name == 'sushiswap':
                        pair_factory = self.config['networks']['mainnet']['exchangeFactories']['Sushiswap']
                        pair_fee = 0.003

                    if swap.token_in == pair_token0:
                        in_ratio = swap.token_in_amount / reserves['token0']
                        out_ratio = swap.token_out_amount / reserves['token1']
                        pair_token1 = swap.token_out
                    else:
                        in_ratio = swap.token_in_amount / reserves['token1']
                        out_ratio = swap.token_out_amount / reserves['token0']
                        pair_token1 = swap.token_in

                    print("in ratio", in_ratio)
                    print("out ratio", out_ratio)

                    affected_pair = Pair(
                        tokens=[pair_token0, pair_token1],
                        reserves=[reserves['token0'], reserves['token1']],
                        factory=pair_factory,
                        address=pair_address,
                        fee=pair_fee,
                        dex_name=swap.dex_name
                    )
                    print("Affected Pair: ", affected_pair)

                    if in_ratio > self.check_threshold or \
                            out_ratio > self.check_threshold:
                        print(
                            "Possible Arbitrage opportunity! Swap amount for txid ",
                            event['event']['transaction']['hash'],
                            " is greater than threshold ", self.check_threshold)

                        # print("getting alt pairs")
                        # alt_pairs = get_alt_pairs(self.w3, swap.token_in, swap.token_out, swap.dex_name)
                        # print(alt_pairs)

                        alt_pairs = hutil.find_pairs(pair_token0, pair_token1)

                        if self.test_mode:
                            try:
                                brownie.network.connect(network='mainnet-fork', launch_rpc=True)
                                solidityBot = self.solBotProject.Bot.deploy({'from': brownie.accounts[0]})
                                solidityBot.depositETH({'from': brownie.accounts[0], 'value': 10e18})
                                before_balances = solidityBot.getBalances()
                                # Call solidityBot.multiswap({'from': accounts[0])
                                swap_args = compare(alt_pairs, network=self.network)
                                solidityBot.multiSwap(
                                    swap_args['inToken'],
                                    swap_args['arbToken'],
                                    1e18,
                                    swap_args['dexs'],
                                    False,
                                    {'from': brownie.accounts[0]}
                                )
                                balances = solidityBot.getBalances()
                                print("balances before ", before_balances)
                                print("balances after ", balances)
                                brownie.network.disconnect()
                            except Exception as e:
                                print('Failed to test bot on ganache fork')
                                print(e)

        except (UnparsableTransactionException, UnparsableSwapMethodException):
            pass
        except KeyError:
            pass
        except Exception:
            pass

    def on_open(self, wsapp):
        data = {
            "categoryCode": "initialize",
            "eventCode": "checkDappId",
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": "139d298b-b21a-487e-be04-b06aa127155b",
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
            "dappId": "139d298b-b21a-487e-be04-b06aa127155b",
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
            "dappId": "139d298b-b21a-487e-be04-b06aa127155b",
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
            "dappId": "139d298b-b21a-487e-be04-b06aa127155b",
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
            "dappId": "139d298b-b21a-487e-be04-b06aa127155b",
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
    parser.add_argument("-n", "--network", default='mainnet',
                        choices=['mainnet', 'goerli'], help="Select mainnet or testnet network")
    parser.add_argument("-d", "--threshold", default=0.01,
                        help="Threshold amount for possible arbitrage, should typically be 0.01 or greater")
    parser.add_argument("-t", "--test", action="store_true", default=False,
                        help="Spin mainnet fork on ganache and test a swap on opportunities")

    args = parser.parse_args()
    NETWORK = args.network.strip()
    THRESHOLD = float(args.threshold)
    TEST_MODE_FLAG = args.test

    reader = MempoolReader(NETWORK, THRESHOLD, TEST_MODE_FLAG)
    reader.start()
