import pytest
from scripts.deploy import deployBot, fundWithWETH, loadYAMLConfig
import time
from brownie import accounts, network

@pytest.fixture
def botContract():
    return deployBot()

def test_profitableSwapV3toV2(botContract):
    account = accounts[0]
    wethExpected = 0
    usdcExpected = 0
    (wethbal, usdcbal, _) = botContract.getBalances()
    # Expect Balances to be 0 when not yet funded.
    assert wethbal == wethExpected
    assert usdcbal == usdcExpected
    fundedWETHAmount = 0
    for i in range(1,9):
        fundableBalance = accounts[i].balance()
        fundAmount = fundableBalance - 1e18
        print('Account ',i, ' balance is ', fundableBalance/1e18, 'ETH')
        if fundableBalance > 1e18:
            print('funding with WETH ', fundAmount/1e18)
            fundWithWETH(botContract, fundAmount, accounts[i])
            fundedWETHAmount += fundAmount
    print('total WETH Funds are ', fundedWETHAmount/1e18)
    wethSkewAmount = 2000e18
    # Record balances before swapping
    tokens = loadYAMLConfig()['networks']['mainnet']['tokens']
    # Sell large amount of WETH for USDC to skew V2 Pool
    botContract.swapUniswapV2(tokens['WETH'], tokens['USDC'], wethSkewAmount, 0, botContract.address)
    # Try to arb for profit with 1 ETH
    (wethbal, usdcbal, _) = botContract.getBalances()
    usdcBeforeBal = usdcbal
    wethBeforeBal = wethbal
    wethTradeAmount=1e18
    botContract.swapV3ExactForV2(tokens['USDC'],tokens['WETH'],wethTradeAmount,True)
    (wethbal, usdcbal, _) = botContract.getBalances()
    # WETH balance should be higher
    assert wethbal > wethBeforeBal
    print("Arbitrage Test Profit is ", (wethbal - wethBeforeBal)/1e18, "WETH")
