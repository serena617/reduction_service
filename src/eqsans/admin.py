from models import ReductionProcess, Instrument, Experiment, BoolReductionProperty, FloatReductionProperty, CharReductionProperty, RemoteJob
from django.contrib import admin
import logging
import sys

class ReductionProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'timestamp', 'properties', 'get_experiments')
    
    def properties(self, obj):
        try:
            data = obj.get_data_dict()
            props = ''
            if 'data_file' in data:
                props += 'DAT=%s, ' % data['data_file']
            if 'subtract_background' in data and data['subtract_background'] is True:
                if 'background_file' in data:
                    props += "BCK=%s, " % data['background_file']
        except:
            return ''
        return props
    properties.short_description = "Properties"
    
    def get_experiments(self, obj):
        try:
            expts = []
            for item in obj.experiments.all():
                expts.append(str(item))
            return '.'.join(expts) 
        except:
            return ''
    get_experiments.short_description = "Experiments"
    
class ReductionPropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'reduction_link', 'value')

class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_instruments')
    def get_instruments(self, obj):
        try:
            instr = []
            for item in obj.instruments.all():
                instr.append(str(item))
            return ', '.join(instr) 
        except:
            return ''
    get_instruments.short_description = "Instruments"    

class RemoteJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'reduction', 'remote_id', 'get_plots')
    
    def get_plots(self, obj):
        plots_str = ''
        try:
            plot_list = obj.plots.all()
            if len(plot_list)>0:
                plots_str = str(plot_list[0])
                if len(plot_list)>1:
                    plots_str += '+'
        except:
            logging.error("RemoteJobAdmin: %s" % sys.exc_value)
        return ''
    get_plots.short_description = "Plots"
    
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    
admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(ReductionProcess, ReductionProcessAdmin)
admin.site.register(BoolReductionProperty, ReductionPropertyAdmin)
admin.site.register(FloatReductionProperty, ReductionPropertyAdmin)
admin.site.register(CharReductionProperty, ReductionPropertyAdmin)
admin.site.register(RemoteJob, RemoteJobAdmin)
