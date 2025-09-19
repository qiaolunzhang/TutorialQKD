# from the following website
# https://mmitchell.net/graph_theory_shortest_path_lab
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

G = nx.navigable_small_world_graph(3, seed=3)
G = nx.relabel_nodes(G, dict(zip(G.nodes, ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])))
#nx.draw(G, pos=nx.random_layout(G, seed=9), with_labels=True, node_color='#1cf0c7',
#        node_size=500, font_weight='bold', width=2, alpha=0.8)

def dijkstra(G:nx.Graph, u, v):
    """
    :param G: the graph
    :param u: the starting node
    :param v:  the destination node
    :return: the shortest path
    """
    visited = set()
    unvisited = set(G.nodes)
    distances = {u:0}
    for node in unvisited:
        if node == u:
            continue
        else:
            distances[node] = np.inf

    cur_node = u
    weight = 1 # Set default weight for non-weighted graphs
    while len(unvisited) > 0:
        if cur_node == v:
            break
        if min([distances[node] for node in unvisited]) == np.inf:
            print('There is no path between u and v.')
            return np.nan
        # Pull up neighbors
        neighbors = G[cur_node]
        for node in neighbors:
            # Future update:Add weight update for weighted graphs
            # Set either the distance through the current node or a previous shorter path
            distances[node] = min(distances[cur_node] + weight, distances[node])
        # Mark current node as visited
        visited.add(cur_node)
        unvisited.remove(cur_node)
        # Set the node with the minimum distance as the current node
        cur_node = sorted([(node, distances[node]) for node in unvisited], key=lambda x: x[1])[0][0]
    return distances[v]


print(dijkstra(G, 'F', 'G'))
