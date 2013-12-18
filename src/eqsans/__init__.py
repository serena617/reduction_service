from django.core.urlresolvers import reverse

def get_new_reduction_url(run, ipts):
    """
        Returns the URL to use to create a new run
        @param run: run number [string or integer]
        @param ipts: experiment name [string]
    """
    return reverse('eqsans.views.reduction_options')+"?reduction_name=Reduction for %s&expt_name=%s&data_file=%s" % (run, ipts, run)