from django.core.urlresolvers import reverse
import users.view_util
import remote.view_util

def fill_template_values(request, **template_args):
    """
        Fill template values for the whole application
    """
    template_args = users.view_util.fill_template_values(request, **template_args)
    template_args = remote.view_util.fill_template_values(request, **template_args)
    template_args['reduction_apps'] = [{'name':'eqsans',
                                        'url': reverse('eqsans.views.reduction_home')}]
    return template_args