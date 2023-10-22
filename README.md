# Alteryx Workflow to Python Code

This project's purpose is to convert Alteryx workflows into Python scripts. The project is still in the early stages of development.

Credits to the owners of these 2 repos that helped me get started with this project:

- https://gitlab.com/keyrus-us/public/alteryx_auto_doc_revamp/tree/master
- https://github.com/msdilli7/Alteryx2Spark/tree/main

AlteryxWorkflow.py is actually a modified version of the original code found in https://gitlab.com/keyrus-us/public/alteryx_auto_doc_revamp/tree/master

Thanks to https://github.com/msdilli7/Alteryx2Spark/tree/main for the code structure of the DAG. The goal is to figure out the order of transformations based on this DAG to generate the equivalent Python code in the correct order (each node with no incoming edge in the DAG needs to have a separate data, e.g. two Input Tools in a workflow will need two Pandas DataFrame or any other suitable object in the equivalent Python code)
