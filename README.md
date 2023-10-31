# Alteryx Workflow to Python Code

This project's purpose is to convert Alteryx workflows into Python scripts. The project is still in the early stages of development.

Credits to the owners of these 2 repos that helped me get started with this project:

- https://gitlab.com/keyrus-us/public/alteryx_auto_doc_revamp/tree/master
- https://github.com/msdilli7/Alteryx2Spark/tree/main

AYXParser.py is actually a modified version of the original code found in https://gitlab.com/keyrus-us/public/alteryx_auto_doc_revamp/tree/master


# Update 2023-10-31

Updated the files using xml.etree.ElementTree instead of xmltodict to parse the workflow XML.

Thanks to https://github.com/shiv-io/Alteryx-Metadata-Parser for the ideas.