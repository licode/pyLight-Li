"""
Job management
A separate thread is used to manage all the submitted jobs
It shares a queue with the main thread to accept job submission.
When a job is submitted, it check if it's ready to run.
If not, put it in a dict storing all un-ready jobs.
If yes, submit it to pbs and store the job in an list storing all submitted jobs
The manager checks periodically the status of all jobs in the list:
update all status
post-action on completed jobs
check if any un-ready jobs are now ready and submit the jobs
Eventually there could be a job manager for each beamline
"""
from main.models import Job
import main.job
from local import LocalRunner
from pbs_runner import PBSRunner

import time
import threading
import logging

log = logging.getLogger(__name__)

runners = {
    "local": LocalRunner,
    "pbs": PBSRunner
    }
        
def create_runner(mode, job):
    return runners[mode](job)

class RunnerThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.waitlist = {}
        self.submit_list = {}
        self.is_running = True
        self.period = 1
        #self.server = pbs.pbs_default()
        #self.c = pbs.pbs_connect(self.server)
        #if self.c < 0:
        #    log.warning("Cannot connect to PBS")

    def stop(self):
        pass
        #if pbs.pbs_disconnect(self.c):
        #    log.warning("Error when disconnecting PBS")

    def run(self):
        while self.is_running:
            self.monitor()
            time.sleep(self.period)

    def monitor(self):
        completed_jobs = self.update_status()
        ready_jobs = self.post_action(completed_jobs)
        self.receive_jobs(ready_jobs)
        self.submit_jobs(ready_jobs)

    def update_status(self):
        completed_jobs = []
        #log.info(self.submit_list.keys())
        for id, job in self.submit_list.items():
            job.update_status()
            if job.status() == main.job.JOB_STATUS.FAIL:
                self.remove_job(job)
            if job.status() == main.job.JOB_STATUS.SUCCESS :
                completed_jobs.append(job)
        return completed_jobs
            
    def post_action(self, jobs):
        """also return a list of jobs that are ready because other jobs are completed"""
        ready_jobs = []
        for job in jobs:
            self.remove_job(job)
        return ready_jobs 

    def submit_jobs(self, jobs):
        for job in jobs:
            job.run()
            self.submit_list[job.jobid()] = job

    def remove_job(self, job):
        jw = self.submit_list[job.jobid()]
        #The running job could still update the status after deleting.
        if jw.status() != main.job.JOB_STATUS.DELETED:
            jw.set_status(main.job.JOB_STATUS.DELETED)
        del self.submit_list[job.jobid()]

    def receive_jobs(self, ready_jobs):
        """for now every job is directly put in queue. This will not be the case
        when we implement workflow
        now it may also receive deleted job as a signal to remove that running job
        """
        size = self.queue.qsize()
        for i in range(size):
            try:
                job = self.queue.get()
            except:
                print "Cannot get message", i, "of", size
                continue
            log.info("Receive job %s", job.db_job.id)
            if job.status() == main.job.JOB_STATUS.DELETED:
                self.remove_job(job)
            else:
                ready_jobs.append(job)

