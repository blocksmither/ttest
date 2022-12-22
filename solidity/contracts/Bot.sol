// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
//import "@uniswapv2-periphery/contracts/interfaces/IUniswapV2Pair.sol";
//import "@uniswapv2-periphery/contracts/interfaces/IUniswapV2Factory.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@openzeppelin/openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IWETH9.sol";

contract Bot {
  address public owner;
  ISwapRouter private constant v3Router = ISwapRouter(0xE592427A0AEce92De3Edee1F18E0157C05861564);
  IUniswapV2Router02 private constant v2Router = IUniswapV2Router02(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
  address private constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
  address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

  IWETH9 private IWETH = IWETH9(payable(WETH));
  IERC20 private usdc = IERC20(USDC);

  event Log(string message, uint data);
  event LogAddress(string message, address addy);
  constructor() {
    owner = msg.sender;
    IERC20(USDC).approve(address(v3Router),type(uint).max);
    IERC20(WETH).approve(address(v3Router),type(uint).max);
    usdc.approve(address(v2Router),type(uint).max);
    IWETH.approve(address(v2Router),type(uint).max);
  }
  
  function depositETH() external payable {
    IWETH.deposit{value: msg.value}();
  }

  function getBalances() external view returns (uint, uint, uint) {
    uint wethbal = IWETH.balanceOf(address(this));
    uint usdcbal = usdc.balanceOf(address(this));
    uint ethbal = address(this).balance;
    return (wethbal, usdcbal, ethbal);

  }

  function swapUniswapV3(address _tokenIn, address _tokenOut, uint _amountIn, uint _amountOutMin, uint24 _poolFee, address _toAddress, uint160 _sqrtPriceLimitX96) public returns (uint){
    require(msg.sender == owner);
    ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
      tokenIn: _tokenIn,
      tokenOut: _tokenOut,
      fee: _poolFee,
      recipient: _toAddress,
      deadline: block.timestamp,
      amountIn: _amountIn,
      amountOutMinimum: _amountOutMin,
      sqrtPriceLimitX96: _sqrtPriceLimitX96
    });
    
    return v3Router.exactInputSingle(params);
  }
  
  function swapV3ExactForV2(address _v3BuyToken, address _v3SellToken, uint _v3SellAmount,bool profitCheck) external {

    require(msg.sender == owner);
    IERC20 Iv3BuyToken = IERC20(_v3BuyToken);
    IERC20 Iv3SellToken = IERC20(_v3SellToken);
    
    require(Iv3SellToken.balanceOf(address(this)) >= _v3SellAmount, "Not enough token to sell");
    uint v3BuyAmount = swapUniswapV3(
      _v3SellToken,
      _v3BuyToken,
      _v3SellAmount,
      0,
      3000,
      address(this),
      0
    );
    
    uint outAmount = swapUniswapV2(_v3BuyToken, _v3SellToken, v3BuyAmount, 0, address(this));

    if(profitCheck) {
      require(outAmount >= _v3SellAmount, "This transaction doesn't make profit!");
    }
  }

  function swapUniswapV2(address _tokenIn, address _tokenOut, uint _tokenInAmount, uint _minTokenOutAmount, address _toAddress) public returns (uint) {
    require(msg.sender == owner);

    address[] memory path = new address[](2);
    path[0] = _tokenIn;
    path[1] = _tokenOut;
    uint[] memory swapAmounts = v2Router.swapExactTokensForTokens(
      _tokenInAmount,
      _minTokenOutAmount,
      path,
      _toAddress,
      block.timestamp
    );

    return swapAmounts[1];
  }
}
