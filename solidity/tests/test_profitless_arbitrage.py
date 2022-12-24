import pytest
from scripts.deploy import deployBot, fundWithWETH, loadYAMLConfig
import time
from brownie import accounts, network

@pytest.fixture
def botContract():
    return deployBot()

def test_profitlessSwapV3toV2(botContract):
    account = accounts[0]
    wethExpected = 0
    usdcExpected = 0
    (wethbal, usdcbal, _) = botContract.getBalances()
    # Expect Balances to be 0 when not yet funded.
    assert wethbal == wethExpected
    assert usdcbal == usdcExpected
    fundWithWETH(botContract,3e18,account)
    wethExpected = 3e18
    (wethbal, usdcbal, _) = botContract.getBalances()
    # Expect balance change to reflect WETH deposit amount
    assert wethbal == wethExpected
    assert usdcbal == usdcExpected
    wethTradeAmount = 1e18
    # Record balances before swapping
    usdcBeforeBal = usdcbal
    wethBeforeBal = wethbal
    tokens = loadYAMLConfig()['networks']['mainnet']['tokens']
    # Cross Swap without checking for profit
    botContract.swapV3ExactForV2(tokens['USDC'],tokens['WETH'],wethTradeAmount,False)
    (wethbal, usdcbal, _) = botContract.getBalances()
    assert usdcBeforeBal == usdcbal
    # Check change in balance is very small
    assert (abs(wethBeforeBal - wethbal) / wethBeforeBal )< 0.02
