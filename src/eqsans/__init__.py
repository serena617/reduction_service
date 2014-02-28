from django.core.urlresolvers import reverse

def get_new_reduction_url(run=None, ipts=None):
    """
        Returns the URL to use to create a new run
        @param run: run number [string or integer]
        @param ipts: experiment name [string]
    """
    if run is None:
        return reverse('eqsans.views.reduction_options')
    return reverse('eqsans.views.reduction_options')+"?reduction_name=Reduction for %s&expt_name=%s&data_file=%s" % (run, ipts, run)

def get_new_batch_url(run=None, ipts=None):
    if run is None:
        return reverse('eqsans.views.reduction_configuration')
    return reverse('eqsans.views.reduction_configuration')+"?reduction_name=Reduction for %s&experiment=%s&data_file=%s" % (run, ipts, run)

def get_remote_jobs_url(ipts=None):
    return reverse('eqsans.views.reduction_jobs')

def get_reduction_url(ipts=None):
    return reverse('eqsans.views.reduction_home')