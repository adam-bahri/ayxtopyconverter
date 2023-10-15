import pandas as pd
import os
from pandas import json_normalize
import xmltodict
import json
from AYXParser import Workflow, Node, Connection

os.chdir(r'/Users/adambahri/Desktop/ayx-python-converter/files')

# Specify the path to the Alteryx Workflow XML file
xml_file_path = 'SampleWFwithJoinTool.xml'

parsed_data = Workflow(xml_file_path).parseWorkflow()

# Create DataFrames for nodes and connections
nodes_df = pd.DataFrame(parsed_data["nodes"])
connections_df = pd.DataFrame(parsed_data["connections"])

####### Identify Selected Fields, isSelected and potential rename for each field in tools that have "SelectFields" in their configuration #######

# Initialize an empty dictionary to store unique values for each node_id
unique_data = {}

# Loop through the rows of nodes_df
for index, row in nodes_df.iterrows():
    node_id = row['node_id']
    configuration = row['configuration']
    
    # Initialize empty lists for fields and renamed_fields
    fields = []
    renamed_fields = []
    
    # Check if "SelectFields" is in the keys of the nested dictionary
    if 'SelectFields' in configuration:
        select_fields = configuration['SelectFields']['SelectField']
        
        # Check if select_fields is a list
        if isinstance(select_fields, list):
            for field_data in select_fields:
                is_selected = field_data.get('@selected', '')
                field_name = field_data.get('@field', '')
                
                # Only add the field if it's selected
                if is_selected.lower() == 'true' and field_name != "*Unknown":
                    # field_name = field_data.get('@field', '')
                    fields.append(field_name)
                    renamed_field_name = field_data.get('@rename', '')
                    renamed_fields.append(renamed_field_name)
        else:
            # If select_fields is not a list, assume it's a single dictionary
            is_selected = select_fields.get('@selected', '')
            field_name = select_fields.get('@field', '')
            
            # Only add the field if it's selected and not "*Unknown"
            if is_selected.lower() == 'true' and field_name != "*Unknown":
                # field_name = select_fields.get('@field', '')
                fields.append(field_name)
                renamed_field_name = select_fields.get('@rename', '')
                renamed_fields.append(renamed_field_name)
        
        # Append the fields and renamed_fields lists to the unique_data dictionary
        if node_id in unique_data:
            unique_data[node_id]['fields'] = fields
            unique_data[node_id]['renamed_fields'] = renamed_fields
        else:
            unique_data[node_id] = {'fields': fields, 'renamed_fields': renamed_fields}

# Create a DataFrame from the unique_data dictionary
unique_data_df = pd.DataFrame({'node_id': list(unique_data.keys()), 
                               'fields_list': [unique_data[node_id]['fields'] for node_id in unique_data],
                               'renamed_fields_list': [unique_data[node_id]['renamed_fields'] for node_id in unique_data]})

# Merge fields_list and renamed_fields_list with nodes_df

nodes_df = pd.merge(nodes_df, unique_data_df, on="node_id", how="left")

# Output
nodes_df.to_csv("nodes.csv", index=False)
connections_df.to_csv("connections.csv", index=False)
unique_data_df.to_csv("unique_data.csv", index=False)

# Console print to make sure everything was run properly
print("Success")