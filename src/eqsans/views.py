"""
    EQSANS views for the SNS analysis/reduction web application.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

from models import ReductionProcess, Experiment, RemoteJob, Instrument, ReductionConfiguration, RemoteJobSet
import reduction_service.view_util
import remote.view_util
import view_util
from catalog.icat_server_communication import get_ipts_info
from . import forms
from django.forms.formsets import formset_factory
import copy
import zipfile
import StringIO

@login_required
def experiment(request, ipts):
    """
        List of reductions and configurations for a given experiment
        @param request: request object
        @param ipts: experiment name
        
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

    icat_ipts = {}
    if not IS_UNCATEGORIZED:
        icat_ipts = get_ipts_info('EQSANS', ipts)

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
        for item in ReductionProcess.objects.filter(owner=request.user,
                                                    experiments=experiment_obj).order_by('data_file'):
            if not item in red_list:
                red_list.append(item)

    reductions = []
    for r in red_list:
        data_dict = r.get_data_dict()
        data_dict['id'] = r.id
        data_dict['config'] = r.get_config()
        latest_job = view_util.get_latest_job(request, r)
        if latest_job is not None:
            data_dict['completed_job'] = reverse('eqsans.views.job_details', args=[latest_job.remote_id])
        try:
            run_id = int(data_dict['data_file'])
            data_dict['webmon_url'] = "https://monitor.sns.gov/report/eqsans/%s/" % run_id
        except:
            pass
        reductions.append(data_dict)
        
    # Get all user configurations
    config_list = ReductionConfiguration.objects.filter(owner=request.user,
                                                        experiments=experiment_obj).order_by('name')
    configurations = []
    for item in config_list:
        data_dict = item.get_data_dict()
        data_dict['id'] = item.id
        latest_jobs = RemoteJobSet.objects.filter(configuration=item)
        if len(latest_jobs)>0:
            latest_job = latest_jobs.latest('id')
            data_dict['latest_job'] = latest_job.id
            #data_dict['latest_job'] = reverse('eqsans.views.reduction_configuration_query', args=[latest_job.id])
        configurations.append(data_dict)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; %s" % ipts.lower()
    template_values = {'reductions': reductions,
                       'configurations': configurations,
                       'title': 'EQSANS %s' % ipts,
                       'breadcrumbs': breadcrumbs,
                       'ipts_number': ipts,
                       'back_url': reverse('eqsans.views.experiment', args=[ipts]),
                       'icat_info': icat_ipts,
                       'form': reduction_start_form,
                       'is_categorized': not IS_UNCATEGORIZED}
    if 'icat_error' in icat_ipts:
        template_values['user_alert'] = [icat_ipts['icat_error']]
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/experiment.html',
                              template_values)

@login_required
def delete_reduction(request, reduction_id):
    """
        Delete a reduction process entry
        @param request: request object
        @param reduction_id: primary key of reduction object
    """
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    reduction_proc.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('eqsans.views.reduction_home'))

@login_required
def reduction_options(request, reduction_id=None):
    """
        Display the reduction options form
        @param request: request object
        @param reduction_id: pk of reduction process object
    """
    # Get reduction and configuration information
    config_obj = None
    if reduction_id is not None:
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
        config_obj = reduction_proc.get_config()
    
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
                initial_values['experiment'] = request.GET['expt_name']
        options_form = forms.ReductionOptions(initial=initial_values)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')

    if config_obj is not None:
        breadcrumbs += " &rsaquo; <a href='%s'>configuration %s</a>" % (reverse('eqsans.views.reduction_configuration', args=[config_obj.id]), config_obj.id)
    if reduction_id is not None:
        breadcrumbs += " &rsaquo; reduction %s" % reduction_id
    else:
        breadcrumbs += " &rsaquo; new reduction"

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=['EQSANS', '0000'])
    icat_url = icat_url.replace('/0000','')
    #TODO: add New an Save-As functionality
    template_values = {'options_form': options_form,
                       'title': 'EQSANS Reduction',
                       'breadcrumbs': breadcrumbs,
                       'reduction_id': reduction_id,
                       'icat_url': icat_url }
    # Get existing jobs for this reduction
    if reduction_id is not None:
        existing_jobs = RemoteJob.objects.filter(reduction=reduction_proc)
        if len(existing_jobs)>0:
            template_values['existing_jobs'] = existing_jobs.order_by('id')
        template_values['expt_list'] = reduction_proc.experiments.all()
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_options.html',
                              template_values)

@login_required
def reduction_configuration(request, config_id=None):
    """
        Show the reduction properties for a given configuration,
        along with all the reduction jobs associated with it.
        
        @param request: The request object
        @param config_id: The ReductionConfiguration pk
    """
    # Create a form for the page
    default_extra = 1 if config_id is None and not (request.method == 'GET' and 'data_file' in request.GET) else 0
    try:
        extra = int(request.GET.get('extra', default_extra))
    except:
        extra = default_extra
    ReductionOptionsSet = formset_factory(forms.ReductionOptions, extra=extra)

    # The list of relevant experiments will be displayed on the page
    expt_list = None
    job_list = None
    # Deal with data submission
    if request.method == 'POST':
        options_form = ReductionOptionsSet(request.POST)
        config_form = forms.ReductionConfigurationForm(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid() and config_form.is_valid():
            # Save the configuration
            config_id = config_form.to_db(request.user, config_id)
            # Save the individual reductions
            for form in options_form:
                form.to_db(request.user, None, config_id)
            if config_id is not None:
                return redirect(reverse('eqsans.views.reduction_configuration', args=[config_id]))
        else:
            # There's a proble with the data, the validated form 
            # will automatically display what the problem is to the user
            pass
    else:
        # Deal with the case of creating a new configuration
        if config_id is None:
            initial_values = []
            if 'data_file' in request.GET:
                initial_values = [{'data_file': request.GET.get('data_file','')}]
            options_form = ReductionOptionsSet(initial=initial_values)
            initial_config = {}
            if 'experiment' in request.GET:
                initial_config['experiment'] = request.GET.get('experiment','')
            if 'reduction_name' in request.GET:
                initial_config['reduction_name'] = request.GET.get('reduction_name','')
            config_form = forms.ReductionConfigurationForm(initial=initial_config)
        # Retrieve existing configuration
        else:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
            initial_config = forms.ReductionConfigurationForm.data_from_db(request.user, reduction_config)
            
            initial_values = []
            for item in reduction_config.reductions.all():
                props = forms.ReductionOptions.data_from_db(request.user, item.pk)
                initial_values.append(props)
                
            options_form = ReductionOptionsSet(initial=initial_values)
            config_form = forms.ReductionConfigurationForm(initial=initial_config)
            expt_list = reduction_config.experiments.all()
            job_list = RemoteJobSet.objects.filter(configuration=reduction_config)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    if config_id is not None:
        breadcrumbs += " &rsaquo; configuration %s" % config_id
    else:
        breadcrumbs += " &rsaquo; new configuration"

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=['EQSANS', '0000'])
    icat_url = icat_url.replace('/0000','')
    #TODO: add New an Save-As functionality
    template_values = {'config_id': config_id,
                       'options_form': options_form,
                       'config_form': config_form,
                       'expt_list': expt_list,
                       'existing_job_sets': job_list,
                       'title': 'EQSANS Reduction',
                       'breadcrumbs': breadcrumbs,
                       'icat_url': icat_url }

    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_table.html',
                              template_values)
    
@login_required
def reduction_configuration_submit(request, config_id):
    """
        Submit all reductions for this configuration.
        @param request: request object
        @param config_id: pk of configuration
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reductions = reduction_config.reductions.all()
    if len(reductions)>0:
        # Start a new transaction
        transaction = remote.view_util.transaction(request, start=True)
        job_set = RemoteJobSet(transaction=transaction,
                               configuration=reduction_config)
        job_set.save()
        # Loop through the reductions and submit them
        for item in reductions:
            data = forms.ReductionOptions.data_from_db(request.user, item.id)
            code = forms.ReductionOptions.as_mantid_script(data, transaction.directory)
            jobID = remote.view_util.submit_job(request, transaction, code)
            if jobID is not None:
                job = RemoteJob(reduction=item,
                                remote_id=jobID,
                                properties=item.properties,
                                transaction=transaction)
                job.save()
                job_set.jobs.add(job)
    return redirect(reverse('eqsans.views.reduction_configuration', args=[config_id]))
    
@login_required
def reduction_configuration_query(request, remote_set_id):
    """
        Query all jobs in a job set
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>configuration %s</a>" % (reverse('eqsans.views.reduction_configuration', args=[job_set.configuration.id]), job_set.configuration.id)
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('eqsans.views.reduction_jobs')
    breadcrumbs += " &rsaquo; job results"
    
    template_values = {'remote_set_id': remote_set_id,
                       'configuration_title': job_set.configuration.name,
                       'configuration_id': job_set.configuration.id,
                       'breadcrumbs': breadcrumbs,
                       'title': 'EQSANS job results',
                       'trans_id': job_set.transaction.trans_id,
                       'job_directory': job_set.transaction.directory,
                       'back_url': request.path}
    
    # Get status of each job
    job_set_info = []
    first_job = None
    for item in job_set.jobs.all():
        job_info = remote.view_util.query_job(request, item.remote_id)
        if job_info is not None:
            first_job = item
            job_info['reduction_name'] = item.reduction.name
            job_info['reduction_id'] = item.reduction.id
            job_info['job_id'] = item.remote_id
            job_info['parameters'] = item.get_data_dict()
            job_set_info.append(job_info)
    template_values['job_set_info'] = job_set_info
    
    # Show list of files in the transaction
    template_values['job_files'] = remote.view_util.query_files(request, job_set.transaction.trans_id)

    # I(q) plots
    plot_data = []
    if first_job is not None and template_values['job_files'] is not None:
        for f in template_values['job_files']:
            if f.endswith('_Iq.txt'):
                plot_info = view_util.process_iq_output(request, first_job, 
                                                        template_values['trans_id'], f)
                plot_info['name'] = f
                plot_data.append(plot_info)
    template_values['plot_data'] = plot_data
 
    # Link to download all I(q) files
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_configuration_query.html', template_values)
    
@login_required
def reduction_configuration_iq(request, remote_set_id):
    """
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    files = remote.view_util.query_files(request, job_set.transaction.trans_id)
    
    str_io = StringIO.StringIO()
    output_zip_file = zipfile.ZipFile(str_io, 'w')
    for f in files:
        if f.endswith('_Iq.txt'):
            file_data = remote.view_util.download_file(request, job_set.transaction, f)
            fd = StringIO.StringIO()
            fd.write(file_data)
            output_zip_file.writestr(f, fd.getvalue())
            fd.close()
    output_zip_file.close()
    # Create response with correct MIME-type
    resp = HttpResponse(str_io.getvalue(), mimetype = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % 'iq_transaction_%s.zip' % job_set.transaction.trans_id
    str_io.close()
    return resp

@login_required
def reduction_configuration_job_delete(request, config_id, reduction_id):
    """
        Delete a reduction from a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
        @param reduction_id: pk of the reduction object
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    if reduction_proc in reduction_config.reductions.all():
        reduction_config.reductions.remove(reduction_proc)
        reduction_proc.delete()
    return redirect(reverse('eqsans.views.reduction_configuration', args=[config_id]))
    
@login_required
def reduction_configuration_delete(request, config_id):
    """
        Delete a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    for item in reduction_config.reductions.all():
        reduction_config.reductions.remove(item)
        item.delete()
    reduction_config.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('eqsans.views.reduction_home'))
    
@login_required
def reduction_script(request, reduction_id):
    """
        Display a script representation of a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='.'>reduction %s</a> &rsaquo; script" % reduction_id
    
    template_values = {'reduction_name': data['reduction_name'],
                       'breadcrumbs': breadcrumbs,
                       'code': forms.ReductionOptions.as_mantid_script(data) }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_script.html',
                              template_values)

@login_required
def py_reduction_script(request, reduction_id):
    """
        Return the python script for a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_mantid_script(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.py"'
    return response

@login_required
def xml_reduction_script(request, reduction_id):
    """
        Return the xml representation of a reduction process that the user
        can load into Mantid.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_xml(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.xml"'
    return response

@login_required
def submit_job(request, reduction_id):
    """
        Submit a reduction script to Fermi.

        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    #TODO: Make sure the submission errors are clearly reported
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
        template_values = reduction_service.view_util.fill_template_values(request, **template_values)
        return render_to_response('remote/failed_connection.html',
                                  template_values)

    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    code = forms.ReductionOptions.as_mantid_script(data, transaction.directory)
    jobID = remote.view_util.submit_job(request, transaction, code)
    if jobID is not None:
        job = RemoteJob(reduction=reduction_proc,
                        remote_id=jobID,
                        properties=reduction_proc.properties,
                        transaction=transaction)
        job.save()
    return redirect(reverse('eqsans.views.reduction_options', args=[reduction_id]))

@login_required
def job_details(request, job_id):
    """
        Show status of a given remote job.
        
        @param request: request object
        @param job_id: pk of the RemoteJob object
        
    """
    remote_job = get_object_or_404(RemoteJob, remote_id=job_id)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>reduction %s</a>" % (reverse('eqsans.views.reduction_options', args=[remote_job.reduction.id]), remote_job.reduction.id)
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('eqsans.views.reduction_jobs')
    breadcrumbs += " &rsaquo; %s" % job_id

    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values['title'] = "EQSANS job results"
    
    # Go through the files and find data to plot
    if 'job_files' in template_values and 'trans_id' in template_values:
        for f in template_values['job_files']:
            if f.endswith('_Iq.txt'):
                plot_info = view_util.process_iq_output(request, remote_job, 
                                                        template_values['trans_id'], f)
                template_values.update(plot_info)
            elif f.endswith('_Iqxy.nxs'):
                plot_info = view_util.process_iqxy_output(request, remote_job, 
                                                          template_values['trans_id'], f)
                template_values.update(plot_info)
    
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
        Return a list of the remote reduction jobs for EQSANS.
        The jobs are those that are owned by the user and have an
        entry in the database.
        
        @param request: request object
    """
    jobs = RemoteJob.objects.filter(transaction__owner=request.user)
    status_data = []
    for job in jobs:
        if not job.transaction.is_active or job.reduction.get_config() is not None:
            continue
        j_data = {'id': job.remote_id,
                  'name': job.reduction.name,
                  'reduction_id': job.reduction.id,
                  'start_date': job.transaction.start_time,
                  'data': job.reduction.data_file,
                  'trans_id': job.transaction.trans_id,
                  'experiments': job.reduction.get_experiments()
                 }
        status_data.append(j_data)
    
    # Get config jobs
    config_jobs = RemoteJobSet.objects.filter(transaction__owner=request.user)
    config_data = []
    for job in config_jobs:
        if not job.transaction.is_active:
            continue
        j_data = {'id': job.id,
                  'config_id': job.configuration.id,
                  'name': job.configuration.name,
                  'trans_id': job.transaction.trans_id,
                  'experiments': job.configuration.get_experiments()
                 }
        config_data.append(j_data)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; jobs"
    template_values = {'status_data': status_data,
                       'config_data': config_data,
                       'back_url': request.path,
                       'breadcrumbs': breadcrumbs}
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)   
    return render_to_response('eqsans/reduction_jobs.html',
                              template_values)

@login_required
def reduction_home(request):
    """
        Home page for the EQSANS reduction
        @param request: request object
    """
    eqsans = Instrument.objects.get(name='eqsans')
    experiments = Experiment.objects.experiments_for_instrument(eqsans, owner=request.user)

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; eqsans reduction" % reverse(settings.LANDING_VIEW)
    template_values = {'title': 'EQSANS Reduction',
                       'experiments':experiments,
                       'breadcrumbs': breadcrumbs}
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_home.html',
                              template_values)
