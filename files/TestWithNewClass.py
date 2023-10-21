import pandas as pd
import xmltodict
import json
import os
from AlteryxWorkflow import Workflow, Node

os.chdir("/Users/adambahri/Desktop/ayx-python-converter/files")

TestWorkflow = Workflow("SampleWFwithJoinTool.xml")

# # Output the dictionary to a text file
# output_file_path = "output.txt"

# with open(output_file_path, 'w') as txt_file:
#     txt_file.write(str(TestWorkflow.nodes))

# output_file_path = "nodes_data.json"
# TestWorkflow.output_nodes_to_json(output_file_path)

data = TestWorkflow.nodes

# Parse the data and create Node objects
nodes = []
for node_data in data['Node']:
    node = Node(node_data)
    nodes.append(node)

# Now, you can access information about nodes
for node in nodes:
    print("Node ID:", node.nodeId)
    print("Node Type:", node.nodeType)
    print("Position X:", node.positionX)
    print("Position Y:", node.positionY)
    print("Annotations:", node.annotations)
    print("Configuration:", node.configuration)
    print("Meta Info:", node.metaInfo)
    print("Fields:", node.fields)
    print("Formulas:", node.formulas)
    print("Is Disabled:", node.isDisabled)
    print("----")

nodes_df = TestWorkflow.parse_nodes()

nodes_df.to_csv("nodes_data.csv", index=False)

print("Successfully parsed")