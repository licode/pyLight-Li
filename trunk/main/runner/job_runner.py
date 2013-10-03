from main.models import ToolData, Job, History, OutputData
import main.job
import json
import Queue
import main.runner
import logging
log = logging.getLogger(__name__)

class JobRunner(object):

    def __init__(self):
        self.file_path = "../static/images/"
        self.output_file = ""
        self.job_queue = Queue.Queue()
        self.runner = main.runner.RunnerThread(self.job_queue)
        self.runner.start()

    def create_job(self, user, tool, form):
        """
        access to database to save data
        """
        job = main.job.JobWrapper()
        job.create(user, tool, form)
        return job

    def submit_job(self, user, tool, form):
        """
        submit a job to the queue
        """
        job = self.create_job(user, tool, form)
        if job.tool.id == "upload":
            job.set_status(main.job.JOB_STATUS.SUCCESS)
            return
        self.job_queue.put(job)
        return
    
    def cancel_job(self, job):
        self.job_queue.put(job)

    def read_jobdata(self, job):
        """
        generate message from a job object
        The message is used for activeMQ
        This function may not be needed
        """
        #tool_name = job.tool.id
        if 'algorithm' in job.params:
            algorithm = job.params['algorithm']
        if 'File' in job.params:
            information = job.params['File']
        else:
            information = ""
        output = job.tool.output[0]
        mode = job.tool.mode
        output_file = output['name'] + str(job.job.id) + "." + output['type']
        OutputData.objects.create(job = job.job, filename = output_file)
        return {"instrument": "HXN",         ###save as dictionary for activeMQ
               "job": algorithm,
               "user": 'user1',
               "passcode": 'pw',
               "input_data_file": "",
               "output_data_file": output_file,
               "information": information,
               "method": "",
               "mode": mode}
