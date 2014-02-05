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
    plot_object = remote_job.get_first_plot(filename=filename, owner=request.user)
    if plot_object is not None and plot_object.first_data_layout() is not None:
        data_str = plot_object.first_data_layout().dataset.data
    else:
        # If we don't have data stored, read it from file
        logging.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
            data_str = process_Iq_data(file_content)
            plot_object = Plot1D.objects.create_plot(request.user,
                                                     data=data_str,
                                                     filename=filename)
            remote_job.plots.add(plot_object)
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = plot_object.id if plot_object is not None else None
    return template_values

def process_iqxy_output(request, remote_job, filename):
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


    return template_values

def process_Iq_data(file_content, return_raw=False):
    """
        Process the content of an I(q) file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
        @param return_raw: if True, return the array instead of a string
    """
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
    if return_raw:
        return data
    return str(data)

