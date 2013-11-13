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
    if reduction_id is not None:
        try:
            reduction_id = int(reduction_id)
        except:
            raise Http404
        
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
                       'title': 'EQSANS Reduction'}
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values.update(csrf(request))
    return render_to_response('eqsans/reduction_options.html',
                              template_values)

@login_required
def save_as_xml(request, reduction_id=None):
    from django.core.files import File

    # Create a Python file object using open() and the with statement
    with open('/tmp/hello.world', 'w') as f:
        myfile = File(f)
        myfile.write('Hello World')
        
    return HttpResponse()