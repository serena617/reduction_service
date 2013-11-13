from django import forms
from django.shortcuts import get_object_or_404
from models import ReductionProcess, BoolReductionProperty, FloatReductionProperty, CharReductionProperty

class ReductionOptions(forms.Form):
    """
        Simple form to select a data file on the user's machine
    """
    # Reduction name
    reduction_name = forms.CharField(required=False)
    # General options
    absolute_scale = forms.FloatField(required=False, initial=1.0)
    dark_current_run = forms.CharField(required=False)
    sample_aperture = forms.FloatField(required=False)
    
    # Beam center
    beam_center_x = forms.FloatField(required=False)
    beam_center_y = forms.FloatField(required=False)
    fit_direct_beam = forms.BooleanField(required=False, initial=True)
    direct_beam_run = forms.CharField(required=False)
    
    # Sensitivity
    
    
    # Data
    
    
    # Background
    
    def as_xml(self):
        """
        """
        pass
    
    def as_mantid_script(self):
        """
            Return the Mantid script associated with the current parameters
        """
        pass

    def to_db(self, user, reduction_id=None):
        """
        """
        if not self.is_valid():
            raise RuntimeError, "Reduction options form invalid"
        
        # Find or create a reduction process entry and update it
        if reduction_id is not None:
            reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
        else:
            # Make sure we don't try to store a string that's longer than allowed
            reduction_proc = ReductionProcess(owner=user)
        reduction_proc.name=self.cleaned_data['reduction_name'][:128]
        reduction_proc.save()
        
        # Clean up the old values
        FloatReductionProperty.objects.filter(reduction=reduction_proc).delete()
        BoolReductionProperty.objects.filter(reduction=reduction_proc).delete()
        CharReductionProperty.objects.filter(reduction=reduction_proc).delete()

        # Set the parameters associated with the reduction process entry
        for name, field in self.fields.items():
            if name == 'reduction_name': continue
            property_cls = None
            if isinstance(field, forms.FloatField):
                property_cls = FloatReductionProperty
            elif isinstance(field, forms.CharField):
                property_cls = CharReductionProperty
            elif isinstance(field, forms.BooleanField):
                property_cls = BoolReductionProperty
            if property_cls is not None and self.cleaned_data[name] is not None:
                property_cls(reduction=reduction_proc,
                             name=name,
                             value=self.cleaned_data[name]).save()
        return reduction_proc.pk
    
    @classmethod
    def data_from_db(cls, user, reduction_id):
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
        data = {}
        data['reduction_name'] = reduction_proc.name
        
        # Go through the list of reduction parameters
        params = FloatReductionProperty.objects.filter(reduction=reduction_proc)
        for p in params:
            data[p.name] = p.value
        params = CharReductionProperty.objects.filter(reduction=reduction_proc)
        for p in params:
            data[p.name] = p.value
        params = BoolReductionProperty.objects.filter(reduction=reduction_proc)
        for p in params:
            data[p.name] = p.value
        
        return data

        