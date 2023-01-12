import json
from py2neo import Graph
from py2neo.bulk import create_nodes,create_relationships
import gc

#TODO - This is really slow on large number of pairs, find way to speed it up possibly using bulk API
# https://py2neo.org/2021.1/bulk/index.html
def plot_v2_graphs(graph, v2poolfile):
    
    f = open(v2poolfile)
    v2pairs = json.load(f)
    f.close()
    # Process the results and add nodes and edges to the graph
    totalPairs = len(v2pairs["data"]["pairs"])
    paircounter = 1
    createKeys = ["id","token0","token0symbol","token1","token1symbol"]
    createData = []
    for pair in v2pairs["data"]["pairs"]:
        print("Processing %d/%d pairs" % (paircounter,totalPairs))
        # Create a node for the liquidity pool pair
        createData.append([pair["id"],pair["token0"]["id"],pair["token0"]["symbol"],pair["token1"]["id"],pair["token1"]["symbol"]])
        paircounter+=1
    create_nodes(graph.auto(),createData,labels={"Pair"},keys=createKeys)

    # Create links between DEX Pairs
    # TODO - speed up for loop. Very slow for large number of pairs (i.e. 1000).
    #   Using something like set() might speed up
    #   https://note.nkmk.me/en/python-set/
    #   https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset
    paircounter = 1
    relationshipData=[]
    for pair in v2pairs["data"]["pairs"]:
        gc.disable()
        pair2counter = 1
        for pair2 in v2pairs["data"]["pairs"]:
            pair2tokens = [pair2["token0"],pair2["token1"]]
            print("On Pair %d, linking %d/%d pairs" % (paircounter,pair2counter,totalPairs))
            if(
              (pair["token0"] in pair2tokens or pair["token1"] in pair2tokens)
              # don't link pair to itself
              and pair["id"] is not pair2["id"]
              # don't link if the reciprocal relationship already in pair
              # otherwise will create pair->pair2 and pair2->pair for every token match
              and (pair2["id"], {},pair["id"]) not in relationshipData):
                relationshipData.append((
                pair["id"],
                {},
                pair2["id"]
                ))
            pair2counter+=1
        paircounter+=1
    gc.enable()
    create_relationships(
        graph.auto(),
        relationshipData,
        "SHARES_TOKEN",
        start_node_key=("Pair","id"),
        end_node_key=("Pair","id")
    )


def plot_v3_graphs(graph,v3poolfile,v2poolfile):
    
    f = open(v3poolfile)
    v3pools = json.load(f)
    f.close()
    f = open(v2poolfile)
    v2pairs = json.load(f)
    f.close()
    
    totalPools = len(v3pools["data"]["pools"])
    totalPairs = len(v2pairs["data"]["pairs"])
    # Process the results and add nodes and edges to the graph
    poolcounter = 1
    createKeys = ["id","token0","token0symbol","token1","token1symbol"]
    createData = []
    for pool in v3pools["data"]["pools"]:
        print("Creating %d/%d pools" %(poolcounter,totalPools))
        # Create a node for the liquidity pool pool
        createData.append([pool["id"],pool["token0"]["id"],pool["token0"]["symbol"],pool["token1"]["id"],pool["token1"]["symbol"]])
        poolcounter+=1
    create_nodes(graph.auto(),createData,labels={"Pair"},keys=createKeys)

    # Create links between DEX Pools and Pairs
    # TODO - speed up for loop. Very slow for large number of pairs.
    #   Using something like set() might speed up
    #   https://note.nkmk.me/en/python-set/
    #   https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset
    poolcounter=1
    relationshipData=[]
    for pool in v3pools["data"]["pools"]:
        gc.disable()
        print("Processing %d/%d pools" %(poolcounter,totalPools))
        # Create edges between pools that share the same ERC20 token
        pool2counter = 1
        for pool2 in v3pools["data"]["pools"]:
            print("On Pool %d, linking %d/%d pools" % (poolcounter,pool2counter,totalPools))
            pool2tokens = [pool2["token0"],pool2["token1"]]
            if(
              (pool["token0"] in pool2tokens or pool["token1"] in pool2tokens)
              # don't link pool to itself
              and pool["id"] is not pool2["id"]
              # don't link if the reciprocal relationship already in pool
              # otherwise will create pool->pool2 and pool2->pool for every token match
              and (pool2["id"], {},pool["id"]) not in relationshipData):
                relationshipData.append((
                pool["id"],
                {},
                pool2["id"]
                ))
            pool2counter+=1
        # Create edges between v3pools and v2pairs that share the same ERC20 token
        pair2counter = 1
        for pair2 in v2pairs["data"]["pairs"]:
            print("On Pool %d, linking %d/%d pairs" % (poolcounter,pair2counter,totalPairs))
            pair2tokens = [pair2["token0"],pair2["token1"]]
            if pool["token0"] in pair2tokens or pool["token1"] in pair2tokens:
                relationshipData.append((
                    pool["id"],
                    {},
                    pair2["id"]
                ))
            pair2counter+=1
        poolcounter+=1
    gc.enable()
    create_relationships(
        graph.auto(),
        relationshipData,
        "SHARES_TOKEN",
        start_node_key=("Pair","id"),
        end_node_key=("Pair","id")
    )


# Connect to the graph database
graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j123"))

plot_v2_graphs(graph,'./pairpages/v2pair-1.json')
plot_v3_graphs(graph,'./pairpages/v3pool-1.json','./pairpages/v2pair-1.json')
