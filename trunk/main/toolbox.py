import json
from my_test import tool_config
from main.tool.views import Tool

class ToolBox:
    def __init__(self, tool_dir):
        self._tool_dir = tool_dir
        self.init_tools()
    
    def init_tools(self):
        self.tools = {}
        self.tool_index = {} # this is an assistant dictionary
        self.content = "\n".join(self.parse(tool_config.menu, self.analyze_link))
        self.workflow_content = "\n".join(self.parse(tool_config.menu, self.workflow_link))
        self.tool_index.clear()
    
    def parse(self, menu, link_method):
        content = []
        for item in menu:
            if type(item) == str:
                content.append("<div class='divisionTitle'>%s</div>" % item)
            else:
                content.append("<div class='sectionTitle'><a href='#'>{0}</a>".format(item[0]))
                content.append("<div class='sectionContent'>")
                for toolpair in item[1]:
                    tool = self.load_config(toolpair[1])
                    content.append(link_method(tool.id, toolpair[0]))
                    content.append("<br>")
                content.append("</div>")
                content.append("</div>")
        return content
    
    def workflow_link(self, tool_id, tool_name):
        return "<a href='#' onclick=\"add_node_for_tool('{0}','{1}')\">{1}</a>".format(tool_id, tool_name)
    
    def analyze_link(self, tool_id, tool_name):
        return "<a target='frame_main' href = '/tool/{0}'>{1}</a>".format(tool_id, tool_name)
    
    def parse1(self, menu, content, step):
        #not use any more
        if not menu:
            return
        if step == 0:
            content.append("<ul class='treeview' id='tree'>")
        else:
            content.append("<ul style='display: none;'>")
        for item in menu:
            if type(item) == str:
                content.append("<li>" + self.fontwrap(step, item) + "</li>")
            else:
                name = item[0]
                if type(item[1]) == str:
                    tool = self.load_config(item[1])
                    content.append("<li><a target='frame_main' href = '/tool/" + tool.id + "'>" + self.fontwrap(step, name) + "</a></li>")
                else:
                    content.append("<li class='expandable'>")
                    content.append("<span>" + self.fontwrap(step, name) + "</span>")
                    self.parse(item[1], content, step + 1)
                    content.append("</li>")
        content.append("</ul>")
    def fontwrap(self, step, label):
        #not use any more
        return "<h" + str(step + 2) + ">" + label + "</h" + str(step + 2) + ">"
    
    def load_config(self, config_file):
        #avoid multiple loading of same tool
        if config_file in self.tool_index:
            return self.tool_index[config_file]
        tool = Tool(self._tool_dir + config_file)
        self.tools[tool.id] = tool
        self.tool_index[config_file] = tool
        return tool


toolbox = ToolBox("tools/")

def get_tool(id):
    return toolbox.tools[id]
