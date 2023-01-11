import argparse
import datetime
import json
import os
from decimal import Decimal

import brownie
import websocket
import yaml
from connectors import connectors

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

    def __init__(self, pair, swap, network):
        self.pair = pair
        self.swap = swap
        self.network = network
        self.connector = eval(f"connectors.{swap}('{network}')")
        self.address = self.config['networks'][self.network]['pairs'][self.swap][self.pair]
        self.wsapp = websocket.WebSocketApp("wss://api.blocknative.com/v0", on_open=self.on_open, on_message=self.on_message)
        self.solBotProject = brownie.project.load('./solidity')
        self.solBotProject.load_config()

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
            event['event']['transaction']['hash']
            print(datetime.datetime.now())
            print(f"hash: {event['event']['transaction']['hash']}")
            print(f"block: {event['event']['transaction']['blockNumber']}")

            op_type = 1

            for nbc in event['event']['transaction']['netBalanceChanges']:
                if nbc['address'].lower() == self.address.lower():
                    for bc in nbc['balanceChanges']:
                        print(f"delta: {Decimal(bc['delta']) / 10 ** symbol_dec(bc['asset']['symbol'])}, asset: {bc['asset']['symbol']}")
                        op_type *= float(bc['delta'])
            if op_type > 0:
                print("ADDING/RETRIEVING LIQUIDITY")
            else:
                print("SWAPING")
                if event['event']['transaction']['blockNumber'] is None:
                    self.connector.predict_price(self.pair, event['event']['transaction']['netBalanceChanges'])
                    # Test Code that Spin up a fork, broadcast the transaction, then try to swap against it.
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
                else:
                    print("Too slow. Can't predict price. Tx is already in the blockchain and price changed.")
        except:
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
                "address": self.address
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
        print(f"Pair: {self.pair}")
        print(f"Swap: {self.swap}")
        print(f"Network: {self.network}")
        print(f"Address: {self.address}")
        self.wsapp.run_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    This script prints transactions in the mempool
    """)
    parser.add_argument("-s", '--swap', default='UniswapV3', choices=["Sushiswap", "UniswapV2", "UniswapV3"], help="Swap")
    parser.add_argument("-n", "--network", default='mainnet', choices=['mainnet', 'goerli'], help="Select mainnet or testnet network")

    args = parser.parse_args()
    SWAP = args.swap
    NETWORK = args.network.strip()

    reader = MempoolReader('USDC-WETH', SWAP, NETWORK)
    reader.start()
