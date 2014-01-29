"""
    Test utilities for deployment where ORNL services are 
    not available
"""
from django.core.urlresolvers import reverse
from django.conf import settings

from models import ReductionProcess, RemoteJob, Instrument
from plotting.models import Plot1D, DataSet, DataLayout, PlotLayout
from remote.models import Transaction
import users.view_util
import remote.view_util
import logging
import os

def get_dummy_data(request, job_id):
    """
        Create a dummy job and plot data
        @param request: request object
        @param job_id: RemoteJob pk
    """
    try:
        remote_job = RemoteJob.objects.get(remote_id=job_id)
    except:
        eqsans = Instrument.objects.get(name='eqsans')
        reduction = ReductionProcess(instrument=eqsans,
                                     name='Dummy job',
                                     owner=request.user,
                                     data_file='/tmp/dummy.nxs')
        reduction.save()
        try:
            transaction = Transaction.objects.get(trans_id=-1)
        except:
            transaction = Transaction(trans_id=-1,
                                      owner=request.user,
                                      directory='/tmp')
            transaction.save()
        remote_job = RemoteJob(reduction=reduction,
                              remote_id='-1',
                              transaction=transaction)
        remote_job.save()
        
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('eqsans.views.reduction_jobs')
    breadcrumbs += " &rsaquo; dummy job"

    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.reduction.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    
    # Go through the files and find data to plot
    f = os.path.join(os.path.split(__file__)[0],'..','plotting','data','4065_Iq.txt')
                
    # Do we read this data already?
    data_str = None
    data_id = None
    plot_object = None
    plots = remote_job.plots.all().filter(filename=f, owner=request.user)
    if len(plots)>0:
        if len(plots[0].data.all())>0:
            data_str = plots[0].data.all()[0].dataset.data
            data_id = plots[0].id
            plot_object = plots[0]
        if len(plots)>1:
            logging.warning("Plotting.models.Plot1D should not have more than 1 entry per data file per user.")
    
    # If we don't have data stored, read it from file
    if data_str is None:
        file_content = open(f,'r').read()
        data = []
        for l in file_content.split('\n'):
            toks = l.split()
            if len(toks)>=3:
                try:
                    q = float(toks[0])
                    iq = float(toks[1])
                    diq = float(toks[2])
                    data.append([q, iq, diq])
                except:
                    pass
        data_str = str(data)
        dataset = DataSet(owner=request.user, data=data_str)
        dataset.save()
        datalayout = DataLayout(owner=request.user, dataset=dataset)
        datalayout.save()
        plotlayout = PlotLayout(owner=request.user)
        plot1d = Plot1D(owner=request.user, filename=f, layout=plotlayout)
        plot1d.save()
        plot1d.data.add(datalayout)
        remote_job.plots.add(plot1d)
        data_id = plot1d.id
        plot_object = plot1d
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = data_id
    
    return template_values
