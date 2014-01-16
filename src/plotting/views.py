from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
import users.view_util
import remote.view_util
import h5py
import numpy
import os
    
import logging
logger = logging.getLogger('plotting')

@login_required
def adjust(request):
    """
        
    """
    fd = open(os.path.join(os.path.split(__file__)[0],'data','4065_Iq.txt'))
    data = []
    for l in fd.readlines():
        toks = l.split()
        if len(toks)>=3:
            try:
                q = float(toks[0])
                iq = float(toks[1])
                diq = float(toks[2])
                data.append({'x':q, 'y':iq, 'dy':diq})
            except:
                pass

    numpy.set_printoptions(threshold='nan', nanstr='0', infstr='0')
    f = h5py.File(os.path.join(os.path.split(__file__)[0],'data','4065_Iqxy.nxs'), 'r')
    g = f['mantid_workspace_1']
    y = g['workspace']['axis1']
    x = g['workspace']['axis2']
    values = g['workspace']['values']

    numpy.set_string_function( lambda x: '['+','.join(map(lambda y:'['+','.join(map(str,y))+']',x))+']' )
    data2d = values[:].__repr__()
    numpy.set_string_function( lambda x: '['+','.join(map(str,x))+']' )

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>plotting</a>" % reverse('plotting_adjust')

    template_values = {'data': data,
                       'data2d': data2d,
                       'max_iq': numpy.amax(values),
                       'qx': x[:].__repr__(), 'qy': y[:].__repr__(),
                       'breadcrumbs': breadcrumbs}
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('plotting/adjust.html',
                              template_values)

