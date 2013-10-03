import logging
import main.job
import os
import main
import pbs
log = logging.getLogger(__name__)

PBS_STATUS = {
    'R': main.job.JOB_STATUS.RUNNING,
    'Q': main.job.JOB_STATUS.QUEUED,
    'C': main.job.JOB_STATUS.SUCCESS
    }

PBS_OPTIONS = {
    '-l': pbs.ATTR_l,
    '-o': pbs.ATTR_o,
    '-e': pbs.ATTR_e,
    '-j': pbs.ATTR_j,
    '-m': pbs.ATTR_m,
    '-M': pbs.ATTR_M,
    '-N': pbs.ATTR_N,
    '-S': pbs.ATTR_S
    }

PBS_SCRIPT = """
cd %s/
%s
"""

class PBSRunner:
    """submit to pbs queue"""
    def __init__(self, job):
        self.jobid = 0
        self.attrl = pbs.new_attrl(1)
        self.attrl[0].name = 'job_state'
        self.attropl = self.get_pbs_attr(job.db_job.id, job.tool.config)
        self.script = PBS_SCRIPT % (job.tool.directory, job.command)
        self.status = main.job.JOB_STATUS.READY

    def connect(self):
        self.c = pbs.pbs_connect(pbs.pbs_default())
        return self.c

    def disconnect(self):
        if hasattr(self, 'c'):
            pbs.pbs_disconnect(self.c)

    def get_status(self):
        if self.status == main.job.JOB_STATUS.FAIL:
            return self.status
        if not self.jobid:
            return PBS_STATUS['Q']
        stats = pbs.pbs_statjob(self.connect(), self.jobid, self.attrl, "NULL")
        status = stats[0].attribs[0].value
        self.disconnect()
        if status in PBS_STATUS:
            return PBS_STATUS[status]
        return PBS_STATUS['Q']
    
    def run(self):
        script_name = 'pylight_script'
        with open(script_name, 'w') as f:
            f.write(self.script)
        self.jobid = pbs.pbs_submit(self.connect(), self.attropl, script_name, 'batch', "NULL") 
        log.info("PBS submits a job %s" % self.jobid) 
        os.remove(script_name)
        e, text = pbs.error()
        if e:
            log.warning("Failed to submit a job: %s", text)
            self.status = main.job.JOB_STATUS.FAIL
        self.disconnect()
          
    def submit_jobs_pbs(self, jobs):
        for job in jobs:
            tool = job.tool
            command = job.create_command()            
            attropl = self.get_pbs_attr(job.db_job.id, tool.config)
            script = PBS_SCRIPT % (job.tool.directory, command)
            log.info(script)
            script_name = 'pylight_script'
            with open(script_name, 'w') as f:
                f.write(script)
            job_id = pbs.pbs_submit(self.c, attropl, script_name, 'batch', "NULL") 
            os.remove(script_name)
            e, text = pbs.error()
            if e:
                log.warning("Failed to submit a job: %s", text)
                #what about jobs that following this one?
                continue
            log.info("PBS submits a job %s as %s" % (job, job_id)) 
            self.submit_list[job_id] = job

    def parse_pbs_comment(self, config):
        """change PBS comments to general pbs parameters used by attropl"""
        pbs_config = []
        for line in config:
            args = line.split()
            op = PBS_OPTIONS[args[0]]
            if op != pbs.ATTR_l:
                pbs_config.append([op, args[1]])
            else:
                pair = args[1].split("=", 1)
                pbs_config.append([op, pair[0], pair[1]])
        return pbs_config

    def get_pbs_attr(self, job_id, config):
        """tool configuration should either have pbs_comments or pbs
        pbs_comments are just comments used in PBS script
        """
        if 'pbs_comments' in config:
            pbs_config = self.parse_pbs_comment(config['pbs_comments'])
        else:
            assert('pbs' in config)
            pbs_config = config['pbs']
        num = len(pbs_config)
        attropl = pbs.new_attropl(num + 2)
        for i, item in enumerate(pbs_config):
            attropl[i].name = item[0].encode('ascii', 'ignore')
            if attropl[i].name == pbs.ATTR_l:
                attropl[i].resource = item[1].encode('ascii', 'ignore')
                attropl[i].value = item[2].encode('ascii', 'ignore')
            else:
                attropl[i].value = item[1].encode('ascii', 'ignore')
        attropl[num].name = pbs.ATTR_o
        attropl[num].value = main.DATA_SOURCE_DIR + "%d.out" % job_id
        attropl[num + 1].name = pbs.ATTR_e
        attropl[num + 1].value = main.DATA_SOURCE_DIR + "%d.err" % job_id
        return attropl
