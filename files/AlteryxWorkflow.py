import pandas as pd
import xmltodict
import json

class Node:

    #This constructor is awful
    def __init__(self,node,imageMapping=None, isChild=0, parentContainer=None):
        self.nodeId = node["@ToolID"]
        #print("Created node ID {}".format(self.nodeId))
        self.nodeType = None
        if 'EngineSettings' in node.keys():
            if '@Macro' in node['EngineSettings']:
                if '\\' in node['EngineSettings']['@Macro']:
                    self.nodeType = node['EngineSettings']['@Macro'].split("\\")[-1].split(".")[0]
                else:
                    self.nodeType = node['EngineSettings']['@Macro'].split(".")[0]
            elif '@Plugin' in node["GuiSettings"].keys():
                self.nodeType = node["GuiSettings"]["@Plugin"].split(".")[-1]
                if len(self.nodeType) < 3: # Assume we messed something up and just got a version number 
                    self.nodeType = node["GuiSettings"]["@Plugin"]
            else:
                self.nodeType = 'Macro'  
        elif '@Plugin' in node["GuiSettings"].keys():
            self.nodeType = node["GuiSettings"]["@Plugin"].split(".")[-1]
        else:
            self.nodeType = 'Macro'

        self.positionX = float(node["GuiSettings"]["Position"]['@x'])
        self.positionY = float(node["GuiSettings"]["Position"]['@y'])
        self.width = None 
        if '@width' in node["GuiSettings"]["Position"].keys():
            self.width = float(node["GuiSettings"]["Position"]['@width'])
        self.height = None 
        if '@height' in node["GuiSettings"]["Position"].keys():
            self.height = float(node["GuiSettings"]["Position"]['@height']) 
        self.annotations = None
        if 'AnnotationText' in node["Properties"]["Annotation"].keys():
            self.annotations = node["Properties"]["Annotation"]["AnnotationText"]
        elif 'DefaultAnnotationText' in node["Properties"]["Annotation"].keys():
            self.annotations = node["Properties"]["Annotation"]["DefaultAnnotationText"]
        else:
            self.annotations = ""
        self.configuration = None 
        if 'Configuration' in node["Properties"].keys():
            self.configuration = node["Properties"]["Configuration"] # this will be json stuff
        self.metaInfo = None 
        if 'MetaInfo' in node["Properties"].keys():
            self.metaInfo = node["Properties"]["MetaInfo"]
        self.imageMapping = imageMapping
        self.isChild = int(isChild) 

        self.text = ""
        if self.nodeType == 'TextBox':
            if 'Text' in self.configuration:
                if self.configuration['Text'] is not None:
                    self.text += self.configuration['Text']
        if self.nodeType == 'ToolContainer':
            if 'Caption' in self.configuration:
                if self.configuration['Caption'] is not None:
                    self.text += self.configuration['Caption']

        self.max_X = self.positionX
        if self.width is not None:
            self.max_X += self.width
        
        self.max_Y = self.positionY
        if self.height is not None:
            self.max_Y += self.height

        self.parentContainer = parentContainer 
        self.topContainer = None
        self.nodeDependencies = None
        self.isDisabled = False

        #If container, check if disabled
        if self.nodeType == 'ToolContainer':
            if self.configuration['Disabled']['@value'] == 'True':
                self.isDisabled=True
        
        #If the parent is disabled, the tool is disabled
        if self.parentContainer is not None:
            if self.parentContainer.isDisabled == True:
                self.isDisabled = True

        self.formulas = []
        if self.nodeType=='Formula' or self.nodeType=='LockInFormula':
            if type(self.configuration['FormulaFields']['FormulaField']) == type(dict({'placeholder':dict})):
                #There is one formula
                f = self.configuration['FormulaFields']['FormulaField']
                self.formulas.append("({2}) {0} = {1}".format(f['@field'],f['@expression'],f['@type']))
                #self.formulas.append( {"formula":f['@expression'], "field":f['@field'], "datatype":f['@type']+" - "+f['@size'] } )
            
            if type(self.configuration['FormulaFields']['FormulaField'])==type(list(['placeholder','list'])):
                #there are multiple formulae
                for f in self.configuration['FormulaFields']['FormulaField']:
                    self.formulas.append("({2}) {0} = {1}".format(f['@field'],f['@expression'],f['@type']))
        elif self.nodeType=="Filter":
            if 'Expression' in self.configuration:
                self.formulas.append(self.configuration['Expression'])
        elif self.nodeType=="MultiRowFormula":
            if 'Expression' in self.configuration:
                if self.configuration['UpdateField']['@value']=='True':
                    self.formulas.append("{0} = {1}".format(self.configuration["UpdateField_Name"],self.configuration['Expression']))
                else:
                    self.formulas.append("({2}) {0} = {1}".format(self.configuration["CreateField_Name"],self.configuration['Expression'], self.configuration['CreateField_Type']))
        elif self.nodeType=="MultiFieldFormula":
            if 'Expression' in self.configuration and 'Fields' in self.configuration:
                self.formulas.append(self.configuration['Expression'])
        else:
            self.formulas.append(None)

        #Get Fields and Tables#
        self.fields=[]
        self.fields_list = []
        self.selected_fields = []
        self.renames = []
        self.tables=[]

        if self.nodeType in ['DbFileInput', 'DbFileOutput']:
            if 'File' in self.configuration:
                if '#text' in self.configuration['File']:
                    self.queryHandler(self.configuration['File']['#text'])
            if self.metaInfo is not None:
                if 'RecordInfo' in self.metaInfo:
                    if 'Field' in self.metaInfo['RecordInfo']:
                        #check if list of fields or single field
                        # 6/14/2019 added ' for field names, can use space for delim (except between ')
                        if type(self.metaInfo['RecordInfo']['Field']) == type(list(["a","b"])):
                            for field in self.metaInfo['RecordInfo']['Field']:
                                self.fields.append("({1}) [{0}]".format(field['@name'],field['@type']))
                        else:
                            field = self.metaInfo['RecordInfo']['Field']
                            self.fields.append("({1}) [{0}]".format(field['@name'],field['@type']))

        if self.nodeType in ['AlteryxSelect','AppendFields','Join','JoinMultiple']:
            if 'SelectFields' in self.configuration or 'SelectFields' in self.configuration['SelectConfiguration']['Configuration']:
                if self.nodeType =='AlteryxSelect':
                    SelectedFields = self.configuration['SelectFields']
                elif self.nodeType in ['Join','AppendFields','JoinMultiple']:
                    SelectedFields = self.configuration['SelectConfiguration']['Configuration']['SelectFields']
                for SelectField in SelectedFields:
                    SelectField = SelectedFields['SelectField']
                    if type(SelectField) == type(list([])):
                        for item in SelectField:
                            #print(item)
                            field = ""
                            selected = ""
                            rename = ""
                            size = ""
                            fieldtype=""
                            if '@field' in item:
                                field = item['@field']
                            if '@selected' in item:
                                selected=item['@selected']
                            if '@rename' in item:
                                rename=item['@rename']
                            if '@size' in item:
                                size=item['@size']
                            if '@type' in item:
                                fieldtype=item['@type']
                            appendstring = "[{0}]|".format(field) + "{0}|".format(selected)  + "{0}|".format(size)+ "{0}|".format(rename) + "{0}".format(fieldtype)
                            self.fields.append(appendstring)

                            self.fields_list.append(field)
                            self.selected_fields.append(selected)
                            self.renames.append(rename)
                            #self.fields.append("({1}) [{0}] [{2}] [{3}] [{4}]".format(field,fieldtype,size,selected,rename))
                    else:
                        item=SelectField
                        field = ""
                        selected = ""
                        rename = ""
                        size = ""
                        fieldtype=""
                        if '@field' in item:
                            field = item['@field']
                        if '@selected' in item:
                            selected=item['@selected']
                        if '@rename' in item:
                            rename=item['@rename']
                        if '@size' in item:
                            size=item['@size']
                        if '@type' in item:
                            fieldtype=item['@type']
                        appendstring = "[{0}]|".format(field) + "{0}|".format(selected)  + "{0}|".format(size)+ "{0}|".format(rename) + "{0}".format(fieldtype)
                        self.fields.append(appendstring)

                        self.fields_list.append(field)
                        self.selected_fields.append(selected)
                        self.renames.append(rename)

    def queryHandler(self, s):
        #TODO:
        #Method to determine if something is a query or file
        #Parse fields and tables if query
        self.tables.append(s)

class Workflow:
    def __init__(self, path):
        self.path = path
        self.doc = xmltodict.parse(open(self.path).read())
        self.nodes = dict(self.doc["AlteryxDocument"]["Nodes"])
        self.connections = dict(self.doc["AlteryxDocument"]["Connections"])
        self.properties = dict(self.doc["AlteryxDocument"]["Properties"])
        # self.objects = pd.DataFrame([n.__dict__ for n in self.nodes])
        # # self.objects = self.objects[['nodeId','nodeType',
        #                              'fields','tables',
        #                              'isDisabled','formulas',
        #                              'configuration','annotations',
        #                              'metaInfo','positionX',
        #                              'positionY','width',
        #                              'height','max_X',
        #                              'max_Y','isChild','text']]

        #     # Process nodes
        # self.processed_nodes = []
        # for node_data in self.nodes:
        #     node = Node(node_data)
        #     self.processed_nodes.append(node)

    def output_nodes_to_json(self, output_file):
        nodes_data = []
        for node in self.processed_nodes:
            # Convert each node object to a dictionary before adding to the list
            nodes_data.append(vars(node))
        
        # Output the list of node dictionaries to a JSON file
        with open(output_file, 'w') as json_file:
            json.dump(nodes_data, json_file, indent=4)
    
    # # Method to parse nodes and store attributes in a DataFrame
    # def parse_nodes(self):
    #     nodes_data = self.nodes['Node']
    #     nodes_list = []
    #     for node_data in nodes_data:
    #         node = Node(node_data)
    #         nodes_list.append({
    #             "Node ID": node.nodeId,
    #             "Node Type": node.nodeType,
    #             "Position X": node.positionX,
    #             "Position Y": node.positionY,
    #             "Annotations": node.annotations,
    #             "Configuration": node.configuration,
    #             "Meta Info": node.metaInfo,
    #             "Fields": node.fields,
    #             "Formulas": node.formulas,
    #             "Is Disabled": node.isDisabled
    #         })
        
    #     # Create a DataFrame from the list of node attributes
    #     nodes_df = pd.DataFrame(nodes_list)
    #     return nodes_df

    # Method to parse nodes and store attributes in a DataFrame
    def parse_nodes(self):
        nodes_data = self.nodes['Node']
        nodes_list = []
        # List to store all unique keys found in node.configuration
        all_keys = set()

        # Parse nodes and extract configuration keys
        for node_data in nodes_data:
            node = Node(node_data)
            if node.configuration:
                # Update all_keys set with keys found in node.configuration
                all_keys.update(node.configuration.keys())
            
            nodes_list.append({
                "Node ID": node.nodeId,
                "Node Type": node.nodeType,
                "Position X": node.positionX,
                "Position Y": node.positionY,
                "Annotations": node.annotations,
                "Meta Info": node.metaInfo,
                "Fields": node.fields,
                "Formulas": node.formulas,
                "Is Disabled": node.isDisabled,
                "Fields_List": node.fields_list,
                "Selected Fields": node.selected_fields,
                "Renames": node.renames,
                **node.configuration  # Include all keys found in node.configuration
            })

        # Create DataFrame columns for each unique key found in node.configuration
        columns = ["Node ID", "Node Type", "Position X", "Position Y", 
                        "Annotations", "Meta Info", "Fields", "Formulas", "Is Disabled", "Fields_List", "Selected Fields", "Renames"]
        new_columns = list(all_keys)

        columns.extend(new_columns)

        nodes_df = pd.DataFrame(nodes_list, columns=columns)

        return nodes_df

# # Example usage
# TestWorkflow = Workflow("SampleWFwithJoinTool.xml")

