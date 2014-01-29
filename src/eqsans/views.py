from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

from models import ReductionProcess, Experiment, RemoteJob, Instrument
from plotting.models import Plot1D, DataSet, DataLayout, PlotLayout
from remote.models import Transaction
import users.view_util
import remote.view_util
from catalog.icat_server_communication import get_ipts_info
from . import forms
import logging
import copy

@login_required
def experiment(request, ipts):
    """
        List of reductions
        #TODO add a way to delete your own entries
        #TODO create new reduction using a pre-existing one as a template
    """
    # Get experiment object
    uncategorized = Experiment.objects.get_uncategorized('eqsans')
    try:
        experiment_obj = Experiment.objects.get(name=ipts)
    except:
        experiment_obj = uncategorized
    
    IS_UNCATEGORIZED = experiment_obj.is_uncategorized()

    reduction_start_form = forms.ReductionStart(request.GET)

    # Query ICAT
    run_list = []
    icat_ipts = {}
    if not IS_UNCATEGORIZED:
        icat_ipts = get_ipts_info('EQSANS', ipts)
        if 'run_range' in icat_ipts:
            try:
                toks = icat_ipts['run_range'].split('-')
                r_min = int(toks[0])
                r_max = int(toks[1])
                for r in range(r_min, r_max+1):
                    run_list.append({'run':r})
            except:
                logging.error("Problem generating run list: %s" % sys.exc_value)

    # Get all the user's reductions
    red_list = []
    if 'run_number' in request.GET:
        red_list = ReductionProcess.objects.filter(owner=request.user,
                                                   data_file__contains=request.GET['run_number'])
        if len(red_list) == 0:
            create_url  = reverse('eqsans.views.reduction_options')
            create_url +=  '?reduction_name=Reduction for r%s' % request.GET['run_number']
            create_url +=  '&expt_id=%d' % experiment_obj.id
            create_url +=  '&data_file=%s' % request.GET['run_number']
            return redirect(create_url)
    else:
        for item in run_list:
            partial_list = ReductionProcess.objects.filter(owner=request.user,
                                                           experiments=uncategorized,
                                                           data_file__contains=str(item['run']))
            red_list.extend(partial_list)
        for item in ReductionProcess.objects.filter(owner=request.user,
                                                        experiments=experiment_obj):
            if not item in red_list:
                red_list.append(item)

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
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; %s" % ipts.lower()
    template_values = {'reductions': reductions,
                       'title': 'EQSANS %s' % ipts,
                       'breadcrumbs': breadcrumbs,
                       'ipts_number': ipts,
                       'run_list': run_list,
                       'icat_info': icat_ipts,
                       'form': reduction_start_form,
                       'is_categorized': not IS_UNCATEGORIZED}
    if 'icat_error' in icat_ipts:
        template_values['user_alert'] = [icat_ipts['icat_error']]
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/experiment.html',
                              template_values)

@login_required
def reduction_options(request, reduction_id=None):
    """
        Display the reduction options form
    """
    #TODO: add ICAT info on top of the page
    #TODO: add notes?
    if reduction_id is not None:
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    
    experiment_obj = None
    if request.method == 'POST':
        options_form = forms.ReductionOptions(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid():
            reduction_id = options_form.to_db(request.user, reduction_id)
            if reduction_id is not None:
                return redirect(reverse('eqsans.views.reduction_options', args=[reduction_id]))
    else:
        if reduction_id is not None:
            initial_values = forms.ReductionOptions.data_from_db(request.user, reduction_id)
        else:
            initial_values = copy.deepcopy(request.GET)
            if 'expt_name' in request.GET:
                try:
                    experiment_obj = Experiment.objects.get(name=request.GET['expt_name'])
                except:
                    experiment_obj = Experiment(name=request.GET['expt_name'])
                    experiment_obj.save()
                initial_values['expt_id'] = experiment_obj.id
                try:
                    instrument_obj = Instrument.objects.get(name='eqsans')
                except:
                    instrument_obj = Instrument(name='eqsans')
                    instrument_obj.save()
                if not instrument_obj in experiment_obj.instruments.all():
                    experiment_obj.instruments.add(instrument_obj)
                    experiment_obj.save()
        
        options_form = forms.ReductionOptions(initial=initial_values)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    if reduction_id is not None:
        breadcrumbs += " &rsaquo; reduction %s" % reduction_id
    else:
        breadcrumbs += " &rsaquo; new reduction"

    #TODO: add New an Save-As functionality
    template_values = {'options_form': options_form,
                       'title': 'EQSANS Reduction',
                       'breadcrumbs': breadcrumbs,
                       'reduction_id': reduction_id,
                       'errors': len(options_form.errors) }
    # Get existing jobs for this reduction
    if reduction_id is not None:
        existing_jobs = RemoteJob.objects.filter(reduction=reduction_proc).order_by('id')
        template_values['existing_jobs'] = existing_jobs
        template_values['expt_list'] = reduction_proc.experiments.all()
    elif experiment_obj is not None:
        template_values['expt_list'] = [experiment_obj]
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_options.html',
                              template_values)

@login_required
def reduction_script(request, reduction_id):
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='.'>reduction</a> &rsaquo; script"
    
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
        Return the xml representation of a reduction process
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_xml(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.xml"'
    return response

@login_required
def submit_job(request, reduction_id):
    """
        Submit a reduction script to Fermi
    """
    #TODO: save snapshot of script
    #TODO: report submission errors
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)

    # Start a new transaction
    transaction = remote.view_util.transaction(request, start=True)
    if transaction is None:
        breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
        breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
        breadcrumbs += " &rsaquo; <a href='%s'>reduction</a>" % reverse('eqsans.views.reduction_options', args=[reduction_id])
        template_values = {'message':"Could not connect to Fermi and establish transaction",
                           'back_url': reverse('eqsans.views.reduction_options', args=[reduction_id]),
                           'breadcrumbs': breadcrumbs,}
        template_values = users.view_util.fill_template_values(request, **template_values)
        template_values = remote.view_util.fill_template_values(request, **template_values)

        return render_to_response('remote/failed_connection.html',
                                  template_values)        

    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)     
    code = forms.ReductionOptions.as_mantid_script(data, transaction.directory)
    jobID = remote.view_util.submit_job(request, transaction, code)
    if jobID is not None:
        job = RemoteJob(reduction=reduction_proc,
                        remote_id=jobID,
                        transaction=transaction)
        job.save()
    return redirect(reverse('eqsans.views.reduction_options', args=[reduction_id]))

@login_required
def job_details(request, job_id):
    """
        Show status of a given remote job
    """
    #TODO plot I(q)
    #TODO download files
    remote_job = get_object_or_404(RemoteJob, remote_id=job_id)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('eqsans.views.reduction_jobs')
    breadcrumbs += " &rsaquo; %s" % job_id

    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.reduction.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    
    # Go through the files and find data to plot
    if 'job_files' in template_values and 'trans_id' in template_values:
        for f in template_values['job_files']:
            if f.endswith('_Iq.txt'):
                
                # Do we read this data already?
                data_str = None
                data_id = None
                plot_object = None
                plots = remote_job.plots.all().filter(filename=f, owner=request.user)
                if len(plots)>0:
                    if len(plots[0].data.all())>0:
                        data_str = plots[0].data.all()[0].dataset.data
                        data_id = plots[0].id
                        plot_object = plots[0]
                    if len(plots)>1:
                        logging.warning("Plotting.models.Plot1D should not have more than 1 entry per data file per user.")
                
                # If we don't have data stored, read it from file
                if data_str is None:
                    logging.warning("Retrieving %s from compute resource" % f)
                    file_content = remote.view_util.download_file(request, template_values['trans_id'], f)
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
                    data_str = str(data)
                    dataset = DataSet(owner=request.user, data=data_str)
                    dataset.save()
                    datalayout = DataLayout(owner=request.user, dataset=dataset)
                    datalayout.save()
                    plot1d = Plot1D(owner=request.user, filename=f)
                    plot1d.save()
                    plot1d.data.add(datalayout)
                    remote_job.plots.add(plot1d)
                    data_id = plot1d.id
                    plot_object = plot1d
                
                template_values['plot_1d'] = data_str
                template_values['plot_object'] = plot_object
                template_values['plot_1d_id'] = data_id
                break
                
    return render_to_response('eqsans/reduction_job_details.html',
                              template_values)

@login_required
def test_result(request, job_id='-1'):
    """
        Dummy job for development when ORNL resources are not available
    """
    from test_util import get_dummy_data
    template_values = get_dummy_data(request, job_id)
    return render_to_response('eqsans/reduction_job_details.html',
                              template_values)
    
@login_required
def reduction_jobs(request):
    """
        { "3954": { "CompletionDate": "2013-10-29T17:13:08+00:00",
                    "StartDate": "2013-10-29T17:12:32+00:00",
                    "SubmitDate": "2013-10-29T17:12:31+00:00",
                    "JobName": "eqsans",
                    "ScriptName": "job_submission_0.py",
                    "JobStatus": "COMPLETED",
                    "TransID": 57 } }
    """
    #TODO sorting
    jobs = RemoteJob.objects.filter(transaction__owner=request.user)
    status_data = []
    for job in jobs:
        j_data = {'ID': job.remote_id,
                  'JobName': job.reduction.name,
                  'StartDate': job.transaction.start_time,
                  'Data': job.reduction.data_file,
                 }
        status_data.append(j_data)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; jobs"
    template_values = {'status_data': status_data,
                       'breadcrumbs': breadcrumbs}
    template_values = users.view_util.fill_template_values(request, **template_values)   
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_jobs.html',
                              template_values)

@login_required
def reduction_home(request):
    eqsans = get_object_or_404(Instrument, name='eqsans')
    experiments = Experiment.objects.experiments_for_instrument(eqsans)

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; eqsans reduction" % reverse(settings.LANDING_VIEW)
    template_values = {'title': 'EQSANS Reduction',
                       'experiments':experiments,
                       'breadcrumbs': breadcrumbs}
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_home.html',
                              template_values)
