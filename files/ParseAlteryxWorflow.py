
import time
import xml.etree.ElementTree as ET
from Node import NodeElement
from Connection import ConnectionElement
import csv
from shutil import copyfile
import sys
import networkx as nx
import matplotlib.pyplot as plt

start_time = time.time()

# Input file
file = "DIM BU.xml"
assert len(file.split('.')) > 1, 'Input file must have an extension'
file_ext = file.split('.')[-1]
assert file_ext == 'xml' or file_ext == 'yxmd', 'Input file must be .xml or .yxmd'
if file_ext == 'yxmd':
    xml = file.split('.')[0] + '.xml'
    copyfile(file, xml)
    tree = ET.parse(xml)
else:
    tree = ET.parse(file)

# Nodes output file
nodes_output_file_name = "nodes_output.csv"
assert len(nodes_output_file_name.split('.')) > 1, 'Output file must have an extension'
nodes_output_file_ext = nodes_output_file_name.split('.')[-1]
assert nodes_output_file_ext == 'csv', 'Output file must be .csv'

# Connections output file
connections_output_file_name = "connections_output.csv"
assert len(connections_output_file_name.split('.')) > 1, 'Output file must have an extension'
connections_output_file_ext = connections_output_file_name.split('.')[-1]
assert connections_output_file_ext == 'csv', 'Output file must be .csv'


# Parse the workflow file
root = tree.getroot()

# Iterate over Node elements
nodes_list = [NodeElement(x).data for x in root.iter('Node')]

nodes_keys = nodes_list[0].keys()


# Iterate over Connection elements
connections_list = [ConnectionElement(x, nodes = nodes_list).data for x in root.iter('Connection')]

connections_keys = connections_list[0].keys()

print("Nodes_list", nodes_list)
# print("Conns_list", connections_list)

# Create a directed graph
G = nx.DiGraph()

# Add nodes to the graph with position from nodes_df
for node in nodes_list:
    node_id = node['Tool ID']
    pos_x = node['x']
    pos_y = node['y']
    G.add_node(node_id, pos=(pos_x, pos_y))

# Add edges to the graph based on OriginToolID and DestinationToolID from connections_df
for connection in connections_list:
    origin_tool_id = connection['OriginToolID']
    destination_tool_id = connection['DestinationToolID']
    G.add_edge(origin_tool_id, destination_tool_id)

# Get node positions from the graph
node_positions = nx.get_node_attributes(G, 'pos')

# Draw the graph with node positions
plt.figure(figsize=(10, 6))
nx.draw(G, pos=node_positions, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold', arrows=True)
labels = {(edge[0], edge[1]): f"{edge[0]}->{edge[1]}" for edge in G.edges()}
nx.draw_networkx_edge_labels(G, pos=node_positions, edge_labels=labels, font_color='red')

# plt.title("DAG based on Workflow Nodes and Connections")
# plt.show()


topological_order = list(nx.topological_sort(G))

print("Topological Order of Nodes:")
print(topological_order)

print("=" * 50)

# Create a new key-value pair "Order" for each element in nodes_list
for node in nodes_list:
    tool_id = node.get('Tool ID')
    if tool_id in topological_order:
        order = topological_order.index(tool_id)
        node['Order'] = order

nodes_list = sorted(nodes_list, key=lambda x: x['Order'])

for id in topological_order:
    print("ID", id)
    print("Tool", next((item['Tool'] for item in nodes_list if item['Tool ID'] == id), None))
    print("=" * 50)

# Output Nodes info
with open(nodes_output_file_name, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, nodes_keys)
    dict_writer.writeheader()
    dict_writer.writerows(nodes_list)

# Output Connections info

with open(connections_output_file_name, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, connections_keys)
    dict_writer.writeheader()
    dict_writer.writerows(connections_list)

end_time = time.time()

elapsed = end_time - start_time

print(f"Elapsed time: {elapsed:.2f} seconds")