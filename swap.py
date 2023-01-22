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
    swap_method: str
    router_name: str
    dex_name: str

class UnparsableSwapMethodException(Exception):
    """Swap detected but contract method cannot be parsed properly. Contract method may be unsupported or unrecognized."""

class UnparsableTransactionException(Exception):
    """The provided transaction cannot be parsed for swaps. It may have a swap embedded but input data is unsupported or unrecognized"""

def parse_swap_tx_blocknative(blocknative_data):
    if 'subCalls' in blocknative_data['event']['contractCall']:
        subcalls = blocknative_data['event']['contractCall']['subCalls']
    else:
        # cannot parse swap in current logic so stop
        raise UnparsableTransactionException('Cannot parse swap data that does not list subCalls')

    to_address = blocknative_data['event']['transaction']['to']
    swaps = []
    for subcall in subcalls:
        try:
            swaps.append(get_swap_blocknative(subcall, to_address))
        except Exception as e:
            print('!! Error getting swap : ', e)
    return swaps


# TODO  use estimate inout methods instead of minmax for some functions
def get_swap_blocknative(subcall, router_address):
    call_method = subcall['data']['methodName']
    params = subcall['data']['params']
    config_router = config['networks']['mainnet']['exchangeRouters']
    if router_address == config_router['UniswapV3']:
        router_name = 'uniswapv3'
    elif router_address == config_router['UniswapV302']:
        router_name = 'uniswapv302'
    elif router_address == config_router['UniswapV2']:
        router_name = 'uniswapv2'
    elif router_address == config_router['Sushiswap']:
        router_name = 'sushiswap'
    else:
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
                dex_name='uniswapv3'
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
                dex_name='uniswapv3'
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
        case 'swapTokensforExactTokens':
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
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapTokensForExactEth':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactTokensForETH':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapETHForExactTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactTokensForTokensSupportingFeeOnTransferTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactETHForTokensSupportingFeeOnTransferTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case 'swapExactTokensForETHSupportingFeeOnTransferTokens':
            raise UnparsableSwapMethodException("No handle for swap method %s" % call_method)
        case _:
            raise UnparsableSwapMethodException(
                "Unrecognized contractcall method %s" % call_method)


def get_v2_pair(w3, token_in, token_out, router_name):
    if router_name == 'uniswapv2' or router_name == 'uniswapv302':
        with open('./interfaces/uniswapv2/factory.abi', 'r') as f:
            factory_abi = f.read().rstrip()
        factory_address = config['networks']['mainnet']['exchangeFactories']['UniswapV2']
    elif router_name == 'sushiswap':
        with open('./interfaces/sushiswap/factory.abi', 'r') as f:
            factory_abi = f.read().rstrip()
        factory_address = config['networks']['mainnet']['exchangeFactories']['Sushiswap']
    else:
        raise Exception("Cannot run get_v2_pair on dex router %s" % router_name)

    factory_contract = w3.eth.contract(
        address=factory_address, abi=factory_abi)
    pair_address = factory_contract.functions.getPair(
        token_in, token_out).call()
    return pair_address


def get_v2_pair_reserves(w3, pair_address, router_name):
    if router_name == 'uniswapv2' or router_name == 'uniswapv302':
        with open('./interfaces/uniswapv2/pair.abi', 'r') as f:
            pair_abi = f.read().rstrip()
    elif router_name == 'sushiswap':
        with open('./interfaces/sushiswap/pair.abi', 'r') as f:
            pair_abi = f.read().rstrip()
    else:
        raise Exception("Cannot run get_v2_pair_reserves on dex %s" % router_name)

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    (token0_reserve, token1_reserve,
     last_block_timestamp) = pair_contract.functions.getReserves().call()
    return {"token0": int(token0_reserve), "token1": int(token1_reserve)}

def get_v2_token0(w3, pair_address, router_name):
    if router_name == 'uniswapv2' or router_name == 'uniswapv302':
        with open('./interfaces/uniswapv2/pair.abi', 'r') as f:
            pair_abi = f.read().rstrip()
    elif router_name == 'sushiswap':
        with open('./interfaces/sushiswap/pair.abi', 'r') as f:
            pair_abi = f.read().rstrip()
    else:
        raise Exception("Cannot run get_v2_pair_reserves on dex %s" % router_name)

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    token0 = pair_contract.functions.token0().call()
    # We assume we already know both token addresses but not which is token0 or token1
    # Speed up execution by evaluating what is token0, assume other token is token1
    return token0

def get_alt_pairs(w3, token0, token1, dex_name):
    dex_list = [
       'uniswapv3',
       'uniswapv2',
       'sushiswap'
    ]
    dex_list.remove(dex_name)

    EMPTY_PAIR = '0x0000000000000000000000000000000000000000'

    alt_pair_list = []

    # Placeholder code to lookup matching pairs in hashmap instead of slow contract calls
    is_pair_in_hashmap = False
    if is_pair_in_hashmap:
        return alt_pair_list

    for dex in dex_list:
        match dex:
            case 'uniswapv3':
                factory_address = config['networks']['mainnet']['exchangeFactories']['UniswapV3']
                with open('./interfaces/uniswapv3/factory.abi','r') as f:
                    factory_abi = f.read().rstrip()

                factory_contract = w3.eth.contract(
                    address=factory_address, abi=factory_abi)

                for pool_fee in [1, 500, 3000, 10000]:
                    pair =  factory_contract.functions.getPool(token0, token1, pool_fee).call()
                    if pair != EMPTY_PAIR:
                        alt_pair_list.append(pair)

            case 'uniswapv2':
                factory_address = config['networks']['mainnet']['exchangeFactories']['UniswapV2']
                with open('./interfaces/uniswapv2/factory.abi','r') as f:
                    factory_abi = f.read().rstrip()

                factory_contract = w3.eth.contract(
                    address=factory_address, abi=factory_abi)

                pair = factory_contract.functions.getPair(token0, token1).call()

                if pair != EMPTY_PAIR:
                    alt_pair_list.append(pair)

            case 'sushiswap':
                factory_address = config['networks']['mainnet']['exchangeFactories']['Sushiswap']
                with open('./interfaces/sushiswap/factory.abi','r') as f:
                    factory_abi = f.read().rstrip()

                factory_contract = w3.eth.contract(
                    address=factory_address, abi=factory_abi)

                pair = factory_contract.functions.getPair(token0, token1).call()

                if pair != EMPTY_PAIR:
                    alt_pair_list.append(pair)

    if len(alt_pair_list) < 1:
        raise Exception("No alternative pairs found! Cannot arbitrage without another pair")

    return alt_pair_list
