import xmltodict
import json 
import os
import pandas as pd
import re

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
                        #self.fields.append("({1}) [{0}] [{2}] [{3}] [{4}]".format(field,fieldtype,size,selected,rename))

    def queryHandler(self, s):
        #TODO:
        #Method to determine if something is a query or file
        #Parse fields and tables if query
        self.tables.append(s)
        



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
        #
        # print("Created connection from node {0} to node {1}".format(self.originNode.nodeId,self.destinationNode.nodeId))

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
        self.nodes = [] # This is a list of nodes
        self.connections = [] # This is a list of connections

    def parseWorkflow(self):
        try:
            with open(self.filePath) as fd:
                # fd.readline() # Drop the first line #
                dat = fd.read()
                self.doc = xmltodict.parse(dat)
        except:
            with open(self.filePath, encoding="utf8") as fd:
                # fd.readline() # Drop the first line #
                dat = fd.read()
                self.doc = xmltodict.parse(dat)

        # Determine Canvas Size #
        # Collect Nodes #
        if self.doc["AlteryxDocument"]["Nodes"] is not None:
            self.collectNodes(self.doc["AlteryxDocument"]["Nodes"],self.nodes)
            self.max_x = max(int(max([node.max_X for node in self.nodes]) + 200), 500)
            self.max_y = max(int(max([node.max_Y for node in self.nodes]) + 200), 300)
            self.max_level = max([node.isChild for node in self.nodes])
        else:
            self.max_x = 500
            self.max_y = 300
            self.max_level = 0

        #Get Connections
        if self.doc["AlteryxDocument"]["Connections"] is not None:
            self.collectConnections(self.doc["AlteryxDocument"]["Connections"],self.nodes,self.connections)

        return self
    
        # Method to collect connections #
    def collectConnections(self, connections, nodelist, li):

        def getConnection(con, li=li,nodelist=nodelist):
            name = None
            if '@name' in con.keys():
                name=con['@name']
            wireless = False
            if '@Wireless' in con.keys():
                wireless=True
            connection = Connection(con,nodelist,name,wireless)
            li.append(connection)


        if len(connections['Connection'])>1 and type(connections['Connection'])==type(list(['placeholder','list'])):
            for con in connections["Connection"]:
                getConnection(con)

        elif len(connections['Connection'])==1 or type(connections['Connection'])==type(dict({'placeholder':'dict'})):
            con = connections["Connection"]
            getConnection(con)

        else:
            #No connections exist
            pass  
    
        # Method to collect Nodes #
    def collectNodes(self, nodes, li, level = 0, parentContainer = None):
        if nodes is not None:
            if len(nodes["Node"])>1 and type(nodes["Node"])==type(list(["placeholder","list"])):
                for node in nodes["Node"]:
                    n = Node(node,isChild=level, parentContainer=parentContainer)
                    li.append(n)
                    if '@Plugin' in node["GuiSettings"].keys():
                        #Recursive Container Search
                        if "ToolContainer" in node["GuiSettings"]["@Plugin"] and "ChildNodes" in node.keys():
                            self.collectNodes(node["ChildNodes"],li,level = level + 1, parentContainer=n)
            elif len(nodes["Node"])==1 or type(nodes["Node"])==type({"placeholder":"dictionary"}):
                node = nodes["Node"]
                #print(node)
                n = Node(node,isChild=level, parentContainer=parentContainer)
                li.append(n)
                if '@Plugin' in node["GuiSettings"].keys():
                    #Recursive Container Search
                    if "ToolContainer" in node["GuiSettings"]["@Plugin"] and "ChildNodes" in node.keys():
                        self.collectNodes(node["ChildNodes"],li,level = level + 1, parentContainer=n)
            else:
                #No Node Found
                pass
