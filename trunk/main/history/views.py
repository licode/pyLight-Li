from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
import main
import main.job
import os
from main.history import HistoryManager
from main.models import User, History, Job, ToolData

JOB_BLOCK_TEMPLATE = \
"""         <div class="jobitem" id="job{id}">
                <div class="jobnumber">{number}.</div>
                <a href="/job/{id}/delete/">
                <img class="delete_icon" src="/static/images/delete.png"/>
                </a>
                <img class="summarytrigger" src="/static/images/arrow_down.png"/>
                <div class="jobtitle"><a href="/job/{id}/" target="frame_main">{title}</a></div>
                <div id="jobstatus">{status}</div>
                <div class="summary" style="display: none">
                    {summary}
                </div>
            </div>"""
        

class HistoryView(View):
    """
    This displays the history panel
    1. get job list from current history
    2. generate html
    """
    template_name = 'history.html'

    def get(self, request, *args, **kwargs):
        if 'id' in kwargs:
            if kwargs['action'] == u'delete':
                self.delete_job(kwargs['id'])
                return HttpResponseRedirect("/history/")
        user = request.user

        hm = HistoryManager(request.user)
        history = hm.get_current_history()
        if history is None:
            return render(request, self.template_name)
        content = self.generate_content(history)
        context = self.get_context_data()
        context['historytitle'] = history.name
        context['content'] = content
        return render(request, self.template_name, context)
    
    def delete_job(self, id):
        job = main.job.JobWrapper(id)
        job.delete()
        
    def generate_content(self, history):
        jobs = Job.objects.filter(history = history).exclude(status = main.job.JOB_STATUS.DELETED).order_by('-id')
        count = len(jobs)
        content = []
        for index, job in enumerate(jobs):
            job_num = str(count - index)
            job_title = main.toolbox.get_tool(job.tool).title
            job_id = str(job.id)
            job_status = main.job.STATUS_LABEL[job.status]
            job_summary = "created: %s %s" % \
                (str(job.created_date), job.created_time.strftime("%X"))
            content.append(JOB_BLOCK_TEMPLATE.format(id = job_id, 
                                                     number = job_num, 
                                                     title = job_title, 
                                                     status = job_status, 
                                                     summary = job_summary))
        return "\n".join(content)

    
    def get_context_data(self):
        context = {}
        return context


