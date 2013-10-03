import main

from django.http import HttpResponse
import json
import logging
log = logging.getLogger(__name__)

def new_module(request):
    tool = main.toolbox.get_tool(request.GET['tool_id'])
    data = {
        'type': 'tool',
        'name':  tool.title,
        'tool_id': tool.id,
        'tool_state': "",
        'tooltip': "tooltip",
        'data_inputs': get_tool_inputs(tool),
        'data_outputs': get_tool_outputs(tool),
        'form_html': "",
        'annotation': ""
        }
    data = json.dumps(data)
    return HttpResponse(data, content_type='application/json')

def get_tool_inputs(tool):
    input_list = [{'label': item['label'],
                   'name': 'input%s' % i,
                   'extensions': [item['suffix']],
                   'multiple': False} \
                  for i, item in enumerate(tool.input) if item['type'] == 'file_select']
    return input_list

def get_tool_outputs(tool):
    output_list = [{'label': 'output%s' % i, 
                    'name': item['name'] + '.' + item['type'], 
                    'extensions': ['input']} \
                   for i, item in enumerate(tool.output)]
    return output_list