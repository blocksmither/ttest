import logging
import os
from dataclasses import dataclass

import yaml

with open(os.path.join(os.path.dirname(__file__), 'config.yaml')) as f:
    config = yaml.safe_load(f)


logger = logging.getLogger(__name__)


@dataclass
class RouterSwap:
    token_in: str
    token_in_amount: int
    token_out: str
    token_out_amount: int
    router_address: str
    swap_method: str
    router_name: str
    dex_name: str
    fee: str = "3000"


@dataclass
class Pair:
    # A Pair may contain more than 2 tokens for some DEX
    # token0 address from a contract should be tokens[0]
    tokens: list
    reserves: list
    # Address of the contract that created the pair
    factory: str
    # Address of the Pair Contract
    address: str
    fee: float
    dex_name: str
    predicted_price: float


@dataclass
class V3Pool(Pair):
    sqrtpricex96: int
    tick: int
    liquidity: int


class UnparsableSwapMethodException(Exception):
    """Swap detected but contract method cannot be parsed properly. Contract method may be unsupported or unrecognized."""


class UnparsableTransactionException(Exception):
    """The provided transaction cannot be parsed for swaps. It may have a swap embedded but input data is unsupported or unrecognized"""


def parse_swap_tx_blocknative(blocknative_data):
    if 'subCalls' in blocknative_data['event']['contractCall']:
        subcalls = blocknative_data['event']['contractCall']['subCalls']
    else:
        subcalls = [{'data': blocknative_data['event']['contractCall']}]

    to_address = blocknative_data['event']['transaction']['to']
    swaps = []
    for subcall in subcalls:
        try:
            swaps.append(get_swap_blocknative(subcall, to_address, blocknative_data))
        except Exception as e:
            logging.debug(f'!! Error getting swap: {e}')
    return swaps


# TODO  use estimate inout methods instead of minmax for some functions
def get_swap_blocknative(subcall, router_address, blocknative_data):
    call_method = subcall['data']['methodName']
    params = subcall['data']['params']
    config_router = config['networks']['mainnet']['exchangeRouters']

    routers = {
        config_router['UniswapV3'].lower(): 'uniswapv3',
        config_router['UniswapV302'].lower(): 'uniswapv302',
        config_router['UniswapV2'].lower(): 'uniswapv2',
        config_router['Sushiswap'].lower(): 'sushiswap'
    }
    router_name = routers.get(router_address.lower())
    if router_name is None:
        raise Exception(
            "Swap Router is not recognized in to address of transaction: %s" % (router_address))

    match call_method:
        # Uniswap V3 Router Methods
        case 'exactInputSingle':
            # params key nested twice
            params = params['params']
            return RouterSwap(
                token_in=params['tokenIn'],
                token_in_amount=int(params['amountIn']),
                token_out=params['tokenOut'],
                token_out_amount=int(params['amountOutMinimum']),
                router_name=router_name,
                swap_method='exactInputSingle',
                router_address=router_address,
                dex_name='uniswapv3',
                fee=params['fee']
            )
        case 'exactInput':
            # This has multiple pools
            raise Exception("No handle for swap method %s" % call_method)
        case 'exactOutputSingle':
            # params key nested twice
            params = params['params']
            return RouterSwap(
                token_in=params['tokenIn'],
                token_in_amount=int(params['amountInMaximum']),
                token_out=params['tokenOut'],
                token_out_amount=int(params['amountOut']),
                router_name=router_name,
                swap_method='exactOutputSingle',
                router_address=router_address,
                dex_name='uniswapv3',
                fee=params['fee']
            )
        case 'exactOutput':
            # This has multiple pools
            raise Exception("No handle for swap method %s" % call_method)
        # Uniswap V2 and Sushiswap Router Methods
        case 'swapExactTokensForTokens':
            # This can affect multiple pairs if path length > 2
            # Example if len(path)==3 then 2 pairs are affected
            # Pair1 = path[0] and path[1]  Pair2 = path[1] and path[2]
            # path[0] and path[-1] is not a pair, but does give total token in and Out
            # But we cannot clearly see which pairs get affected
            # TODO: Catch multiple pairs that could be imbalanced and check against other dexes
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')

            if router_name == 'sushiswap':
                dex_name = 'sushiswap'
            else:
                dex_name = 'uniswapv2'

            return RouterSwap(
                token_in=params['path'][0],
                token_in_amount=int(params['amountIn']),
                token_out=params['path'][1],
                token_out_amount=int(params['amountOutMin']),
                router_name=router_name,
                swap_method='swapExactTokensForTokens',
                router_address=router_address,
                dex_name=dex_name
            )
        case 'swapTokensForExactTokens':
            # This can affect multiple pairs if path length > 2
            # Example if len(path)==3 then 2 pairs are affected
            # Pair1 = path[0] and path[1]  Pair2 = path[1] and path[2]
            # path[0] and path[-1] is not a pair, but does give total token in and Out
            # But we cannot clearly see which pairs get affected
            # TODO: Catch multiple pairs that could be imbalanced and check against other dexes
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')

            if router_name == 'sushiswap':
                dex_name = 'sushiswap'
            else:
                dex_name = 'uniswapv2'

            return RouterSwap(
                token_in=params['path'][0],
                token_in_amount=int(params['amountOut']),
                token_out=params['path'][1],
                token_out_amount=int(params['amountInMax']),
                router_name=router_name,
                swap_method='swapTokensForExactTokens',
                router_address=router_address,
                dex_name=dex_name
            )
        case 'swapExactETHForTokens':
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')

            if router_name == 'sushiswap':
                dex_name = 'sushiswap'
            else:
                dex_name = 'uniswapv2'

            return RouterSwap(
                # path0 will be WETH
                token_in=params['path'][0],
                token_in_amount=int(blocknative_data['event']['transaction']['value']),
                token_out=params['path'][1],
                token_out_amount=int(params['amountOutMin']),
                router_name=router_name,
                swap_method='swapExactTokensForTokens',
                router_address=router_address,
                dex_name=dex_name
            )
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapTokensForExactEth':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactTokensForETH':
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')

            if router_name == 'sushiswap':
                dex_name = 'sushiswap'
            else:
                dex_name = 'uniswapv2'

            return RouterSwap(
                token_in=params['path'][0],
                token_in_amount=int(params['amountIn']),
                token_out=params['path'][1],
                token_out_amount=int(params['amountOutMin']),
                router_name=router_name,
                swap_method='swapExactTokensForTokens',
                router_address=router_address,
                dex_name=dex_name
            )
        case 'swapETHForExactTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactTokensForTokensSupportingFeeOnTransferTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactETHForTokensSupportingFeeOnTransferTokens':
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')

            if router_name == 'sushiswap':
                dex_name = 'sushiswap'
            else:
                dex_name = 'uniswapv2'

            return RouterSwap(
                token_in=params['path'][0],
                token_in_amount=int(params['amountIn']),
                token_out=params['path'][1],
                token_out_amount=int(params['amountOutMin']),
                router_name=router_name,
                swap_method='swapExactTokensForTokens',
                router_address=router_address,
                dex_name=dex_name
            )
        case 'swapExactTokensForETHSupportingFeeOnTransferTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case _:
            raise UnparsableSwapMethodException(
                "Unrecognized contractcall method %s" % call_method)
