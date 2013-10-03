from django.views.generic import TemplateView, View
from django.shortcuts import render, render_to_response
from django.http import HttpResponseRedirect
from django import forms
import main
import main.job
import os
import json
import main.runner.job_runner


FIELD_TYPES = {
    "float": forms.FloatField,
    "int": forms.IntegerField,
    "file": forms.FileField,
    "select": forms.ChoiceField,
    "file_select": forms.ChoiceField,
    "char": forms.CharField
}

def get_data_source(extension):
    """
    This function generate a list of choices used in the tool's select field as data source
    """
    import glob
    files = glob.glob(main.DATA_SOURCE_DIR + "*." + extension)
    source = [(f, os.path.basename(f)) for f in files]
    return source

def generate_form(tool):
    """
    This function generate a class that inherits forms.Form. This class represents
    the form used by the incoming 'tool'.
    """
    fields = {}
    for item in tool.input:
        _type = item["type"]
        _label = item["label"]
        _choices = None
        if _type == "file_select":
            _choices = get_data_source(item["suffix"])
        elif _type == "select":
            _choices = item["options"]
            _choices = [(item, item) for item in _choices]
        if _choices:
            fields[_label] = FIELD_TYPES[_type](label = _label, choices = _choices)           
        else:
            fields[_label] = FIELD_TYPES[_type](label = _label)            
    return type('MyForm', (forms.Form,), fields)

def handle_uploaded_file(f):
    with open(main.DATA_SOURCE_DIR + str(f), 'wb') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

JOB_RUNNER = main.runner.job_runner.JobRunner()

class ToolView(View):
    template_name = 'tool_run.html'
    template_name0 = "login_simple.html"
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if len(user.username)==0:
            return render(request, self.template_name0)
        if 'rerun' in kwargs:
            j = main.job.JobWrapper(kwargs['id'])
            tool = j.tool
            request.session['_initials'] = j.inputs()
            return HttpResponseRedirect("/tool/%s" % tool.id)
        initials = request.session.get('_initials') 
        tool = main.toolbox.get_tool(kwargs['id'])
        form_class = generate_form(tool)
        context = self.get_context_data()
        if initials:
            del request.session['_initials']
            context['form'] = form_class(initials)
        else:
            context['form'] = form_class()
        context['tool_name'] = tool.title
        context['tool_tutorial'] = tool.config['tutorial']
	return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        tool = main.toolbox.get_tool(kwargs['id'])
        form_class = generate_form(tool)            
        form = form_class(request.POST,request.FILES)
        if form.is_valid():
            myform = form.cleaned_data
            if tool.id == "upload":
                #need redesign in the future
                #uploaded file names could be already used
                #file should be renamed and original file name is stored as a label
                #besides, this job also need to be recorded in database
                handle_uploaded_file(request.FILES['File'])
            
            JOB_RUNNER.submit_job(request.user, tool, myform)
            return HttpResponseRedirect(request.get_full_path() + "run/")
        
        context = self.get_context_data()
        context['form'] = form
        context['tool_name'] = tool.title
        return render(request, self.template_name, context)

    def get_context_data(self):
        context = {}
        return context


class Tool:
    def __init__(self, config_file):
        self.id = None
        self.input = None
        self.output = None
        self.command = None
        self.title = None
        self.directory = os.path.dirname(os.path.abspath(config_file))
        config = json.load(open(config_file))
        self.config = config
        self.load(config)
    def load(self, config):
        if "id" in config:
            self.id = config["id"]

        if "input" in config:
            self.input = config["input"]
            #self.parse_input(config["input"])

        if "output" in config:
            self.output = config["output"]
            #self.parse_output(config["output"])

        if "command" in config:
            self.command = config["command"]
            
        if "mode" in config:
            self.mode = config["mode"]

        if "title" in config:
            self.title = config["title"]

