# By convention, teachers set up meeting times in the student's time zone.
# In the teachers view, provide upcoming meeting times in PT and ET.
import pytz
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

from thoughtmuseum_app.models import Timezone, Meeting


class MeetingForm(forms.ModelForm):
    REPEAT_NUMBER_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    )

    REPEAT_INTERVAL_CHOICES = (
        ('1', 'week'),
        #     ('2',  'month'),
    )
    MERIDIEM_CHOICES = (
        ('1', 'am'),
        ('2', 'pm')
    )

    DURATION =(
        ('15', 15),
        ('30', 30),
        ('45', 45),
        ('60', 60),
        ('75', 75),
        ('90', 90),
        ('105', 105),
        ('120', 120),
    )

    HOUR_CHOICES = tuple((str(n), str(n)) for n in range(1, 13, 1))
    MINUTE_CHOICES = tuple((str(idx), str(n).zfill(2)) for idx, n in enumerate(range(0, 60, 1)))
    meeting_hour = forms.ChoiceField(choices=HOUR_CHOICES, initial='2')
    meeting_minute = forms.ChoiceField(choices=MINUTE_CHOICES, initial='0')
    meeting_meridiem = forms.ChoiceField(choices=MERIDIEM_CHOICES)
    duration = forms.ChoiceField(choices=DURATION, initial='60')
    # two fields not in model to handle repeated meetings
    repeat_number = forms.ChoiceField(choices=REPEAT_NUMBER_CHOICES)
    repeat_interval = forms.ChoiceField(choices=REPEAT_INTERVAL_CHOICES)

    DISABLED = ['meeting_hour', 'meeting_minute', 'meeting_meridiem', 'repeat_number', 'repeat_interval', 'teacher',
                'meeting_date', 'meeting_time']

    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', False)
        super(MeetingForm, self).__init__(*args, **kwargs)
        if disabled:
            for f in self.DISABLED:
                self.fields[f].widget.attrs['disabled'] = 'true'
                self.fields[f].required = False
            self.fields['meeting_date'].widget.attrs['id'] = ''  # remove datepicker id
        for f in self.fields:
            self.fields[f].widget.attrs['class'] = 'form-control'
        if self.instance and self.instance.pk:
            tz = Timezone.objects.get(user=self.instance.student).get_timezone()
            self.instance.meeting_time = self.instance.meeting_time.astimezone(tz)

    class Meta:
        model = Meeting
        fields = '__all__'
        widgets = {
            'meeting_time': forms.TimeInput(format='%I:%M %p'),
            'meeting_date': forms.DateInput(attrs={'type': 'text',
                                                   'id': 'datepicker', 'name': 'meeting_date'}, format='%m/%d/%Y'),
        }


class TimezoneCalcForm(forms.Form):
    tzs = list(pytz.all_timezones_set)
    tzs.sort(key=str.lower)
    TIMEZONE_CHOICES = tuple((str(idx), str(n)) for idx, n in enumerate(tzs))

    tmp_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'text',
                                                             'id': 'datepicker1', 'name': 'tmp_date'},
                                                      format='%m/%d/%Y'),
                               input_formats=('%m/%d/%Y',), initial=timezone.now)

    student_timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, initial='0')
    student_hour = forms.ChoiceField(choices=MeetingForm.HOUR_CHOICES, initial='2')
    student_min = forms.ChoiceField(choices=MeetingForm.MINUTE_CHOICES, initial='0')
    student_meridiem = forms.ChoiceField(choices=MeetingForm.MERIDIEM_CHOICES, initial='0')

    teacher_timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, initial='0')
    teacher_hour = forms.ChoiceField(choices=MeetingForm.HOUR_CHOICES, initial='2')
    teacher_min = forms.ChoiceField(choices=MeetingForm.MINUTE_CHOICES, initial='0')
    teacher_meridiem = forms.ChoiceField(choices=MeetingForm.MERIDIEM_CHOICES, initial='0')

    def __init__(self, *args, **kwargs):
        super(TimezoneCalcForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs['class'] = 'form-control'
        tz_users = Timezone.objects.all().order_by('timezone').distinct().values_list('timezone', flat=True)
        tz_choices = [(tz, self.tzs[int(tz)]) for tz in tz_users]
        self.fields['student_timezone'].choices = tz_choices
        self.fields['teacher_timezone'].choices = tz_choices
        
        
class ContactForm(forms.Form):
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Phone')
    comments = forms.CharField(label='Comments', widget=forms.Textarea(attrs={'cols': 80, 'rows': 6}))

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            label = self.fields.get(f).label 
            self.fields[f].widget.attrs['class']='form-control'
            self.fields[f].widget.attrs['placeholder']=label
    
    class Meta:
        widgets = {
            'comments': forms.Textarea(attrs={'cols': 80, 'rows': 6, 'placeholder':'Comments'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.TextInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone'})
            }


class CalendarSearchForm(forms.Form):    
    teacher_choice = [(choice.pk, choice.get_full_name()) for choice in User.objects.filter(groups__name='teacher').order_by('first_name')]
    teacher_choice.insert(0, ('0','----'))
    customer_choice = [(choice.pk, choice.get_full_name()) for choice in User.objects.filter(groups__name='customer').order_by('first_name')]
    customer_choice.insert(0, ('0','----'))
    
    teacher = forms.ChoiceField(choices=teacher_choice)
    student = forms.ChoiceField(choices=customer_choice)
   
    def __init__(self, *args, **kwargs):
        super(CalendarSearchForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs['class']='form-control'
