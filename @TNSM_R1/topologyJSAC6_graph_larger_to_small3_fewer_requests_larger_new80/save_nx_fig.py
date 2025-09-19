import networkx as nx
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(12,12))
ax = plt.subplot(111)
ax.set_title('Graph - Shapes', fontsize=10)

G = nx.DiGraph()
G.add_node('shape1', level=1)
G.add_node('shape2', level=2)
G.add_node('shape3', level=2)
G.add_node('shape4', level=3)
G.add_edge('shape1', 'shape2')
G.add_edge('shape1', 'shape3')
G.add_edge('shape3', 'shape4')
pos = nx.spring_layout(G)
nx.draw(G, pos, node_size=1500, node_color='yellow', font_size=8, font_weight='bold', with_labels=True)

plt.tight_layout()
plt.savefig("Graph.png", format="PNG")
plt.show()