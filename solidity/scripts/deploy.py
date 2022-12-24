from brownie import Bot, accounts, config, network
import os, yaml


def loadYAMLConfig():
    solidity_rootdir = os.environ.get('SOLIDITY_ROOTDIR','.')
    with open(solidity_rootdir +'/../config.yaml','r') as f:
        yamlConfig = yaml.safe_load(f)
    return yamlConfig


def deployBot():
    c = Bot.deploy({'from': accounts[0]})
    return c

def fundWithWETH(Botcontract, amount, fromAccount):
    Botcontract.depositETH({'from': fromAccount, 'value': amount})


def main():
    print(accounts[0])
    print('balance is ', accounts[0].balance())
    deployBot()
