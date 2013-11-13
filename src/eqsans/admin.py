from models import ReductionProcess, BoolReductionProperty, FloatReductionProperty, CharReductionProperty
from django.contrib import admin

class ReductionProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'timestamp')

class ReductionPropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'reduction_link', 'value')

admin.site.register(ReductionProcess, ReductionProcessAdmin)
admin.site.register(BoolReductionProperty, ReductionPropertyAdmin)
admin.site.register(FloatReductionProperty, ReductionPropertyAdmin)
admin.site.register(CharReductionProperty, ReductionPropertyAdmin)
