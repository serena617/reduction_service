from models import ReductionProcess, BoolReductionProperty, FloatReductionProperty, CharReductionProperty
from django.contrib import admin

class ReductionProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'timestamp', 'properties')
    
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
    
class ReductionPropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'reduction_link', 'value')

admin.site.register(ReductionProcess, ReductionProcessAdmin)
admin.site.register(BoolReductionProperty, ReductionPropertyAdmin)
admin.site.register(FloatReductionProperty, ReductionPropertyAdmin)
admin.site.register(CharReductionProperty, ReductionPropertyAdmin)
