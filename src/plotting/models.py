"""
    Models used to store plotting data and options
"""
from django.db import models
from django.contrib.auth.models import User

class PlotLayout(models.Model):
    """
        Options for a plotting area,
        which means everything except the options
        related to the data points.
    """
    owner = models.ForeignKey(User)
    title = models.TextField(default='')
    width = models.IntegerField(default=550)
    height = models.IntegerField(default=250)
    is_x_log = models.BooleanField(default=False)
    is_y_log = models.BooleanField(default=False)
    x_label = models.TextField(default='Q [1/&Aring;]')
    y_label = models.TextField(default='Intensity')
    
    def __str__(self):
        return "%s-%s" % (self.owner, self.id)

class DataSet(models.Model):
    """
        Data set. Used as cache.
    """
    owner = models.ForeignKey(User)
    data  = models.TextField()
    #filename = models.TextField()
    
    def __str__(self):
        return str(self.owner)
    
class DataLayout(models.Model):
    """
        Options related to the plotted data.
    """
    owner = models.ForeignKey(User)
    color = models.CharField(max_length=12, default='#0077cc')
    size  = models.IntegerField(default=2)
    dataset = models.ForeignKey(DataSet)
    
    def __str__(self):
        return "%s-%s" % (self.owner, self.id)
    
class Plot1D(models.Model):
    """
        Put together a plot
    """
    owner = models.ForeignKey(User)
    filename = models.TextField()
    data = models.ManyToManyField(DataLayout)
    layout = models.ForeignKey(PlotLayout, null=True, blank=True)
    
    def __str__(self):
        return self.filename
    
    def first_data_layout(self):
        """
            Return the first data set to be plotted
        """
        if len(self.data.all())>0:
            return self.data.all()[0]
        return None
    