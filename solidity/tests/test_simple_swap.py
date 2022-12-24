import pytest
from scripts.deploy import deployBot, fundWithWETH, loadYAMLConfig
import time
from brownie import accounts, network
@pytest.fixture
def botContract():
    return deployBot()

def test_swapUniswapV3SingleInput(botContract):
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
    # Sell WETH for USDC
    botContract.swapUniswapV3(tokens['WETH'], tokens['USDC'], wethTradeAmount, 0, 3000, botContract.address, 0)
    # Get balances after swapping
    (wethbal, usdcbal, _) = botContract.getBalances()
    wethExpected = (wethBeforeBal - wethTradeAmount)
    # Confirm USDC balance increased (bought) by some amount and WETH decreased (sold) by the amount specified
    assert usdcbal > usdcBeforeBal
    assert wethbal == wethExpected

def test_swapUniswapV2SingleInput(botContract):
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
    # Sell WETH for USDC
    botContract.swapUniswapV2(tokens['WETH'], tokens['USDC'], wethTradeAmount, 0, botContract.address)
    # Get balances after swapping
    (wethbal, usdcbal, _) = botContract.getBalances()
    wethExpected = (wethBeforeBal - wethTradeAmount)
    # Confirm USDC balance increased (bought) by some amount and WETH decreased (sold) by the amount specified
    assert usdcbal > usdcBeforeBal
    assert wethbal == wethExpected
