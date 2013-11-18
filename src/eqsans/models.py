from django.db import models
from django.contrib.auth.models import User

class Instrument(models.Model):
    name = models.CharField(max_length=24)
    
class Experiment(models.Model):
    ipts = models.CharField(max_length=24)
    
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
        return self.name
    
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
    
