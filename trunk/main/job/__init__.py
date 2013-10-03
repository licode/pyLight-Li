from main.models import User, History, Job, ToolData, OutputData
import datetime
import urllib2
import shutil
import urlparse
import os
import main
from main.history import HistoryManager
import logging
log = logging.getLogger(__name__)

STATUS_LABEL = {0: 'Created', 
              1: 'Ready',
              2: 'Queued',
              3: 'Running',
              4: "Succeeded",
              5: "Failed",
              6: "Deleted"}
class JOB_STATUS:
    CREATED, READY, QUEUED, RUNNING, SUCCESS, FAIL, DELETED = range(7)


class JobWrapper:
    def __init__(self, id = -1):
        if id != -1:
            self.db_job = Job.objects.get(id = id)
            self.tool = main.toolbox.get_tool(self.db_job.tool)
            #more to go
        
    def update_status(self):
        status = self.runner.get_status()
        self.set_status(status)
        if status == JOB_STATUS.SUCCESS:
            self.finish()
        
    def create(self, user, 
               tool, form):
        hm = HistoryManager(user)
        self.history = hm.get_current_history()
        self.tool = tool
        self.db_job = Job.objects.create(history = self.history, 
                                      tool = tool.id, 
                                      status = JOB_STATUS.READY)
        self.params = form
        options = [self.tool.command]
        for item in tool.input:
            key = item["label"]
            val = str(form[key])
            options.append(val)
            ToolData.objects.create(job=self.db_job,
                                    data_key=key,
                                    data_val=val)
                        
        self.record_outputs(form, options)
        self.command = " ".join(options)
        log.info(self.command)
        import main.runner
        if hasattr(tool, 'mode'):
            self.runner = main.runner.create_runner(tool.mode, self)
        
    def run(self):
        if hasattr(self, "runner"):
            self.runner.run()
            
    def result_directory(self):
        """eventually each job will have its own directory"""
        if not hasattr(self, 'result_dir'):
            self.result_dir = main.DATA_SOURCE_DIR
        return self.result_dir
        
    def finish(self):
        outputs = OutputData.objects.filter(job = self.db_job)
        for item in outputs:
            filename = self.tool.directory + "/" + item.filename
            if not os.path.isfile(filename):
                self.set_status(JOB_STATUS.FAIL)
                continue
            shutil.move(filename, self.result_directory())

    def inputs(self):
        results = ToolData.objects.filter(job=self.db_job)
        return dict([(item.data_key, item.data_val) for item in results])
    
    def record_outputs(self, form, options):
        for item in self.tool.output:
            assert('type' in item)
            if item['type'] != 'input':
                filename = item['name'] + str(self.db_job.id) + "." + item['type']
                options.append(filename)
            else:
                assert('index' in item)
                input_item = self.tool.input[item['index']]
                if item['name'] == 'url':
                    filename = self.get_filename_from_url(form[input_item['label']])
                else:
                    filename = str(form[input_item['label']])
            log.info(filename)
            OutputData.objects.create(job = self.db_job, filename = filename)

    def get_filename_from_url(self, url):
        openUrl = urllib2.urlopen(urllib2.Request(url))
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info()['Content-Disposition'].split(';')))
            if 'filename' in cd:
                filename = cd['filename'].strip("\"'")
                if filename: 
                    return filename
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse.urlsplit(openUrl.url)[2])
    
    def set_status(self, status):
        assert(self.db_job)
        if self.db_job.status != status:
            self.db_job.status = status
        self.db_job.save()
    
    def status(self):
        return self.db_job.status
    
    def jobid(self):
        return self.db_job.id
        
    def delete(self):
        from main.tool.views import JOB_RUNNER
        old_status = self.db_job.status
        self.set_status(JOB_STATUS.DELETED)
        if old_status not in (JOB_STATUS.SUCCESS, JOB_STATUS.FAIL):
            JOB_RUNNER.cancel_job(self)
        
    def display(self, request):
        pass
    
