"""
    Utilities for EQSANS views
"""
from plotting.models import Plot1D, DataSet, DataLayout, PlotLayout
import remote.view_util
import logging

def process_iq_output(request, remote_job, trans_id, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    template_values = {}
    # Do we read this data already?
    data_str = None
    data_id = None
    plot_object = None
    plots = remote_job.plots.all().filter(filename=filename, owner=request.user)
    if len(plots)>0:
        plot1d = plots[0].first_data_layout()
        if plot1d is not None:
            data_str = plot1d.dataset.data
            data_id = plots[0].id
            plot_object = plots[0]
    
    # If we don't have data stored, read it from file
    if data_str is None:
        logging.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
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
            plot_object = Plot1D.objects.create_plot(request.user,
                                                     data=data_str,
                                                     filename=filename)
            remote_job.plots.add(plot_object)
            data_id = plot_object.id
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = data_id
    return template_values

def process_iqxy_output(request, remote_job, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    template_values = {}
    
    return template_values
