"""
    Reduction task models.
    TODO: Some of the models here are meant to be common to all instruments and are
    not specific to EQSANS. Those should be pulled out as we start building the common
    reduction framework.
"""
from django.db import models
from django.contrib.auth.models import User
from remote.models import Transaction
from plotting.models import Plot1D

UNCATEGORIZED = 'uncategorized'

class Instrument(models.Model):
    name = models.CharField(max_length=24)
    
    def __str__(self):
        return self.name

class ExperimentManager(models.Manager):
    
    def experiments_for_instrument(self, instrument_id):
        return super(ExperimentManager, self).get_query_set().filter(instruments=instrument_id)

    def get_uncategorized(self, instrument):
        expt_list = super(ExperimentManager, self).get_query_set().filter(name=UNCATEGORIZED)
        if len(expt_list)>0:
            expt = expt_list[0]
        else:
            expt = Experiment(name=UNCATEGORIZED)
            expt.save()
        if instrument is not None:
            instrument_id = Instrument.objects.get_or_create(name=instrument.lower())
            expt.instruments.add(instrument_id[0])
        return expt
        
class Experiment(models.Model):
    """
        Table holding IPTS information
    """
    name = models.CharField(max_length=24, unique=True)
    instruments = models.ManyToManyField(Instrument, related_name='_ipts_instruments+')
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    objects = ExperimentManager()
    
    def __unicode__(self):
        return self.name
    
    def is_uncategorized(self):
        return self.name == UNCATEGORIZED
    
class ReductionProcess(models.Model):
    """
    """
    instrument = models.ForeignKey(Instrument)
    experiments = models.ManyToManyField(Experiment, related_name='_reduction_experiment+')
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(User)
    data_file = models.CharField(max_length=128)
    timestamp = models.DateTimeField('timestamp', auto_now=True)
    
    def __str__(self):
        return "%s - %s" % (self.id, self.name)
    
    def get_data_dict(self):
        """
            Return a dictionary of properties for this entry
        """
        data = {}
        data['reduction_name'] = self.name
        
        # Go through the list of reduction parameters
        params = FloatReductionProperty.objects.filter(reduction=self)
        for p in params:
            data[p.name] = p.value
        params = CharReductionProperty.objects.filter(reduction=self)
        for p in params:
            data[p.name] = p.value
        params = BoolReductionProperty.objects.filter(reduction=self)
        for p in params:
            data[p.name] = p.value
            
        return data
    
class ReductionProperty(models.Model):
    reduction = models.ForeignKey(ReductionProcess)
    name = models.CharField(max_length=56)

    def reduction_link(self):
            return "<a href='/database/eqsans/reductionprocess/%s'>%s %s</a>" % (self.reduction.id, self.reduction.id, self.reduction)
    reduction_link.allow_tags = True

    class Meta:
        abstract = True
    
class BoolReductionProperty(ReductionProperty):
    value = models.BooleanField(default=True)
    
class FloatReductionProperty(ReductionProperty):
    value = models.FloatField()
    
class CharReductionProperty(ReductionProperty):
    value = models.CharField(max_length=128)
    
class RemoteJob(models.Model):
    reduction = models.ForeignKey(ReductionProcess)
    remote_id = models.CharField(max_length = 30, unique=True)
    transaction = models.ForeignKey(Transaction)
    plots = models.ManyToManyField(Plot1D, null=True, blank=True, related_name='_remote_job_plot+')
    
