import pytest
import brownie
from scripts.deploy import deployBot, fundWithWETH


@pytest.fixture
def botContract():
    return deployBot()


def test_example(botContract):
    account = brownie.accounts[0]

    fundWithWETH(botContract, 10e18, account)

    token0_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    token1_address = '0x2f141ce366a2462f02cea3d12cf93e4dca49e4fd'
    token0 = brownie.Contract.from_explorer(token0_address)
    token1 = brownie.Contract.from_explorer(token1_address)

    token0_balance = token0.balanceOf(botContract.address)
    print(f"Token0 balance: {token0_balance}")
    token1_balance = token1.balanceOf(botContract.address)
    print(f"Token1 balance: {token1_balance}")

    with brownie.reverts():
        tx = botContract.multiSwap(
            token0_address,
            token1_address,
            1e5,
            ['UniswapV2', 'UniswapV3-10000'],
            False
        )
    print(brownie.history[-1].call_trace(expand=True))

    token0_balance = token0.balanceOf(botContract.address)
    print(f"Token0 balance: {token0_balance}")
    token1_balance = token1.balanceOf(botContract.address)
    print(f"Token1 balance: {token1_balance}")
