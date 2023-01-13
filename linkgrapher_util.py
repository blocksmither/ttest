from py2neo import Graph


def find_shared_token_pairs(pair_id, token_address):
    # Connect to the graph database
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j"))

    # Find pairs that share the same ERC20 token
    query = """
    MATCH (p1:Pair {id: $pair_id})-[:SHARES_TOKEN]-(p2:Pair)
    WHERE p2.token0 = $token_address OR p2.token1 = $token_address
    RETURN p2.id as id
    """
    results = graph.run(query, pair_id=pair_id, token_address=token_address)

    # Extract the pair IDs from the results
    pair_ids = [result["id"] for result in results]

    return pair_ids


def delete_all_pair_nodes():
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "neo4j"))
    graph.delete_all()
