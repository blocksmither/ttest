from py2neo import Graph
from py2neo.bulk import create_nodes,create_relationships
import json, time, concurrent.futures, gc

def remove_reciprocals(lst):
    seen_pairs = set()
    return [tup for tup in lst if not (tup[2], tup[0]) in seen_pairs and not seen_pairs.add((tup[0], tup[2]))]

def create_relationships_chunk(graph, chunk):
    create_relationships(
        graph.auto(),
        chunk,
        "SHARES_TOKEN",
        start_node_key=("Pair","id"),
        end_node_key=("Pair","id")
    )

def create_nodes_chunk(graph, chunk):
        graph.create(*chunk)

def create_relationships_with_retry(graph,chunknumber,chunkmax,chunk,rel_type,start_node_key,end_node_key,tries=30):
    # Use begin(),commit(), and rollback() to ensure tx is properly closed or rolledback on fail, and is not open when starting
    # Otherwise a failed transaction thread could fail every time
    for i in range(tries):
        try:
            start_time=time.time_ns()
            tx=graph.begin()
            print(f"Attempting chunk {chunknumber}/{chunkmax}")
            create_relationships(tx,chunk,rel_type,start_node_key,end_node_key)
            graph.commit(tx)
            duration_ms = (time.time_ns() - start_time)/1000/1000
            print(f"Finished {chunknumber} in {duration_ms} milliseconds")
            break
        except Exception as e:
            graph.rollback(tx)
            if i+1 == tries:
                raise e
            print(f"!WARNING! backing off {i/2} seconds on chunk {chunknumber}")
            time.sleep(i/2)


def plot_v2_graphs(graph, v2poolfile):

    with open(v2poolfile) as f:
        v2pairs = json.load(f)

    print("Creating nodes for v2 pairs...")
    # Using list comprehension to create nodes
    createKeys = ["id",'dexname',"token0","token0symbol","token1","token1symbol"]
    createData = []
    for pair in v2pairs["data"]["pairs"]:
        createData.append([pair["id"],'UniswapV2',pair["token0"]["id"],pair["token0"]["symbol"],pair["token1"]["id"],pair["token1"]["symbol"]])
    create_nodes(graph.auto(),createData,labels={"Pair"},keys=createKeys)

    print("Creating relationships between v2 pairs...")
    pair2tokens = [[pair2["token0"], pair2["token1"]] for pair2 in v2pairs["data"]["pairs"]]
    relationshipData = [(pair["id"], {}, pair2["id"])
                    for paircounter, pair in enumerate(v2pairs["data"]["pairs"])
                    for pair2counter, (pair2, tokens) in enumerate(zip(v2pairs["data"]["pairs"], pair2tokens))
                    if (pair["id"] is not pair2["id"])
                    and (pair["token0"] in tokens or pair["token1"] in tokens)
                    ]
    print("removing reciprocal relationships...")
    relationshipDataClean = remove_reciprocals(relationshipData)
    print("sorting relationship list to minimized thread deadlocks")
    relationshipDataClean.sort()
    print("committing relationships...")

    chunk_size = 100
    chunks = [relationshipDataClean[i:i+chunk_size] for i in range(0, len(relationshipDataClean), chunk_size)]
    chunkmax = len(chunks)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk = [executor.submit(create_relationships_with_retry,graph, chunknumber, chunkmax, chunk,"SHARES_TOKEN",start_node_key=("Pair","id"),end_node_key=("Pair","id")) for chunknumber,chunk in enumerate(chunks)]
        for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
            try:
                future.result()
                print(f"Successfully processed chunk {i}")
            except Exception as exc:
                print(f"!Error! Failed to create relationships for chunk {i}, with error {exc}")
        gc.collect()

def plot_v3_graphs(graph, v3poolfile, v2poolfile):

    with open(v3poolfile) as f:
        v3pools = json.load(f)

    with open(v2poolfile) as f:
        v2pairs = json.load(f)

    print("Creating V3 Pair nodes...")
    # Using list comprehension to create nodes
    createKeys = ["id",'dexname',"token0","token0symbol","token1","token1symbol"]
    createData = []
    for pool in v3pools["data"]["pools"]:
        createData.append([pool["id"],'UniswapV3',pool["token0"]["id"],pool["token0"]["symbol"],pool["token1"]["id"],pool["token1"]["symbol"]])
    create_nodes(graph.auto(), createData, labels={"Pair"}, keys=createKeys)

    # Using list comprehension to create relationship between pools
    relationshipData = [(pool["id"], {}, pool2["id"])
                       for pool in v3pools["data"]["pools"]
                       for pool2 in v3pools["data"]["pools"]
                       if pool["token0"]["id"] in [pool2["token0"]["id"], pool2["token1"]["id"]] and pool["id"] != pool2["id"]]

    # List of relationships will contain reciprocals, remove them
    # Pool1->Pool2 and Pool2->Pool1, so only one copy: Pool1->Pool2 remains
    print("removing reciprocal relationships...")
    relationshipDataClean = remove_reciprocals(relationshipData)

    print("creating relationships between V3 and V2 Pairs...")
    # Using list comprehension to create relationship between pools and pairs
    relationshipDataClean += [(pool["id"], {}, pair2["id"])
                        for pool in v3pools["data"]["pools"]
                        for pair2 in v2pairs["data"]["pairs"]
                        if pool["token0"]["id"] in [pair2["token0"]["id"], pair2["token1"]["id"]]]

    print("sorting relationship list to minimized thread deadlocks")
    relationshipData.sort()
    print("committing relationships...")
    # Commit relationship edges in chunks of chunk_size and run the create function in separate threads to speed up create_relationship()
    chunk_size = 100
    chunks = [relationshipDataClean[i:i+chunk_size] for i in range(0, len(relationshipDataClean), chunk_size)]
    chunkmax = len(chunks)

    # Create a thread pool and use submit() to submit function and params to be executed by a thread in the thread pool
    # Use dict to store the future object returned by submit() to associate each future with corresponding chunk of relationships
    # Use as_completed() to return iterator of Future objects of the the completed futures. Wait for threads to finish and check results of completed futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk = [executor.submit(create_relationships_with_retry,graph, chunknumber, chunkmax, chunk,"SHARES_TOKEN",start_node_key=("Pair","id"),end_node_key=("Pair","id")) for chunknumber,chunk in enumerate(chunks)]
        for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
            try:
                future.result()
                print(f"Successfully processed chunk {i}")
            except Exception as exc:
                print(f"!Error! Failed to create relationships for chunk {i}, with error {exc}")
        gc.collect()

# Connect to the graph database
graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j123"))

print("Setup Uniswap V2 first")
start_time1 = time.time_ns()
plot_v2_graphs(graph, './pairpages/v2pair-1.json')
duration1 = (time.time_ns() - start_time1) /1000/1000/1000
print("---------")
print("Setup Uniswap V3")
start_time2 = time.time_ns()
plot_v3_graphs(graph, './pairpages/v3pool-1.json', './pairpages/v2pair-1.json')
duration2 = (time.time_ns() - start_time2) /1000/1000/1000
print("Executed V2 setup in %f seconds" % (duration1))
print("Executed V3 setup in %f seconds" % (duration2))
