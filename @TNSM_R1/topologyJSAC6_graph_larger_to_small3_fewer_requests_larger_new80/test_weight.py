import networkx as nx
G = nx.read_gpickle('myGraph.gpickle')
shortest_path = nx.shortest_path(G=G, source=1, target=3, weight="weight")
n = nx.shortest_path_length(G, 1, 3)
print(n)
print(nx.path_weight(G, shortest_path, "weight"))
print(nx.path_weight(G, [1, '0-1-out', '0-5-in', '0-5-out', '0-3-in', 3], "weight"))
print(nx.path_weight(G, [1, '1-1-out', '1-2-in', '1-2-out', '1-3-in', 3], "weight"))