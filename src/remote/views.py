from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.utils.dateparse import parse_datetime
from django import forms
from models import ReductionJob

import users.view_util

import httplib
from base64 import b64encode
import json
import logging
import sys

# The following should be in settings
FERMI_HOST = 'fermi.ornl.gov'
FERMI_BASE_URL = '/MantidRemote/'
FERMI_QUERY = '/MantidRemote/query'

#FERMI_HOST = 'localhost:8000'
#FERMI_QUERY = '/remote/query/'


class FermiLoginForm(forms.Form):
    """
        Simple form to submit authentication
    """
    username = forms.CharField()
    password = forms.CharField()

@login_required
def query_remote_jobs(request):
    """
        Query the Fermi remote service for the user's jobs.
        The response will be like this:
        
        { "3954": { "CompletionDate": "2013-10-29T17:13:08+00:00",
                    "StartDate": "2013-10-29T17:12:32+00:00",
                    "SubmitDate": "2013-10-29T17:12:31+00:00",
                    "JobName": "eqsans",
                    "ScriptName": "job_submission_0.py",
                    "JobStatus": "COMPLETED",
                    "TransID": 57 } }
    """
    sessionid = request.session.get('fermi', '')
    if request.method == 'POST':
        form = FermiLoginForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                conn = httplib.HTTPSConnection(FERMI_HOST, timeout=0.5)
                userAndPass = b64encode(b"%s:%s" % (request.POST['username'], request.POST['password'])).decode("ascii")
                headers = { 'Authorization' : 'Basic %s' %  userAndPass }
                conn.request('GET', FERMI_BASE_URL+'authenticate', headers=headers)
                r = conn.getresponse()  
                logging.error(r.getheaders())
                logging.error(r.status)
                sessionid = r.getheader('set-cookie', '')
                request.session['fermi']=sessionid
                #headers['Cookie'] = response['set-cookie']  
            except:
                logging.error("Could not authenticate with Fermi: %s" % sys.exc_value)

    template_values = {}
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=30)
        conn.request('GET', FERMI_QUERY, headers={'Cookie': sessionid})
        r = conn.getresponse()
        logging.error(r.status)
        # Check to see whether we need authentication
        jobs = json.loads(r.read())
        need_authentication = True
        if r.status == 401:
            pass
        elif r.status == 404:
            need_authentication = False
            template_values['errors'] = "Fermi service could not be found [404]"
        else:
            need_authentication = False
            status_data = []
            for key in jobs:
                jobs[key]['ID'] = key
                jobs[key]['CompletionDate'] = parse_datetime(jobs[key]['CompletionDate'])
                jobs[key]['StartDate'] = parse_datetime(jobs[key]['StartDate'])
                jobs[key]['SubmitDate'] = parse_datetime(jobs[key]['SubmitDate'])
                status_data.append(jobs[key])
            template_values['status_data'] = status_data
        template_values['need_authentication'] = need_authentication

    except:
        logging.error("Could not connect to status page: %s" % sys.exc_value)
        template_values['errors'] = "Could not connect to Fermi: %s" % sys.exc_value
    
    template_values = users.view_util.fill_template_values(request, **template_values)   
    template_values.update(csrf(request))
    return render_to_response('remote/query_remote_jobs.html',
                              template_values)

def fake_query(request):
    data = { "3974": { "CompletionDate": "2013-10-29T17:13:08+00:00",
                "StartDate": "2013-10-29T17:12:32+00:00",
                "SubmitDate": "2013-10-29T17:12:31+00:00",
                "JobName": "eqsans",
                "ScriptName": "job_submission_0.py",
                "JobStatus": "COMPLETED",
                "TransID": 57 },
            "3954": { "CompletionDate": "2013-10-29T17:13:08+00:00",
                "StartDate": "2013-10-29T17:12:32+00:00",
                "SubmitDate": "2013-10-29T17:12:31+00:00",
                "JobName": "eqsans",
                "ScriptName": "job_submission_0.py",
                "JobStatus": "COMPLETED",
                "TransID": 57 } }
    return HttpResponse(json.dumps(data), mimetype="application/json")
