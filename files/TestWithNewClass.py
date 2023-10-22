import pandas as pd
import xmltodict
import json
import os
from AlteryxWorkflow import Workflow, Node
import networkx as nx
import matplotlib.pyplot as plt

os.chdir("/Users/adambahri/Desktop/ayx-python-converter/files")

TestWorkflow = Workflow("SampleWFwithJoinTool.xml")

data = TestWorkflow.nodes

# Parse the data and create Node objects
nodes = []
for node_data in data['Node']:
    node = Node(node_data)
    nodes.append(node)

# for node in nodes:
#     print("Node ID:", node.nodeId)
#     print("Node Type:", node.nodeType)
#     print("Position X:", node.positionX)
#     print("Position Y:", node.positionY)
#     print("Annotations:", node.annotations)
#     print("Configuration:", node.configuration)
#     print("Meta Info:", node.metaInfo)
#     print("Fields:", node.fields)
#     print("Formulas:", node.formulas)
#     print("Is Disabled:", node.isDisabled)
#     print("----")

nodes_df = TestWorkflow.parse_nodes()

nodes_df.to_csv("nodes.csv", index=False)

connections_df = TestWorkflow.parse_connections()

connections_df.to_csv("connections.csv", index=False)

# joined = pd.merge(left = nodes_df, right = connections_df, left_on = "Node ID", right_on  = "OriginToolID")

# joined.to_csv("joined.csv", index=False)

# Create a directed graph
G = nx.DiGraph()

# Add nodes to the graph with position from nodes_df
for _, row in nodes_df.iterrows():
    node_id = row['Node ID']
    pos_x = row['Position X']
    pos_y = row['Position Y']
    G.add_node(node_id, pos=(pos_x, pos_y))

# Add edges to the graph based on OriginToolID and DestinationToolID from connections_df
for _, row in connections_df.iterrows():
    origin_tool_id = row['OriginToolID']
    destination_tool_id = row['DestinationToolID']
    G.add_edge(origin_tool_id, destination_tool_id)

# Get node positions from the graph
node_positions = nx.get_node_attributes(G, 'pos')

# Draw the graph with node positions
plt.figure(figsize=(10, 6))
nx.draw(G, pos=node_positions, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold', arrows=True)
labels = {(edge[0], edge[1]): f"{edge[0]}->{edge[1]}" for edge in G.edges()}
nx.draw_networkx_edge_labels(G, pos=node_positions, edge_labels=labels, font_color='red')

plt.title("DAG based on Workflow Nodes and Connections")
plt.show()


topological_order = list(nx.topological_sort(G))

print("Topological Order of Nodes:")
print(topological_order)









 
# for connection in connections_list:
#     print(type(connection))

print("Success")