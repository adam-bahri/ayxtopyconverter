# # import pandas as pd
# # import os
# # from pandas import json_normalize
# # import xmltodict
# # import json
# # from AYXParser import Workflow, Node, Connection

# # os.chdir(r'/Users/adambahri/Desktop/ayx-python-converter/files')

# # # Specify the path to the Alteryx Workflow XML file
# # xml_file_path = 'DIM BU.xml'

# # parsed_data = Workflow(xml_file_path).parseWorkflow()

# # nodes_data = parsed_data["nodes"]

# # first_tool = nodes_data[0]

# # print(first_tool["configuration"]["Caption"])

# # # nodes_df = pd.DataFrame(parsed_data["nodes"])

# # # print(nodes_df)

# import pandas as pd

# # Sample data for fields, selected, and rename
# fields = ['temp_change_Right_Employee ID', 'temp_change_Right_Staff_ID', 'Right_GUID', 'Right_Work Email', 'Right_Worker', 'Right_First Name']
# selected = [True, True, False, False, False, True]
# rename = ['TestField1', '', '', '', '', 'TEST_First_Name']

# # Sample DataFrame df
# data = {
#     'temp_change_Right_Employee ID': [1, 2, 3],
#     'temp_change_Right_Staff_ID': [4, 5, 6],
#     'Right_GUID': [7, 8, 9],
#     'Right_Work Email': [10, 11, 12],
#     'Right_Worker': [13, 14, 15],
#     'Right_First Name': [16, 17, 18]
# }

# df = pd.DataFrame(data)

# # Select and rename fields
# selected_fields = [field for field, is_selected in zip(fields, selected) if is_selected]
# renamed_fields = [new_name if new_name != '' else field for field, new_name in zip(selected_fields, rename)]
# filtered_df = df[selected_fields]
# filtered_df.columns = renamed_fields

# print(1, selected_fields)
# print(2, renamed_fields)

# print(filtered_df)

# import pandas as pd

# # Sample data for fields, selected, and rename
# fields = ['temp_change_Right_Employee ID', 'temp_change_Right_Staff_ID', 'Right_GUID', 'Right_Work Email', 'Right_Worker', 'Right_First Name']
# selected = [True, True, False, False, False, True]
# rename = ['TestField1', '', '', '', '', 'TEST_First_Name']

# # Sample DataFrame df
# data = {
#     'temp_change_Right_Employee ID': [1, 2, 3],
#     'temp_change_Right_Staff_ID': [4, 5, 6],
#     'Right_GUID': [7, 8, 9],
#     'Right_Work Email': [10, 11, 12],
#     'Right_Worker': [13, 14, 15],
#     'Right_First Name': [16, 17, 18]
# }

# df = pd.DataFrame(data)

# # Select fields where selected is True
# selected_fields = [field for field, is_selected in zip(fields, selected) if is_selected]

# print(selected_fields)

# # Rename selected fields based on the rename list
# renamed_fields = [rename_value if is_selected and rename_value != '' else field for field, is_selected, rename_value in zip(fields, selected, rename)]

# print(renamed_fields)

# # Filter the DataFrame based on selected fields and rename columns
# filtered_df = df[selected_fields]
# filtered_df.columns = renamed_fields

import pandas as pd

# Sample data for fields, selected, and rename
fields = ['temp_change_Right_Employee ID', 'temp_change_Right_Staff_ID', 'Right_GUID', 'Right_Work Email', 'Right_Worker', 'Right_First Name']
selected = [True, True, False, False, False, True]
rename = ['TestField1', '', '', '', '', 'TEST_First_Name']

# Sample DataFrame creation (replace this with your actual DataFrame)
data = {
    'temp_change_Right_Employee ID': [1, 2, 3],
    'temp_change_Right_Staff_ID': [4, 5, 6],
    'Right_GUID': [7, 8, 9],
    'Right_Work Email': ['a@example.com', 'b@example.com', 'c@example.com'],
    'Right_Worker': ['X', 'Y', 'Z'],
    'Right_First Name': ['Alice', 'Bob', 'Charlie']
}

df = pd.DataFrame(data)

# Filter columns based on the 'selected' list
selected_fields = [fields[i] for i in range(len(fields)) if selected[i]]

print(selected_fields)

# Rename selected columns based on the 'rename' list
rename_dict = {fields[i]: rename[i] for i in range(len(fields)) if selected[i] and rename[i] != ''}
print(rename_dict)

df = df[selected_fields].rename(columns=rename_dict)

print(df)

