class ConnectionElement(object):
    def __init__(self, connection, nodes):
        self.origin_tool_id = int(connection.find("Origin").attrib.get("ToolID"))
        self.origin_tool_connection_name = connection.find("Origin").attrib.get("Connection")
        self.destination_tool_id = int(connection.find("Destination").attrib.get("ToolID"))
        self.destination_tool_connection_name = connection.find("Destination").attrib.get("Connection")
        self.origin_tool = next((item['Tool'] for item in nodes if item['Tool ID'] == self.origin_tool_id), None)
        self.destination_tool = next((item['Tool'] for item in nodes if item['Tool ID'] == self.destination_tool_id), None)

        self.data = {
            "OriginToolID" : self.origin_tool_id,
            "OriginTool" : self.origin_tool,
            "OriginToolConnectionName" : self.origin_tool_connection_name,
            "DestinationToolID" : self.destination_tool_id,
            "DestinationTool" : self.destination_tool,
            "DestinationToolConnectionName" : self.destination_tool_connection_name
        }
