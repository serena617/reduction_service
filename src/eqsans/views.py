from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

from icat_server_communication import get_ipts_info, get_run_info
from models import ReductionProcess
import users.view_util
from . import forms

@login_required
def reduction_home(request):
    """
        List of reductions
    """
    if request.method == 'POST':
        reduction_start_form = forms.ReductionStart(request.POST)
        if reduction_start_form.is_valid():
            return redirect(reverse('eqsans.views.reduction_start', args=[reduction_start_form.cleaned_data['run_number']]))
    else:
        reduction_start_form = forms.ReductionStart()

    # Get all the user's reductions
    red_list = ReductionProcess.objects.filter(owner=request.user)
    reductions = []
    for r in red_list:
        data_dict = r.get_data_dict()
        data_dict['id'] = r.id
        try:
            run_id = int(data_dict['data_file'])
            data_dict['webmon_url'] = "https://monitor.sns.gov/report/eqsans/%s/" % run_id
        except:
            pass
        reductions.append(data_dict)
        
    # Query ICAT
    ipts_number = 'IPTS-9388'
    icat_ipts = get_ipts_info('EQSANS', ipts_number)
    run_list = []
    if 'run_range' in icat_ipts:
        try:
            toks = icat_ipts['run_range'].split('-')
            r_min = int(toks[0])
            r_max = int(toks[1])
            for r in range(r_min, r_max+1):
                run_list.append({'run':r})
        except:
            pass
        
    breadcrumbs = "eqsans"
    template_values = {'reductions': reductions,
                       'title': 'EQSANS %s' % ipts_number,
                       'breadcrumbs': breadcrumbs,
                       'ipts_number': ipts_number,
                       'run_list': run_list,
                       'icat_info': icat_ipts,
                       'form': reduction_start_form,
                       'errors':icat_ipts }
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values.update(csrf(request))
    return render_to_response('eqsans/reduction_home.html',
                              template_values)
    
@login_required
def reduction_start(request, run_number):
    """
        Initiate a new reduction process
    """
    return HttpResponse()

@login_required
def reduction_options(request, reduction_id=None):
    """
    """
    if request.method == 'POST':
        options_form = forms.ReductionOptions(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid():
            reduction_id = options_form.to_db(request.user, reduction_id)
            if reduction_id is not None:
                return redirect(reverse('eqsans.views.reduction_options', args=[reduction_id]))
    else:
        initial_values = {}
        if reduction_id is not None:
            initial_values = forms.ReductionOptions.data_from_db(request.user, reduction_id)
        options_form = forms.ReductionOptions(initial=initial_values)

    breadcrumbs = "<a href='%s'>eqsans</a>" % reverse('eqsans.views.reduction_home')
    if reduction_id is not None:
        breadcrumbs += " &rsaquo; reduction %s" % reduction_id

    #TODO: add New an Save-As functionality
    template_values = {'options_form': options_form,
                       'title': 'EQSANS Reduction',
                       'breadcrumbs': breadcrumbs,
                       'reduction_id': reduction_id,
                       'errors': len(options_form.errors) }
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values.update(csrf(request))
    return render_to_response('eqsans/reduction_options.html',
                              template_values)

@login_required
def reduction_script(request, reduction_id):
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    breadcrumbs = "<a href='%s'>eqsans</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='.'>reduction %s</a>" % reduction_id
    breadcrumbs += " &rsaquo; script"
    
    template_values = {'reduction_name': data['reduction_name'],
                       'breadcrumbs': breadcrumbs,
                       'code': forms.ReductionOptions.as_mantid_script(data) }
    template_values = users.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_script.html',
                              template_values)

@login_required
def py_reduction_script(request, reduction_id):
    """
        Return the python script for a reduction process
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_mantid_script(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.py"'
    return response

@login_required
def xml_reduction_script(request, reduction_id):
    """
        Return the python script for a reduction process
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_xml(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.xml"'
    return response


