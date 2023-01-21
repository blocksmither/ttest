import json
from dataclasses import dataclass
import yaml

with open('./config.yaml', 'r') as f:
    config = yaml.safe_load(f)

@dataclass
class RouterSwap:
    token_in: str
    token_in_amount: int
    token_out: str
    token_out_amount: int
    router_address: str
    dex_name: str

def parse_swap_tx_blocknative(blocknative_data):
    subcalls = blocknative_data['event']['contractCall']['subCalls']
    to_address = blocknative_data['event']['to']
    swaps = []
    for subcall in subcalls:
        try:
            swaps.append(get_swap_blocknative(subcall, to_address))
        except Exception as e:
            print('!! Error getting swap : ', e)


# TODO  use estimate inout methods instead of minmax for some functions
def get_swap_blocknative(subcall, router_address):
    call_method = subcall['data']['methodName']
    params = subcall['data']['params']
    config_router = config['networks']['mainnet']['exchangeRouters']
    if router_address == config_router['UniswapV3']:
       dex_name = 'uniswapv3'
    elif router_address == config_router['UniswapV302']:
       dex_name = 'uniswapv302'
    elif router_address == config_router['UniswapV2']:
       dex_name = 'uniswapv2'
    elif router_address == config_router['Sushiswap']:
       dex_name = 'sushiswap'
    else:
        raise Exception("Swap Router is not recognized in to address of transaction: %s" % (router_address))

    match call_method:
        # Uniswap V3 Router Methods
        case 'exactInputSingle':
            # params key nested twice
            params = params['params']
            return RouterSwap(
                    token_in = params['tokenIn'],
                    token_in_amount = int(params['amountIn']),
                    token_out = params['tokenOut'],
                    token_out_amount = int(params['amountOutMinimum']),
                    dex_name = dex_name,
                    router_address = router_address
                    )
        case 'exactInput':
            # This has multiple pools
            raise Exception("No handle for swap method %s" % call_method)
        case 'exactOutputSingle':
            # params key nested twice
            params = params['params']
            return RouterSwap(
                    token_in = params['tokenIn'],
                    token_in_amount = int(params['amountInMax']),
                    token_out = params['tokenOut'],
                    token_out_amount = int(params['amountOut']),
                    dex_name = dex_name,
                    router_address = router_address
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
            return RouterSwap(
                    token_in = params['path'][0],
                    token_in_amount = int(params['amountIn']),
                    token_out = params['path'][1],
                    token_out_amount = int(params['amountOutMin']),
                    dex_name = dex_name,
                    router_address = router_address
                    )
        case 'swapTokensforExactTokens':
            # This can affect multiple pairs if path length > 2
            # Example if len(path)==3 then 2 pairs are affected
            # Pair1 = path[0] and path[1]  Pair2 = path[1] and path[2]
            # path[0] and path[-1] is not a pair, but does give total token in and Out
            # But we cannot clearly see which pairs get affected
            # TODO: Catch multiple pairs that could be imbalanced and check against other dexes
            if len(params['path']) > 2:
                raise Exception('Cannot parse v2 swap path across >1 pairs')
            return RouterSwap(
                    token_in = params['path'][0],
                    token_in_amount = int(params['amountOut']),
                    token_out = params['path'][1],
                    token_out_amount = int(params['amountInMax']),
                    dex_name = dex_name,
                    router_address = router_address
                    )
        case 'swapExactETHForTokens':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapTokensForExactEth':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapExactTokensForETH':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapETHForExactTokens':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapExactTokensForTokensSupportingFeeOnTransferTokens':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapExactETHForTokensSupportingFeeOnTransferTokens':
            raise Exception("No handle for swap method %s" % call_method)
        case 'swapExactTokensForETHSupportingFeeOnTransferTokens':
            raise Exception("No handle for swap method %s" % call_method)
