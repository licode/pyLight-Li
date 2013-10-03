from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
import main
import main.job
import os
from main.models import User, History, Job, ToolData, OutputData

import logging
log = logging.getLogger(__name__)

import h5py
import numpy as np
from scipy.misc import imsave

IMAGE_TYPES = ('.png', '.jpg')

class JobView(View):
    """
    """
    template_name = 'job_detail.html'

    def get(self, request, *args, **kwargs):
        
        id = kwargs['id']
        job = main.job.JobWrapper(id)
        tool_name = job.tool.title

        info = []
        info.append("Created: %s %s" % (str(job.db_job.created_date), job.db_job.created_time.strftime("%X")))
        info.append("<br>")
        info.append("Output Size: ")
        context = self.get_context_data()
        context['input_info'] = self.get_inputs(job)
        context['basic_info'] = "\n".join(info)
        context['output_info'] = self.get_outputs(job) 
        context['tool_name'] = tool_name
        context['job_id'] = id
        return render(request, self.template_name, context)
    def get_context_data(self):
        context = {}
        return context
    def get_inputs(self, job):
        datadict = job.inputs()
        content = ["%s: %s<br>" % (item['label'], datadict[item['label']]) for item in job.tool.input]
        return '\n'.join(content)

    def get_outputs(self, job):
        """
        if no outputs are available, return nothing
        otherwise render output according to the file type
        """
        out_url = "/" + os.path.relpath(job.result_directory(), main.ROOT_DIR)
        if job.status() != main.job.JOB_STATUS.SUCCESS:
            return "" 
        outputs = OutputData.objects.filter(job = job.db_job)
        if len(outputs) == 0:
            return ""
        content = []
        for item in outputs:
            filename, ext = os.path.splitext(item.filename)
            if ext in IMAGE_TYPES:
                content.append(item.filename)
                content.append('<br>')
                content.append('<img width="500" src="{0}/{1}"/>'.format(out_url, item.filename))
            else:
                content.append('<a href="{0}/{1}">{1}</a>'.format(out_url, item.filename))
            content.append('<br>')
        return '\n'.join(content)
#         output = output[0]
#         path = os.getcwd()
#         imagefolder = "/static/images/"
#         ofile = path + '/WorkflowPrototype1/Results/' + output.filename
#         
#         out = tool.output[0]
#         if out['type'] == 'h5':
#             path += imagefolder
#             image_list = self.getFile(path, ofile)
#         else:
#             import shutil
#             shutil.copy(ofile, path + imagefolder + output.filename)
#             image_list = [output.filename]
#         content = []
#         for image in image_list:
#             image = imagefolder + image
#             content.append('<img width="500" src="%s"/>' % image)
#             content.append('<br>')
#         return '\n'.join(content)

    def getFile(self, path, h5name):
        file = h5py.File(h5name)
        data = file['/volume']
        
        namelist = []
        for i in [0, 10, 19]:
        	filename = 'tomo_' + str(i) + '.png'
        	namelist.append(filename)
        	imsave(path + filename, data[:,:,i])
        file.close()
        
        return namelist
