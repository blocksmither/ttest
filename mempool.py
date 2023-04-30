import argparse
import datetime
import json
import logging
import os

import brownie
import hashmap_util as hutil
import websocket
import yaml
from connectors import connectors
from swap import (Pair, UnparsableSwapMethodException,
                  UnparsableTransactionException, parse_swap_tx_blocknative)
from web3 import Web3

from comparator import compare


logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s")


def symbol_dec(symbol):
    dec = {
        "USDC": 6,
        "WETH": 18
    }
    return dec[symbol]


class MempoolReader():
    with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as file:
        config = yaml.safe_load(file)

    def __init__(self, network, threshold=0.01, test=False, save=False, dapp_id='pro'):
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
        self.save_events = save
        self.dapp_id = dapp_id

    @property
    def mempool_network(self):
        networks = {
            'mainnet': 'main',
            'goerli': 'goerli'
        }
        return networks[self.network]

    @property
    def dappid(self):
        ids = {
            'pro': "139d298b-b21a-487e-be04-b06aa127155b",
            'free': "cf6aaedd-10c1-45bd-8970-be4ee9544d9e"
        }
        return ids[self.dapp_id]

    def save_event(self, event):
        try:
            if self.save_events:
                if not os.path.exists(os.path.join(os.path.dirname(__file__), 'downloads')):
                    os.makedirs(os.path.join(os.path.dirname(__file__), 'downloads'))
                with open(
                        os.path.join(
                            os.path.dirname(__file__),
                            'downloads',
                            f"{event['timeStamp'].replace(':', '.')}-{event['event']['transaction']['hash']}.json"
                        ),
                        'w'
                ) as f:
                    json.dump(event, f, indent=2)
        except:
            pass

    def on_message(self, wsapp, message):
        event = json.loads(message)
        self.save_event(event)
        try:
            swaps = parse_swap_tx_blocknative(event)
            for swap in swaps:
                try:
                    pair_address = hutil.find_pairs(
                        swap.token_in,
                        swap.token_out,
                        dex=hutil.ROUTER_2_DEX[swap.router_name],
                        fee=swap.fee
                    )[0]['id']
                except:
                    # not in hashmap
                    pair_address = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_pair(
                        swap.token_in,
                        swap.token_out,
                        fee=swap.fee
                    )
                reserves = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_pair_reserves(
                    pair_address
                )
                pair_token0, pair_token1 = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_tokens(
                    pair_address
                )
                if swap.dex_name == 'uniswapv2':
                    pair_factory = self.config['networks']['mainnet']['exchangeFactories']['UniswapV2']
                    pair_fee = 0.003
                elif swap.dex_name == 'uniswapv3':
                    pair_factory = self.config['networks']['mainnet']['exchangeFactories']['UniswapV3']
                    pair_fee = int(swap.fee) / (10 ** 6)
                elif swap.dex_name == 'sushiswap':
                    pair_factory = self.config['networks']['mainnet']['exchangeFactories']['Sushiswap']
                    pair_fee = 0.003

                current_price = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].get_prices_sdk(pair_address)
                predicted_price = self.connectors[hutil.ROUTER_2_DEX[swap.router_name]].predict_price(pair_address, swap)

                percent_change = abs((predicted_price[0] - current_price[0]) / current_price[0])

                affected_pair = Pair(
                    tokens=[pair_token0, pair_token1],
                    reserves=[reserves['token0'], reserves['token1']],
                    factory=pair_factory,
                    address=pair_address,
                    fee=pair_fee,
                    dex_name=swap.dex_name,
                    predicted_price=predicted_price[0]
                )

                if percent_change > self.check_threshold:
                    logging.info(
                        f"Possible Arbitrage opportunity! Swap amount for txid {event['event']['transaction']['hash']} is greater than threshold {self.check_threshold}"
                    )
                    logging.info(f"Percent price change: {round(percent_change, 2)}%")
                    logging.info(f"Affected Pair: {affected_pair}")
                    alt_pairs = hutil.find_pairs(pair_token0, pair_token1)
                    if self.test_mode:
                        try:
                            swap_args = compare(alt_pairs, network=self.network, predicted=affected_pair)
                            logging.info(f"Swap args: {swap_args}")
                            brownie.network.connect(network='mainnet-fork', launch_rpc=True)
                            solidityBot = self.solBotProject.Bot.deploy({'from': brownie.accounts[0]})
                            solidityBot.depositETH({'from': brownie.accounts[0], 'value': 10e18})
                            before_balances = solidityBot.getBalances()

                            solidityBot.multiSwap(
                                swap_args['inToken'],
                                swap_args['arbToken'],
                                1e5,
                                swap_args['dexs'],
                                False,
                                {'from': brownie.accounts[0]}
                            )
                            balances = solidityBot.getBalances()
                            logging.info(f"Balances before: {before_balances[0]}")
                            logging.info(f"Balances after: {balances[0]}")
                            logging.info(f"Balances delta: {balances[0] - before_balances[0]}")
                            brownie.network.disconnect()
                        except Exception as e:
                            logging.info('Failed to test bot on ganache fork')
                            logging.info(e)
                            if brownie.network.is_connected():
                                brownie.network.disconnect()

        except (UnparsableTransactionException, UnparsableSwapMethodException) as e:
            logging.debug(1, e)
        except KeyError as e:
            logging.debug(2, e)
        except Exception as e:
            logging.debug(3, e)

    def on_open(self, wsapp):
        data = {
            "categoryCode": "initialize",
            "eventCode": "checkDappId",
            "timeStamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "dappId": self.dappid,
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
            "dappId": self.dappid,
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
            "dappId": self.dappid,
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
            "dappId": self.dappid,
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
            "dappId": self.dappid,
            "version": "1",
            "blockchain": {
                "system": "ethereum",
                "network": self.mempool_network
            }
        }
        wsapp.send(json.dumps(data))

    def start(self):
        logging.info("Reading mempool of:")
        logging.info(f"Network: {self.network}")
        logging.info(f"Address: {self.address1}")
        logging.info(f"Address: {self.address2}")
        logging.info(f"Address: {self.address3}")
        logging.info(f"Address: {self.address4}")
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
    parser.add_argument("-s", "--save", action="store_true", default=False,
                        help="Saves the received event on downloads to be used for testing/planning.")
    parser.add_argument("-i", "--id", default='pro',
                        choices=['pro', 'free'], help="Select the blocknative API key to use.")

    args = parser.parse_args()
    NETWORK = args.network.strip()
    THRESHOLD = float(args.threshold)
    TEST_MODE_FLAG = args.test
    SAVE_EVENTS = args.save
    DAPP_ID = args.id

    reader = MempoolReader(NETWORK, threshold=THRESHOLD, test=TEST_MODE_FLAG, save=SAVE_EVENTS, dapp_id=DAPP_ID)
    reader.start()
