# Preinstallation
You will need to install eth-brownie with pip.

# Prequisites

Before compiling or running tests you will need to source the `.env` file. Check the INFURA ID and other variables before proceeding.

# Compiling

To compile run the following
`source .env && brownie compile`


To compile and run interactive prompt
`brownie compile && brownie console --network mainnet-fork`

# Test Cases

Test Cases Handled
 - Swap WETH for USDC on UniswapV2
 - Swap WETH for USDC on UniswapV3
 - Swap WETH->USDC-WETH for no profit between V2 and V3
 - Swap WETH->USDC->WETH for profit between V2 and V3 by imbalancing the pool before swap

To run all test cases:
`brownie test --network mainnet-fork`


# Testing Live with Comparator

1. Comparator detects profitable swap
2. Comparator uses brownie to create a fork of the current mainnet using INFURA ID
3. Ensure tx in mempool is included
4. Use brownie to deploy bot contract and call the swap.


# TODO

1. Make Bot upgradeable by selfdestructing and redeploying to the same address
2. Add Sushiswap and other DEXes
3. Gas Optimizations
4. Add ability to borrow
5. Add ability to make more than hops over 3 or more DEXes
6. Add withdraw functions for all ERC20 and ETH
7. Add Bundling
8. Add ability to call directy to pool pairs instead of router for gas optimization and accuracy when required


