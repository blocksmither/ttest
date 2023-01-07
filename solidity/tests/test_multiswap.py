import pytest
import itertools
import brownie
from scripts.deploy import deployBot, fundWithWETH, loadYAMLConfig


@pytest.fixture
def botContract():
    return deployBot()


def test_multiswap(botContract):
    dexs = ['Sushiswap', 'UniswapV2', 'UniswapV3']
    permutations = list(map(list, (itertools.permutations(dexs, 2))))

    account = brownie.accounts[0]
    wethExpected = 0
    usdcExpected = 0
    (wethbal, usdcbal, _) = botContract.getBalances()

    # Expect Balances to be 0 when not yet funded.
    assert wethbal == wethExpected
    assert usdcbal == usdcExpected

    # Fund 1 ETH for each dex permutation plus one
    wethExpected = 1e18 * (len(permutations) + 1)
    fundWithWETH(botContract, wethExpected, account)

    (wethbal, usdcbal, _) = botContract.getBalances()

    # Expect balance change to reflect WETH deposit amount
    assert wethbal == wethExpected
    assert usdcbal == usdcExpected

    wethTradeAmount = 1e18

    tokens = loadYAMLConfig()['networks']['mainnet']['tokens']

    # Make all possible swaps
    for permutation in permutations:
        botContract.multiSwap(tokens['WETH'], tokens['USDC'], wethTradeAmount, permutation, False)

    # Try swaping on a non supported dex
    with brownie.reverts():
        botContract.multiSwap(tokens['WETH'], tokens['USDC'], wethTradeAmount, ['Sashimiswap', 'UniswapV4'], False)

    # Try swaping not being the owner
    with brownie.reverts():
        botContract.multiSwap(tokens['WETH'], tokens['USDC'], wethTradeAmount, permutations[0], False, {'from': brownie.accounts[1]})

    # Try swaping checking profit
    with brownie.reverts():
        botContract.multiSwap(tokens['WETH'], tokens['USDC'], wethTradeAmount, permutations[0], True)
