from brownie import accounts, config, bot, network
import yaml
import os

def getAccount():
    networkName = network.show_active()
    devNetworks = ['development','mainnet-fork']

    if networkName in devNetworks:
        return accounts[0]
    else:
        return accounts.add(config['wallets'][networkName]['privateKey'])

def fundWithWETH(botContract, amount=1e18):
    account = getAccount()
    botContract.depositETH({"from": account, "value": amount})

def loadYAMLConfig():
    solidity_rootdir = os.environ.get('SOLIDITY_ROOTDIR','.')
    with open(solidity_rootdir +'/../config.yaml','r') as f:
        yamlConfig = yaml.safe_load(f)
    return yamlConfig

def main():
    _
