from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

import users.view_util
from . import forms

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

    #TODO: add New an Save-As functionality
    template_values = {'options_form': options_form,
                       'title': 'EQSANS Reduction',
                       'errors': len(options_form.errors) }
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values.update(csrf(request))
    return render_to_response('eqsans/reduction_options.html',
                              template_values)

@login_required
def reduction_script(request, reduction_id):
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    template_values = {'reduction_name': data['reduction_name'],
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


