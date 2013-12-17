from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from icat_server_communication import get_ipts_runs, get_instruments, get_experiments
import users.view_util
import remote.view_util

@login_required
def instrument_list(request):
    """
        Return a list of available instruments
    """
    breadcrumbs = "home"
    instruments = get_instruments()
    template_values = {'instruments': instruments,
                       'breadcrumbs': breadcrumbs}
    if len(instruments)==0:
        template_values['user_alert'] = ['No instruments were returned']
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/instrument_list.html',
                              template_values)
    
@login_required
def experiment_list(request, instrument):
    """
        Return the list of experiments for a given instrument
    """
    breadcrumbs = "<a href='/catalog/'>home</a> &rsaquo; %s" % (instrument.lower())
    experiments = get_experiments(instrument.upper())
    template_values = {'experiments': experiments,
                       'instrument': instrument,
                       'title': '%s experiments' % instrument.upper(),
                       'breadcrumbs': breadcrumbs}
    if len(experiments)==0:
        template_values['user_alert'] = ['No experiments were returned for instrument %s' % instrument]
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_list.html',
                              template_values)
    
@login_required
def experiment_run_list(request, instrument, ipts='IPTS-8340'):

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; %s" % (reverse('catalog.views.instrument_list'),
                                                                                             reverse('catalog.views.experiment_list', args=[instrument]),
                                                                                             instrument.lower(),
                                                                                             ipts.lower(),
                                                                                             )
    runs = get_ipts_runs(instrument.upper(), ipts)
    template_values = {'run_data': runs,
                       'experiment': ipts,
                       'title': '%s %s' % (instrument.upper(), ipts.upper()),
                       'breadcrumbs': breadcrumbs}
    if len(runs)==0:
        template_values['user_alert'] = ['No runs were returned for instrument %s experiment %s' % (instrument, ipts)]
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_run_list.html',
                              template_values)