from django.db import models
from django.contrib.auth.models import User
import datetime
from django.utils.timezone import utc

class History(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User)
    size = models.IntegerField()
    is_current = models.BooleanField()

class Workflow(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User)
    #more fields to add

class Job(models.Model):
    history = models.ForeignKey(History)
    tool = models.CharField(max_length=50)
    created_date = models.DateField(auto_now_add = True)
    created_time = models.TimeField(auto_now_add = True)
    last_save_datetime = models.DateTimeField(auto_now = True)
    status = models.IntegerField()   ###job status

    """def save(self, *args, **kwargs):
	now = datetime.datetime.utcnow().replace(tzinfo=utc)
	if not self.id:
		self.created_date = now.date()
		self.created_time = now.time()
	self.last_save_datetime = now"""
    def __unicode__(self):
        return str(self.tool)

class ToolData(models.Model):
    """
    generate a much generic way to store data
    """
    job = models.ForeignKey(Job)
    data_key = models.CharField(max_length=200)
    data_val = models.CharField(max_length=500)

    def __unicode__(self):
        return str(self.job)


class OutputData(models.Model):
	job = models.ForeignKey(Job)
	filename = models.CharField(max_length=50)



