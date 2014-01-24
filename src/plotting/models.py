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
    title = models.TextField()
    width = models.IntegerField()
    height = models.IntegerField()
    is_x_log = models.BooleanField(default=False)
    is_y_log = models.BooleanField(default=False)
    x_label = models.TextField()
    y_label = models.TextField()

class DataSet(models.Model):
    """
        Data set. Used as cache.
    """
    owner = models.ForeignKey(User)
    data  = models.TextField()
    
class DataLayout(models.Model):
    """
        Options related to the plotted data.
    """
    owner = models.ForeignKey(User)
    color = models.CharField(max_length=12)
    size  = models.IntegerField(default=2)
    dataset = models.ForeignKey(DataSet)
    
class Plot1D(models.Model):
    """
        Put together a plot
    """
    owner = models.ForeignKey(User)
    data = models.ManyToManyField(DataLayout)
    layout = models.ForeignKey(PlotLayout)
    