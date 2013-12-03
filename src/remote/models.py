from django.db import models
from django.contrib.auth.models import User

class JobStatus(models.Model):
    """
        Table of job status codes
    """ 
    status = models.CharField(max_length=24)
    
    def __str__(self):
        return self.status

class ReductionJob(models.Model):
    """
        Table of Fermi jobs
    """
    job_id = models.IntegerField(unique=True)
    status = models.ForeignKey(JobStatus)
    title = models.CharField(max_length=128)
    owner = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    