from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
import datetime
from django.utils.timezone import utc
import json
import main
import job
from main.models import Job
import logging
log = logging.getLogger(__name__)

CHECK_PERIOD = 10

class FrameView(View):
    def get(self, request, *args, **kwargs):
        name = kwargs['name']
        template_name = '';
        if name == 'welcome':
            template_name = 'welcome.html'
        elif name == "tool_menu":
            template_name = 'tool_menu.html'
        return render(request, template_name, self.get_context_data())
    def get_context_data(self):
        context = {'menu': main.toolbox.toolbox.content}
        return context
 
class HistoryView(TemplateView):
    """
    display history panel
    """
    template_name = "history.html"
    def get_context_data(self, **kwargs):
        pass
    
class MainView(TemplateView):
    """
    website main page
    """
    template_name = "main.html"
    def get_context_data(self, **kwargs):
        return {'user': self.request.user}
    
class AnalyzeView(TemplateView):
    """
    main page for analyzing data function - single tool execution
    """
    template_name = "menu_base.html"
    def get_context_data(self, **kwargs):
        return {'src': '/frame/welcome/', 'selected': 'menu_tool'}
    
class WorkflowView(TemplateView):
    """
    workflow main page
    """
    template_name = "workflow.html"
    def get_context_data(self, **kwargs):
        return {'selected': 'menu_workflow', 'menu': main.toolbox.toolbox.workflow_content}

class RunView(TemplateView):
    """
    Right now it just shows a job created message
    """
    template_name = "run_notice.html"

def get_status(request):
    """return updated status of jobs in the history"""
    import main.history
    hm = main.history.HistoryManager(request.user)
    history = hm.get_current_history()
    count = Job.objects.filter(history=history).exclude(status__gte = job.JOB_STATUS.SUCCESS).count()
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    jobs = Job.objects.filter(history=history).filter(last_save_datetime__gte = now - 
                              datetime.timedelta(seconds = CHECK_PERIOD))
    log.info(jobs)
    if count == 0:
        status = {'done': 1}
    else:
        status = {'done': 0}
    update_dict = {}
    if jobs:
        for job_ in jobs:
            update_dict['job%d' % job_.id] = job.STATUS_LABEL[job_.status]
    status['list'] = update_dict
    status = json.dumps(status)
    log.info("Status response: %s", status)
    return HttpResponse(status, content_type='application/json')



    
class VisualizationView(TemplateView):
    """
    Right now it just shows a job created message
    """
    template_name = "visualization.html"
    
class HelpView(TemplateView):
    """
    Right now it just shows a job created message
    """
    template_name = "help.html"    
