from django import forms
from django.utils.dateparse import parse_datetime
from django.http import Http404
from django.shortcuts import get_object_or_404
import httplib, urllib
from base64 import b64encode
import json
import logging
import sys
from models import Transaction

# The following should be in settings
FERMI_HOST = 'fermi.ornl.gov'
FERMI_BASE_URL = '/MantidRemote/'

class FermiLoginForm(forms.Form):
    """
        Simple form to submit authentication
    """
    username = forms.CharField()
    password = forms.CharField()

def get_authentication_status(request):
    """
        Get the authentication status of the user on Fermi
    """
    sessionid = request.session.get('fermi', '')
    fermi_uid = request.session.get('fermi_uid', '')
    if len(sessionid)>0 and len(fermi_uid)>0:
        return fermi_uid
    if len(sessionid)==0:
        return None
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=0.5)
        conn.request('GET', FERMI_BASE_URL+'info', headers={'Cookie':sessionid})
        r = conn.getresponse()  
        info = json.loads(r.read())
        if "Authenticated_As" in info:
            request.session['fermi_uid'] = info["Authenticated_As"]
            return info["Authenticated_As"]
        if "Err_Msg" in info:
            logging.error("MantidRemote: %s" % info["Err_Msg"])
    except:
        logging.error("Could not obtain information from Fermi: %s" % sys.exc_value)
    return None

def fill_template_values(request, **template_args):
    """
        Fill template values for remote submission
    """
    fermi_user = get_authentication_status(request)
    template_args['fermi_authenticated'] = fermi_user is not None
    template_args['fermi_uid'] = fermi_user
    template_args['current_path'] = request.path

    return template_args

def authenticate(request):
    """
        Authenticate with Fermi
    """
    reason = ''
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=0.5)
        userAndPass = b64encode(b"%s:%s" % (request.POST['username'], request.POST['password'])).decode("ascii")
        headers = { 'Authorization' : 'Basic %s' %  userAndPass }
        conn.request('GET', FERMI_BASE_URL+'authenticate', headers=headers)
        r = conn.getresponse()
        if not r.status == 200:
            try:
                info = json.loads(r.read())
                if "Err_Msg" in info:
                    logging.error("MantidRemote: %s" % info["Err_Msg"])
                    reason = info["Err_Msg"]
            except:
                logging.error("MantidRemote: %s" % sys.exc_value)
        sessionid = r.getheader('set-cookie', '')
        if len(sessionid)>0:
            request.session['fermi']=sessionid
            request.session['fermi_uid']=request.POST['username']
        return r.status, reason
    except:
        logging.error("Could not authenticate with Fermi: %s" % sys.exc_value)
    return 500, reason

def transaction(request, start=False):
    """
        Start a transaction with Fermi
    """
    if start is not True:
        transID = request.session.get('fermi_transID', None)
        if transID is not None:
            transactions = Transaction.objects.filter(trans_id=transID)
            if len(transactions)>0:
                return transactions[0]
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=0.5)
        conn.request('GET', FERMI_BASE_URL+'transaction?Action=Start',
                            headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if not r.status == 200:
            logging.error("Fermi transaction call failed: %s" % r.status)
        info = json.loads(r.read())
        if "Err_Msg" in info:
            logging.error("MantidRemote: %s" % info["Err_Msg"])

        request.session['fermi_transID'] = info["TransID"]
        transaction = Transaction(trans_id = info["TransID"],
                                  directory = info["Directory"],
                                  owner = request.user)
        transaction.save()
        return transaction
    except:
        logging.error("Could not get new transaction ID: %s" % sys.exc_value)
    return None

def submit_job(request, transaction, script_code, script_name='web_submission.py'):
    """
    """
    jobID = None

    # Submit job
    post_data = urllib.urlencode({'TransID': transaction.trans_id,
                                  'NumNodes': 1,
                                  'CoresPerNode': 1,
                                  'ScriptName': script_name,
                                  script_name: script_code})
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=5)
        conn.request('POST', FERMI_BASE_URL+'submit',
                     body=post_data,
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        resp = json.loads(r.read())
        if "Err_Msg" in resp:
            logging.error("MantidRemote: %s" % resp["Err_Msg"])
        if 'JobID' in resp:
            jobID = request.session['fermi_jobID'] = resp['JobID']
    except:
        logging.error("Could not submit job: %s" % sys.exc_value)
    return jobID

def query_job(request, job_id):
    """
        Query Fermi for a specific job
    """
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=1.5)
        conn.request('GET', '%squery?JobID=%s' % (FERMI_BASE_URL, job_id),
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            job_info = json.loads(r.read())[job_id]
            job_info['CompletionDate'] = parse_datetime(job_info['CompletionDate'])
            job_info['StartDate'] = parse_datetime(job_info['StartDate'])
            job_info['SubmitDate'] = parse_datetime(job_info['SubmitDate'])
            return job_info
        else:
            logging.error("Could not get job info: %s" % r.status)
    except:
        logging.error("Could not get job info: %s" % sys.exc_value)
    return None

def query_files(request, trans_id):
    """
        Query files for a given transaction
    """
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=1.5)
        conn.request('GET', '%sfiles?TransID=%s' % (FERMI_BASE_URL, trans_id),
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            file_list = json.loads(r.read())['Files']
            return file_list
        else:
            logging.error("Could not get files for transaction: %s" % r.status)
    except:
        logging.error("Could not get files for transaction: %s" % sys.exc_value)
    return None

def download_file(request, trans_id, filename):
    """
        Download a file from the compute node
        https://fermi.ornl.gov/MantidRemote/download?TransID=90&File=submit.sh
    """
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=60)
        conn.request('GET', '%sdownload?TransID=%s&File=%s' % (FERMI_BASE_URL, trans_id, filename),
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            return r.read()
        else:
            logging.error("Could not get file from compute node: %s" % r.status)
    except:
        logging.error("Could not get file from compute node: %s" % sys.exc_value)
    return None

def fill_job_dictionary(request, remote_job_id, **template_values):

    template_values['title'] = 'Job %s' % remote_job_id
    template_values['job_id'] = remote_job_id

    # Query basic job info
    job_info = query_job(request, remote_job_id)
    if job_info is None:
        template_values['user_alert'] = ["Could not connect to Fermi"]
        return template_values
    
    # Get list of files for this transaction
    transaction = get_object_or_404(Transaction, trans_id=job_info['TransID'])
    files = query_files(request, transaction.trans_id)


    template_values['trans_id'] = transaction.trans_id
    template_values['job_info'] = job_info
    template_values['job_directory'] = transaction.directory
    template_values['job_files'] = files
    return template_values

