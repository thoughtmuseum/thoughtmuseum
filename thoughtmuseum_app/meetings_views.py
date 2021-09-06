# helper function for converting local django (UTC) time to various timezones
import datetime
import pytz
import logging

from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from thoughtmuseum_app.forms import TimezoneCalcForm, MeetingForm
from thoughtmuseum_app.models import TeacherProfile, Meeting, Timezone, ParentProfile
from thoughtmuseum_app.zoom import ZoomAPI

from .views import is_parent, is_customer, is_scheduler, is_teacher, _get_selected_user

from .reminder_views import _send_emails_for_meetings

logger = logging.getLogger(__name__)

def worldclock(timezones):
    fmt = '%Y-%m-%d %H:%M:%S'
    # get local time
    # Django gets local time in UTC
    # see 'settings.py':
    #   TIME_ZONE = "America/Los_Angeles"
    #   USE_TZ = True
    now_local = timezone.now()
    # convert to different timezones
    times = []
    for tmpzone in timezones:
        times.append(now_local.astimezone(pytz.timezone(tmpzone)).strftime(fmt))
    tz_times = zip(timezones, times)
    return tz_times


# checks if current user is in the 'scheduler' group
def in_scheduler_group(user):
    return user.groups.filter(name='scheduler').count() > 0


@user_passes_test(in_scheduler_group, login_url='/meetings')
def delete_meeting(request):
    if request.method == 'POST':
        zoom = ZoomAPI()
        m = Meeting.objects.get(pk=request.POST['meeting_id'])
        if zoom.delete_meeting(m.get_meeting_id()):
            m.delete()
        else:
            raise Exception('Zoom API error')
        return HttpResponse()
    else:
        raise Http404


# meeting overview
@login_required
def meetings(request):
    all_meetings = None
    past_meetings = []
    future_meetings = []
    user = _get_selected_user(request)    

    # retrieve timezone of user
    tz = Timezone.objects.get(user=user).get_timezone()
   
    if is_customer(user):
        # get all meetings and teacher pairs for current user, ordered by meeting_time
        all_meetings = Meeting.objects.filter(Q(student=user) |
                                              Q(student2=user) |
                                              Q(student3=user) |
                                              Q(student4=user) |
                                              Q(student5=user)).order_by('meeting_time')

    elif is_teacher(user):
        all_meetings = Meeting.objects.filter(teacher=user).order_by('meeting_time')
    elif is_scheduler(user):
        all_meetings = Meeting.objects.all().order_by('meeting_time')
    elif is_parent(request.user):
        parent = ParentProfile.objects.get(user=request.user)
        if parent.selected_child is None:
            all_meetings = Meeting.objects.filter(Q(student__in=parent.children.all()) 
                                        | Q(student2__in=parent.children.all()) 
                                        | Q(student3__in=parent.children.all()) 
                                        | Q(student4__in=parent.children.all()) 
                                        | Q(student5__in=parent.children.all())).order_by('meeting_time')    

    if all_meetings:
        fmt_date = '%Y-%m-%d'
        fmt_time = '%I:%M %p'
        for meeting in all_meetings:
            group_meeting = False
            student_name = u'{} {} '.format(meeting.student.first_name, meeting.student.last_name)
            if meeting.student2 or meeting.student3 or meeting.student4 or meeting.student5:
                group_meeting = True
            if is_scheduler(user):
                tz = Timezone.objects.get(user=meeting.student).get_timezone()
            elif is_parent(request.user):
                parent = ParentProfile.objects.get(user=request.user)
                if parent.selected_child is None:
                    tz = Timezone.objects.get(user=request.user).get_timezone()
                    student_name = meeting.get_students_first_name_for_parent(parent)
                else:
                    student_name = u'{}'.format(meeting.student.first_name)            
            meeting_datetime = meeting.meeting_time.astimezone(tz)
            meeting_date = meeting_datetime.date().strftime(fmt_date)
            meeting_time = meeting_datetime.time().strftime(fmt_time)
            teacher_name = u'{} {} '.format(meeting.teacher.first_name, meeting.teacher.last_name)            
                
            tmp_meeting = {
                'id': meeting.id,
                'date': meeting_date,
                'time': meeting_time,
                'student_name': student_name,
                'teacher_name': teacher_name,
                'join_url': meeting.join_url,
                'start_url': meeting.start_url,
                'group': '+' if group_meeting else '',
                'meeting_id': meeting.get_meeting_id(),
                'meeting_password': meeting.meeting_password,
            }
            if meeting_datetime < timezone.now() - datetime.timedelta(days=0, hours=1, minutes=0):
                past_meetings.append(tmp_meeting)
            else:
                future_meetings.append(tmp_meeting)
        # reverse order of past meetings to have the most recent first
        past_meetings.reverse()

    return render(request, 'meetings.html',
                  {'past_meetings': past_meetings,
                   'future_meetings': future_meetings,
                   'timezone': str(tz),
                   })


@login_required
def ajax_get_recordings(request):
    zoom = ZoomAPI()
    recordings = zoom.retrieve_recordings(request.GET['meeting_id'])
    return render(request, 'meetings/recordings.html', {'recs': recordings})


# meeting scheduling and timezone overview
@user_passes_test(in_scheduler_group, login_url='/meetings')
def scheduler(request):
    collision_meetings = []
    zoom = ZoomAPI()
    timezones = pytz.all_timezones_set

    tz_times = worldclock(timezones)
    time_student = None
    time_teacher = None
    not_scheduled_meeting_date = None
    success = ''
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form2 = TimezoneCalcForm(request.POST)
        form1 = MeetingForm(request.POST)
        if 'meeting-setup' in request.POST:

            if form1.is_valid():
                # grab data from form1 and populate model
                new_meeting = Meeting(
                    teacher=form1.cleaned_data['teacher'],
                    student=form1.cleaned_data['student'], )
                new_meeting.setup_time = timezone.now()

                new_meeting.student2 = form1.cleaned_data['student2']
                new_meeting.student3 = form1.cleaned_data['student3']
                new_meeting.student4 = form1.cleaned_data['student4']
                new_meeting.student5 = form1.cleaned_data['student5']
                new_meeting.duration = int(form1.cleaned_data['duration'])

                #         )
                # # add values not included on form1
                # calculate meeting time
                # grab hours from form
                tmp_hour = form1.cleaned_data.get('meeting_hour')
                tmp_hour = dict(form1.fields['meeting_hour'].choices)[tmp_hour]
                # grab minuted from form1
                tmp_min = form1.cleaned_data['meeting_minute']
                tmp_min = dict(form1.fields['meeting_minute'].choices)[tmp_min]
                # grab meridiem from form1
                tmp_mer = form1.cleaned_data['meeting_meridiem']
                tmp_mer = dict(form1.fields['meeting_meridiem'].choices)[tmp_mer]
                # Convert hours from 12 hour to 24 hour form1at
                tmp_hour = int(tmp_hour)
                if tmp_mer == 'pm':
                    if tmp_hour < 12:
                        tmp_hour += 12
                else:
                    if tmp_hour == 12:
                        tmp_hour = 0
                tmp_hour = str(tmp_hour)
                # grab date from form1
                tmp_date = form1.cleaned_data.get('meeting_date')
                # merge entries and use strptime to convert to datetime object
                tmp_datetime = str(tmp_date) + ' ' + str(tmp_hour).zfill(2) + ':' + str(tmp_min).zfill(2)
                date_object = datetime.datetime.strptime(tmp_datetime, '%Y-%m-%d %H:%M')
                # retrieve timezone of student
                tz = Timezone.objects.filter(user=form1.cleaned_data['student']).values_list('timezone', flat=True)[0]
                tz = pytz.timezone(Timezone.MY_CHOICES[int(tz)][1])
                # Attach timezone information of student to meeting time
                date_obj = tz.localize(date_object)
                # Convert meeting time to UTC (django default)
                fmt = '%Y-%m-%d %H:%M:%S %Z%z'
                date_object_utc = date_obj.astimezone(pytz.timezone('UTC'))
                # Save meeting time in UTC to model
                new_meeting.meeting_time = date_object_utc
                # # redirect to a new URL:
                # return HttpResponseRedirect('/thanks/')
                # return HttpResponseRedirect(reverse('meetings.views.scheduler'))
                #
                # use submitted date to call zoom api and create meeting
                #
                # query data base for number of meetings for the particular student
                number_of_meetings = len(Meeting.objects.filter(student=form1.cleaned_data['student']))
                # similarly the timezone, e.g. 'GMT-7:00'
                fmt = '%Z%z'
                tmp_timezone = date_object_utc.strftime(fmt)
                # make call to zoom api
                # get zoom host user-id from teacher profile
                zoom_host_user_id = \
                    TeacherProfile.objects.filter(user=form1.cleaned_data['teacher']).values_list('zoom_host_user_id',
                                                                                                  flat=True)[0]

                # Week
                if form1.cleaned_data['repeat_interval'] == '1':
                    week = datetime.timedelta(days=7)
                    success_count = 0
                    repeat_number = int(form1.cleaned_data['repeat_number'])  
                    not_scheduled_meeting_date = []                 
                    for index in range(1, repeat_number + 1):
                        new_meeting.pk = None
                        new_meeting.meeting_date = new_meeting.meeting_time
                        new_meeting.topic = 'Meeting Number ' + str(number_of_meetings + index)
                        # meeting date and time need specific format: '2016-3-21T21:00:00Z'
                        #response = zoom.create_meeting(new_meeting.meeting_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        #                               new_meeting.topic, tmp_timezone, zoom_host_user_id)
                        response = {'start_url':'https://zoom.us/s/84394292629', 
                                    'join_url':'https://us02web.zoom.us/j/84394292629?pwd=T1piV3BySEtFZkQyZlRmUC9SNGdZdz09',
                                    'password': 'qz51ji',
                                    'id': '843 9429 2629' }
                        # get response and extract join_url if no errors
                        if 'join_url' in response.keys():
                            success_count += 1
                            new_meeting.start_url = str(response['start_url'])
                            new_meeting.join_url = str(response['join_url'])
                            new_meeting.meeting_password = response.get('password', '')
                            new_meeting.meeting_id =  response.get('id', '')
                            new_meeting.save()
                            collision_meetings += is_teacher_date_collision(new_meeting)                            
                            check_if_it_is_less_than_24h_to_meeting(new_meeting)
                        else:                            
                            logger.error('Zoom API response: {}'.format(response))
                            not_scheduled_meeting_date.append(new_meeting.get_meeting_date_time_for_the_user_time_zone(new_meeting.student))
                        new_meeting.meeting_time += week
                        

                    if success_count == repeat_number:
                        if repeat_number == 1:
                            success = 'Your meeting has been scheduled.'
                        else:
                            success = 'Your meetings has been scheduled.'
                    else:
                        success = 'Not all of your meetings have been scheduled !'

        elif 'student_to_teacher' in request.POST or 'teacher_to_student' in request.POST:
            if form2.is_valid():

                if 'student_to_teacher' in request.POST:
                    # Convert student time to teacher time
                    # grab student info from form2
                    tz_origin = form2.cleaned_data.get('student_timezone')
                    tz_origin = dict(form2.fields['student_timezone'].choices)[tz_origin]
                    tz_target = form2.cleaned_data.get('teacher_timezone')
                    tz_target = dict(form2.fields['teacher_timezone'].choices)[tz_target]
                    tmp_hour = form2.cleaned_data.get('student_hour')
                    tmp_hour = dict(form2.fields['student_hour'].choices)[tmp_hour]
                    tmp_min = form2.cleaned_data.get('student_min')
                    tmp_min = dict(form2.fields['student_min'].choices)[tmp_min]
                    tmp_mer = form2.cleaned_data.get('student_meridiem')
                    tmp_mer = dict(form2.fields['student_meridiem'].choices)[tmp_mer]

                if 'teacher_to_student' in request.POST:
                    # Convert teacher time to student time
                    # grab teacher info from form2
                    tz_origin = form2.cleaned_data.get('teacher_timezone')
                    tz_origin = dict(form2.fields['teacher_timezone'].choices)[tz_origin]
                    tz_target = form2.cleaned_data.get('student_timezone')
                    tz_target = dict(form2.fields['student_timezone'].choices)[tz_target]
                    tmp_hour = form2.cleaned_data.get('teacher_hour')
                    tmp_hour = dict(form2.fields['teacher_hour'].choices)[tmp_hour]
                    tmp_min = form2.cleaned_data.get('teacher_min')
                    tmp_min = dict(form2.fields['teacher_min'].choices)[tmp_min]
                    tmp_mer = form2.cleaned_data.get('teacher_meridiem')
                    tmp_mer = dict(form2.fields['teacher_meridiem'].choices)[tmp_mer]

                # grab date from form2
                tmp_date = form2.cleaned_data.get('tmp_date')
                # Convert hours from 12 hour to 24 hour form2at
                print('Date as set', tmp_date)
                tmp_hour = int(tmp_hour)
                if tmp_mer == 'pm':
                    if tmp_hour < 12:
                        tmp_hour += 12
                else:
                    if tmp_hour == 12:
                        tmp_hour = 0
                tmp_hour = str(tmp_hour)
                # merge with date and convert to datetime object
                tmp_datetime = str(tmp_date) + ' ' + str(tmp_hour).zfill(2) + ':' + str(tmp_min).zfill(2)
                date_object = datetime.datetime.strptime(tmp_datetime, '%Y-%m-%d %H:%M')
                print('Complete detobject', date_object)
                # Attach timezone information to time
                print('Timezone of origin', tz_origin)
                tz = pytz.timezone(tz_origin)
                print('Timezone of target', tz_target)
                date_obj = tz.localize(date_object)
                print('Localized dateobject', date_object)
                # convert datetime to UTC timezone
                date_object_utc = date_obj.astimezone(pytz.timezone('UTC'))
                # convert UTC to target timezone
                date_object_target = date_object_utc.astimezone(pytz.timezone(tz_target))
                #
                print('Time at target:', date_object_target)
                # Origin
                day_origin = date_obj.day
                print('Day origin:', day_origin)
                hour_origin = date_obj.hour
                if hour_origin > 12:
                    hour_origin = hour_origin % 12
                    meridiem_origin = 'pm'
                elif hour_origin == 12:
                    meridiem_origin = 'pm'
                else:
                    meridiem_origin = 'am'
                hour_origin = str(hour_origin)
                min_origin = str(date_obj.minute).zfill(2)
                time_origin = hour_origin + ':' + min_origin + ' ' + meridiem_origin
                # Target
                day_target = date_object_target.day
                print('Day target:', day_target)
                hour_target = date_object_target.hour
                if hour_target > 12:
                    hour_target = hour_target % 12
                    meridiem_target = 'pm'
                elif hour_target == 12:
                    meridiem_target = 'pm'
                else:
                    meridiem_target = 'am'
                hour_target = str(hour_target)
                min_target = str(date_object_target.minute).zfill(2)
                time_target = hour_target + ':' + min_target + ' ' + meridiem_target
                # Check for date change
                if day_origin == day_target:
                    pass
                elif day_origin < day_target:
                    time_target = time_target + ' (+1 Day)'
                elif day_origin > day_target:
                    time_target = time_target + ' (-1 Day)'
                if 'student_to_teacher' in request.POST:
                    time_student = time_origin
                    time_teacher = time_target
                if 'teacher_to_student' in request.POST:
                    time_teacher = time_origin
                    time_student = time_target

    # if a GET (or any other method) we'll create a blank form
    else:
        form1 = MeetingForm()
        form2 = TimezoneCalcForm()

    return render(request,
                  'scheduler.html',
                  {'form1': form1,
                   'form2': form2,
                   'tz_times': tz_times,
                   'time_student': time_student,
                   'time_teacher': time_teacher,
                   'success': success,
                   'not_scheduled_meeting_date': not_scheduled_meeting_date,
                   'collision_meetings':collision_meetings if len(collision_meetings) > 0 else None,})


def check_if_it_is_less_than_24h_to_meeting(meeting):  
    if meeting.meeting_time < timezone.now() + datetime.timedelta(days=0, hours=24, minutes=0):
        _send_emails_for_meetings([meeting]) 


def is_teacher_date_collision(meeting):
    collision_meetings = set()
   
    col_meet = Meeting.objects.filter(teacher=meeting.teacher,                       
                        meeting_time__lte=meeting.meeting_time + datetime.timedelta(days=0, hours=5, minutes=0),
                        meeting_time__gte=meeting.meeting_time - datetime.timedelta(days=0, hours=4, minutes=0)
                        ).exclude(id=meeting.id)     
    
    for cm in col_meet:       
        if cm.meeting_end_time() > meeting.meeting_time and cm.meeting_end_time() < meeting.meeting_end_time():
            collision_meetings.add(cm)

    for cm in col_meet:       
        if cm.meeting_end_time() > meeting.meeting_end_time() and cm.meeting_time < meeting.meeting_end_time():
            collision_meetings.add(cm)
   
    for cm in col_meet:     
        if cm.meeting_time >=  meeting.meeting_time and cm.meeting_time < meeting.meeting_end_time():
            collision_meetings.add(cm)    
    
    return collision_meetings
