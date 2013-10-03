from main.job import JOB_STATUS
import subprocess
import logging
log = logging.getLogger(__name__)


class LocalRunner:
    """Runner is attached to a job when it's submitted to the running queue"""
    def __init__(self, job):
        self.command = "cd %s;" % job.tool.directory
        self.command += job.command
        log.info(self.command)

    def get_status(self):
        if not hasattr(self, "proc"):
            return JOB_STATUS.QUEUED
        status = self.proc.poll()
        if status is None:
            return JOB_STATUS.RUNNING
        if status == 0:
            return JOB_STATUS.SUCCESS
        else:
            return JOB_STATUS.FAIL
        
    def run(self):
        if hasattr(self, "proc"):
            log.warning("Already running")
            return
        self.proc = subprocess.Popen(self.command, shell=True)
        
        