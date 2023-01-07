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
  IUniswapV2Router02 private constant sushiRouter = IUniswapV2Router02(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
  address private constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
  address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

  IWETH9 private IWETH = IWETH9(payable(WETH));
  IERC20 private usdc = IERC20(USDC);

  event Log(string message, uint data);
  event LogAddress(string message, address addy);
  constructor() {
    owner = msg.sender;
    // Approve UniswapV3 on all tokens
    usdc.approve(address(v3Router),type(uint).max);
    IWETH.approve(address(v3Router),type(uint).max);
    // Approve UniswapV2 on all tokens
    usdc.approve(address(v2Router),type(uint).max);
    IWETH.approve(address(v2Router),type(uint).max);
    // Approve SushiSwap on all tokens
    usdc.approve(address(sushiRouter),type(uint).max);
    IWETH.approve(address(sushiRouter),type(uint).max);
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

  function swapUniswapV3(
      address _tokenIn, 
      address _tokenOut, 
      uint _amountIn, 
      uint _amountOutMin, 
      uint24 _poolFee, 
      address _toAddress, 
      uint160 _sqrtPriceLimitX96
    ) private returns (uint){

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

  function swapUniswapV2(
    address _tokenIn, 
    address _tokenOut, 
    uint _tokenInAmount, 
    uint _minTokenOutAmount, 
    address _toAddress
    ) private returns (uint) {

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

  function swapSushiSwap(
    address _tokenIn, 
    address _tokenOut, 
    uint _tokenInAmount, 
    uint _minTokenOutAmount, 
    address _toAddress
    ) private returns (uint) {

      address[] memory path = new address[](2);
      path[0] = _tokenIn;
      path[1] = _tokenOut;
      uint[] memory swapAmounts = sushiRouter.swapExactTokensForTokens(
        _tokenInAmount,
        _minTokenOutAmount,
        path,
        _toAddress,
        block.timestamp
      );

      return swapAmounts[1];
  }

  function multiSwap(
    address inToken, 
    address arbToken, 
    uint arbAmount, 
    string[] calldata dexs,
    bool profitCheck
    ) external {

    require(msg.sender == owner);

    address currentIn = inToken;
    address currentOut = arbToken;
    address holder;
    uint currentAmount = arbAmount;

    for (uint i = 0; i < dexs.length; i++) {
      if (keccak256(abi.encodePacked(dexs[i])) == keccak256(abi.encodePacked('Sushiswap'))) {
        currentAmount = swapSushiSwap(currentIn, currentOut, currentAmount, 0, address(this));
      } else if (keccak256(abi.encodePacked(dexs[i])) == keccak256(abi.encodePacked('UniswapV2'))) {
        currentAmount = swapUniswapV2(currentIn, currentOut, currentAmount, 0, address(this));
      } else if (keccak256(abi.encodePacked(dexs[i])) == keccak256(abi.encodePacked('UniswapV3'))) {
        currentAmount = swapUniswapV3(currentIn, currentOut, currentAmount, 0, 3000, address(this), 0);
      } else {
        revert();
      }
      holder = currentIn;
      currentIn = currentOut;
      currentOut = holder;
    }

    if(profitCheck) {
      require(currentAmount >= arbAmount, "This transaction doesn't make profit!");
    }
  }  
}
