import xmltodict
import json 
import os
import pandas as pd
import re

class Node:

    def __init__(self,node,imageMapping=None, isChild=0, parentContainer=None):
        self.nodeId = node["@ToolID"]
        self.nodeType = None
        if 'EngineSettings' in node.keys():
            if '@Macro' in node['EngineSettings']:
                if '\\' in node['EngineSettings']['@Macro']:
                    self.nodeType = node['EngineSettings']['@Macro'].split("\\")[-1].split(".")[0]
                else:
                    self.nodeType = node['EngineSettings']['@Macro'].split(".")[0]
            elif '@Plugin' in node["GuiSettings"].keys():
                self.nodeType = node["GuiSettings"]["@Plugin"].split(".")[-1]
                if len(self.nodeType) < 3:
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
            self.configuration = node["Properties"]["Configuration"]
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
        self.tables=[]
        if self.nodeType in ['DbFileInput', 'DbFileOutput']:
            if 'File' in self.configuration:
                if '#text' in self.configuration['File']:
                    self.queryHandler(self.configuration['File']['#text'])
            if self.metaInfo is not None:
                if 'RecordInfo' in self.metaInfo:
                    if 'Field' in self.metaInfo['RecordInfo']:
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



class Connection:
    
    def __init__(self, con, nodelist, connectionName=None, isWireless=False):
        self.originNodeId = con['Origin']['@ToolID']
        self.destinationNodeId = con['Destination']['@ToolID']
        self.connectionName = connectionName
        self.isWireless = isWireless
        self.originConnection = None
        if '@Connection' in con['Origin'].keys():
            self.originConnection=con['Origin']['@Connection']
        self.destinationConnection = None
        if '@Connection' in con['Destination'].keys():
            self.destinationConnection = con['Destination']['@Connection']

        for n in nodelist:
            if n.nodeId == self.originNodeId:
                self.originNode = n
            if n.nodeId == self.destinationNodeId:
                self.destinationNode = n
        
    #Method to get X,Y coods of origin node and destination node
    def getCoords(self):
        x1 = self.originNode.positionX+42
        y1 = self.originNode.positionY+18
        x2 = self.destinationNode.positionX
        y2 = self.destinationNode.positionY+18
        return [x1,y1,x2,y2]


class Workflow:

    def __init__(self, filePath):
        self.filePath = filePath
        self.nodes = []
        self.connections = []

    def parseWorkflow(self):
        try:
            with open(self.filePath) as fd:
                dat = fd.read()
                self.doc = xmltodict.parse(dat)
        except:
            with open(self.filePath, encoding="utf8") as fd:
                dat = fd.read()
                self.doc = xmltodict.parse(dat)

        workflow_data = {
            "nodes": self.collectNodes(self.doc["AlteryxDocument"]["Nodes"]),
            "connections": self.collectConnections(self.doc["AlteryxDocument"]["Connections"]),
        }

        return workflow_data

    def collectConnections(self, connections):
        connection_list = []

        def getConnection(con):
            name = con.get('@name')
            wireless = con.get('@Wireless', 'False')
            origin_tool_id = con['Origin']['@ToolID']
            destination_tool_id = con['Destination']['@ToolID']
            
            connection_data = {
                "name": name,
                "wireless": wireless,
                "origin_tool_id": origin_tool_id,
                "destination_tool_id": destination_tool_id,
            }

            connection_list.append(connection_data)

        if "Connection" in connections:
            if isinstance(connections["Connection"], list):
                for con in connections["Connection"]:
                    getConnection(con)
            else:
                getConnection(connections["Connection"])

        return connection_list

    def collectNodes(self, nodes):
        node_list = []

        def getNodeData(node, level, parent_container=None):
            node_id = node["@ToolID"]
            node_type = self.getNodeType(node)
            position_x = float(node["GuiSettings"]["Position"]["@x"])
            position_y = float(node["GuiSettings"]["Position"]["@y"])
            width = float(node["GuiSettings"]["Position"].get("@width", 0))
            height = float(node["GuiSettings"]["Position"].get("@height", 0))
            annotations = self.getNodeAnnotations(node)
            configuration = node["Properties"].get("Configuration")
            meta_info = node["Properties"].get("MetaInfo")
            config_keys = configuration.keys()

            node_data = {
                "node_id": node_id,
                "node_type": node_type,
                "position_x": position_x,
                "position_y": position_y,
                "width": width,
                "height": height,
                "annotations": annotations,
                "configuration": configuration,
                "configuration keys" : config_keys,
                "meta_info": meta_info,
                "level": level,
                "parent_container": parent_container,
            }

            node_list.append(node_data)

            if "ChildNodes" in node and "Node" in node["ChildNodes"]:
                child_nodes = node["ChildNodes"]["Node"]
                if isinstance(child_nodes, list):
                    for child_node in child_nodes:
                        getNodeData(child_node, level + 1, node_id)
                else:
                    getNodeData(child_nodes, level + 1, node_id)

        if "Node" in nodes:
            if isinstance(nodes["Node"], list):
                for node in nodes["Node"]:
                    getNodeData(node, 0)
            else:
                getNodeData(nodes["Node"], 0)

        return node_list

    def getNodeType(self, node):
        if "EngineSettings" in node:
            if "@Macro" in node["EngineSettings"]:
                macro_path = node["EngineSettings"]["@Macro"]
                if "\\" in macro_path:
                    return macro_path.split("\\")[-1].split(".")[0]
                else:
                    return macro_path.split(".")[0]
            elif "@Plugin" in node["GuiSettings"]:
                return node["GuiSettings"]["@Plugin"].split(".")[-1]
            else:
                return "Macro"
        elif "@Plugin" in node["GuiSettings"]:
            return node["GuiSettings"]["@Plugin"].split(".")[-1]
        else:
            return "Macro"

    def getNodeAnnotations(self, node):
        if "Properties" in node and "Annotation" in node["Properties"]:
            annotation = node["Properties"]["Annotation"]
            if "AnnotationText" in annotation:
                return annotation["AnnotationText"]
            elif "DefaultAnnotationText" in annotation:
                return annotation["DefaultAnnotationText"]
        return ""

# Example usage:
# workflow = Workflow("your_workflow_file.xml")
# workflow_data = workflow.parseWorkflow()

