from django import forms
from .models import TeacherProfile, CustomerProfile, ParentProfile
from django.forms import ModelForm
from django.contrib.auth.models import User

                
class UserEditForm(ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        
    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)
        super(UserEditForm, self).__init__(*args, **kwargs)
        if disabled:
            for f in self.fields:
                self.fields[f].widget.attrs['disabled'] = 'true'  


class CustomerProfileForm(ModelForm):
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        exclude = ['user']
        widgets = {
            #'address': forms.Textarea(attrs={'cols': 80, 'rows': 6}),
        }
        
    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
        if disabled:
            for f in self.fields:
                self.fields[f].widget.attrs['disabled'] = 'true'  


class TeacherProfileForm(ModelForm):
    class Meta:
        model = TeacherProfile
        fields = '__all__'
        exclude = ['user','photo','zoom_host_user_id']
        widgets = {
            'address': forms.Textarea(attrs={'cols': 80, 'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)
        super(TeacherProfileForm, self).__init__(*args, **kwargs)
        if disabled:
            for f in self.fields:
                self.fields[f].widget.attrs['disabled'] = 'true'  


class ParentProfileForm(ModelForm):
    class Meta:
        model = ParentProfile
        fields = '__all__'
        exclude = ['user', 'selected_child']
        
        
    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)
        super(ParentProfileForm, self).__init__(*args, **kwargs)        
        self.fields["children"].queryset = User.objects.filter(parentprofile__id = self.instance.id)
        if disabled:
            for f in self.fields:
                self.fields[f].widget.attrs['disabled'] = 'true'  