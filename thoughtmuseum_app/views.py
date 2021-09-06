import datetime
import json
import logging

import pytz
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from .flexiquiz import FlexiQuizAPI
from .models import Timezone, CustomerProfile, TeacherProfile, Meeting, ParentProfile, Class, Exam, FlexiQuizUser, \
    FlexiquizResponse
from django.contrib.auth.models import User
from .forms_my_profile import UserEditForm, CustomerProfileForm, TeacherProfileForm, ParentProfileForm
from .forms import ContactForm, CalendarSearchForm
from django.core.mail.message import EmailMessage
from Thoughtmuseum.settings import  DEFAULT_FROM_EMAIL
from avatar.forms import PrimaryAvatarForm, DeleteAvatarForm, UploadAvatarForm
from avatar.signals import avatar_updated
from avatar.views import _get_avatars
from avatar.utils import get_default_avatar_url
from avatar.models import Avatar
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib.auth import logout as _logout

logger = logging.getLogger(__name__)


def is_teacher(user):
    return user.groups.filter(name='teacher').exists()


def is_customer(user):
    return user.groups.filter(name='customer').exists()


def is_scheduler(user):
    return user.groups.filter(name='scheduler').exists()


def is_parent(user):
    return user.groups.filter(name='parent').exists()


def _send_mail_contact_form(data):
    message = data['comments']
    subject = u'Contact request from: {} {} {} {}'.format(data['first_name'], data['last_name'], data['email'],
                                                          data['phone'])
    mail = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, [DEFAULT_FROM_EMAIL, ])
    return mail.send(fail_silently=True)


def index2(request):
    return render(request, 'index2.html', {})


def dashboard2(request):
    return render(request, 'dashboard2.html', {})

@csrf_exempt
def classPage(request):
    quiz_id = 'a207e8dd-0dd7-48ba-934c-96c0f688a983'
    r = None
    if request.method == 'POST':
        jwt_token = FlexiQuizAPI.sso_token(request.user)
        redirect_url = 'https://www.flexiquiz.com/account/auth?jwt={}&quiz_id={}'.format(jwt_token, quiz_id)
        return HttpResponseRedirect(redirect_url)
    try:
        exam = Exam.objects.get(quiz_id=quiz_id)
        r = exam.get_results(request.user)
        print(r.last())
    except:
        pass

    return render(request, 'classPage.html', {'r':r.last()})


def _save_response(data):
    has_pass = data.pop('pass')
    data['has_pass'] = has_pass
    response = FlexiquizResponse.objects.create(**data)
    user = User.objects.get(username=response.user_name)
    try:
        exam = Exam.objects.get(quiz_id=response.quiz_id)
        exam.taken.add(user)
        exam.save()
    except ObjectDoesNotExist:
        pass


@csrf_exempt
def flexiquiz_webhook(request):
    logger.debug(request)
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        if data['event_type'] == 'response.submitted':
            _save_response(data['data'])
    return HttpResponse('OK')


@login_required
def my_courses(request):
    if request.user.username == 'janet_example':
        return dashboard2(request)
    classes = request.user.user_classes.all()
    exams_taken = request.user.exams_taken.all()
    if request.method == 'POST':
        exam = Exam.objects.get(pk=request.POST['exam_id'])
        if 'enroll' in request.POST:
            api = FlexiQuizAPI()
            try:
                flexiquiz_user = request.user.flexiquiz_user
                flexiquiz_user_id = flexiquiz_user.flexiquiz_user_id
            except ObjectDoesNotExist:
                create_user = api.create_user(request.user)
                flexiquiz_user_id = create_user.get('user_id')
                if flexiquiz_user_id:
                    obj = FlexiQuizUser(user=request.user, flexiquiz_user_id=flexiquiz_user_id)
                    obj.save()
            if flexiquiz_user_id:
                assign_quiz = api.assign_quiz(flexiquiz_user_id, exam.quiz_id)
                if assign_quiz:
                    exam.enrolled.add(request.user)
        elif 'take' in request.POST:
            quiz_id = exam.quiz_id
            jwt_token = FlexiQuizAPI.sso_token(request.user)
            redirect_url = 'https://www.flexiquiz.com/account/auth?jwt={}&quiz_id={}'.format(jwt_token, quiz_id)
            return HttpResponseRedirect(redirect_url)

    return render(request, 'my_courses.html', {'classes': classes, 'exams_taken': exams_taken})


@login_required
def dashboard(request):
    if request.user.username == 'janet_example':
        return index2(request)
    all_meetings = []
    fmt_date = '%a, %B %d %Y'
    fmt_time = '%I:%M %p'
    meeting_datetime = 'No booked lesson'
    teacher_name = ''
    parent = None

    if 'avatar' not in request.session:
        _set_session_user_data(request, request.user)

    tz = Timezone.objects.get(user=_get_selected_user(request)).get_timezone()

    if is_customer(request.user):
        # get all meetings and teacher pairs for current user, ordered by meeting_time
        all_meetings = _get_student_meetings(request.user)
    elif is_teacher(request.user):
        all_meetings = Meeting.objects.filter(teacher=request.user).order_by('meeting_time')
    elif is_parent(request.user):
        parent = ParentProfile.objects.get(user=request.user)
        if 'children' not in request.session:
            children = []
            for ch in parent.children.all():
                children.append((ch.id, ch.first_name))
            request.session['children'] = children
        if parent.selected_child:
            all_meetings = _get_student_meetings(parent.selected_child)

    for meeting in all_meetings:
        if meeting.meeting_time > timezone.now():
            meeting_datetime = meeting.meeting_time.astimezone(tz)
            meeting_date = meeting_datetime.date().strftime(fmt_date)
            meeting_time = meeting_datetime.time().strftime(fmt_time)
            meeting_datetime = u'{} {}'.format(meeting_datetime.time().strftime(fmt_time),
                                               meeting_datetime.date().strftime(fmt_date))
            if is_customer(request.user) or (is_parent(request.user) and parent and parent.selected_child):
                teacher_name = u'With {} {} '.format(meeting.teacher.first_name, meeting.teacher.last_name)
            break

    return render(request, 'dashboard.html',
                  {
                      'meeting_datetime': meeting_datetime,
                      'teacher_name': teacher_name,
                  })


@login_required
def select_user(request, user_id):
    if is_parent(request.user):
        parent = ParentProfile.objects.get(user=request.user)
        if request.user.id == user_id:
            parent.selected_child = None
            _set_session_user_data(request, request.user)
        else:
            _selected_user = User.objects.get(pk=user_id)
            parent.selected_child = _selected_user
            _set_session_user_data(request, _selected_user)
        parent.save()

    return HttpResponseRedirect('/')


@login_required
def calendar(request):
    _is_scheduler = is_scheduler(request.user)

    if request.method == 'POST':
        calendarSearchForm = CalendarSearchForm(request.POST)
    else:
        calendarSearchForm = CalendarSearchForm()

    tz = None if _is_scheduler else Timezone.objects.get(user=request.user).get_timezone()

    return render(request, 'calendar.html', {'calendarSearch': calendarSearchForm,
                                             'isScheduler': _is_scheduler,
                                             'timezone': str(tz), })


@login_required
def get_calendar(request):
    data = []
    user = _get_selected_user(request)
    tz = Timezone.objects.get(user=user).get_timezone()
    if request.method == "GET":
        start = request.GET.get("start", "2000-01-01")
        end = request.GET.get("end", "2100-01-01")

        if len(start) > 8:
            start = start.split('T')[0]
        if len(end) > 8:
            end = end.split('T')[0]

        start = datetime.datetime.strptime(start, "%Y-%m-%d")
        end = datetime.datetime.strptime(end, "%Y-%m-%d")

        if is_customer(user):
            metting = Meeting.objects.filter(Q(meeting_date__gte=start), Q(meeting_date__lte=end),
                                             Q(student=user) | Q(student2=user) | Q(student3=user) | Q(
                                                 student4=user) | Q(student5=user))
            for m in metting:
                url = m.join_url
                className = ''
                tdelta = timedelta(hours=2)
                if (now() - m.meeting_time) > tdelta:
                    url = ''
                    className = 'calendar-event-disabled'
                data.append({'id': m.id,
                             'title': m.get_meeting_time_for_the_student() + ' {}min '.format(
                                 m.duration) + m.teacher.get_full_name(),
                             'url': url,
                             'className': className,
                             'start': m.meeting_time.astimezone(tz),
                             'end': m.meeting_time.astimezone(tz) + datetime.timedelta(minutes=m.duration),
                             })

        if is_teacher(user):
            data = []
            metting = Meeting.objects.filter(Q(meeting_date__gte=start), Q(meeting_date__lte=end), Q(teacher=user))
            for m in metting:
                title = m.get_meeting_time_for_the_teacher() + ' {}min '.format(m.duration) + m.get_students_name()
                url = m.start_url
                className = ''
                tdelta = timedelta(hours=2)
                if (now() - m.meeting_time) > tdelta:
                    url = ''
                    className = 'calendar-event-disabled'
                data.append({'id': m.id,
                             'title': title,
                             'url': url,
                             'className': className,
                             'start': m.meeting_time.astimezone(tz),
                             'end': m.meeting_time.astimezone(tz) + datetime.timedelta(minutes=m.duration),
                             })

        if is_scheduler(user):
            data = []
            teacher_id = int(request.GET.get("teacher_id", 0))
            student_id = int(request.GET.get("student_id", 0))
            metting = Meeting.objects.filter(Q(meeting_date__gte=start), Q(meeting_date__lte=end))
            if teacher_id > 0:
                metting = metting.filter(teacher__id=teacher_id)
            if student_id > 0:
                metting = metting.filter(
                    Q(student__id=student_id) | Q(student2__id=student_id) | Q(student3__id=student_id) | Q(
                        student4__id=student_id) | Q(student5__id=student_id))

            for m in metting:
                title = m.get_meeting_time_for_the_teacher() + " " + m.get_meeting_time_for_the_student() + ' {}min '.format(
                    m.duration) + m.teacher.get_full_name() + " with " + m.get_students_name()
                tz = pytz.timezone('PST8PDT')  # Timezone.objects.get(user=m.student).get_timezone()
                url = m.join_url
                className = ''
                tdelta = timedelta(hours=2)
                if (now() - m.meeting_time) > tdelta:
                    url = ''
                    className = 'calendar-event-disabled'
                data.append({'id': m.id,
                             'title': title,
                             'url': url,
                             'className': className,
                             'start': m.meeting_time.astimezone(tz),
                             'end': m.meeting_time.astimezone(tz) + datetime.timedelta(minutes=m.duration)
                             }),

        if is_parent(request.user):
            parent = ParentProfile.objects.get(user=request.user)
            if parent.selected_child is None:
                tz = Timezone.objects.get(user=request.user).get_timezone()
                metting = Meeting.objects.filter(Q(meeting_date__gte=start), Q(meeting_date__lte=end),
                                                 Q(student__in=parent.children.all()) | Q(
                                                     student2__in=parent.children.all()) | Q(
                                                     student3__in=parent.children.all())
                                                 | Q(student4__in=parent.children.all()) | Q(
                                                     student5__in=parent.children.all()))

                for m in metting:
                    className = ''
                    tdelta = timedelta(hours=2)
                    if (now() - m.meeting_time) > tdelta:
                        url = ''
                        className = 'calendar-event-disabled'
                    data.append({'id': m.id,
                                 'title': m.get_meeting_time_for_the_user_time_zone(parent.user)[
                                              0] + " " + m.get_students_first_name_for_parent(
                                     parent) + ' {}min '.format(m.duration) + ' with ' + m.teacher.get_full_name(),
                                 'url': '#',
                                 'className': className,
                                 'start': m.meeting_time.astimezone(tz),
                                 'end': m.meeting_time.astimezone(tz) + datetime.timedelta(minutes=m.duration)
                                 })

    return JsonResponse(data, safe=False)


@login_required
def my_profile(request):
    _user = _get_selected_user(request)
    details_user_form = None
    user_form = None

    if request.method == 'POST':
        pass
        '''
        user_form = UserEditForm(request.POST, instance=_user)
        if is_teacher(_user):
            instance = TeacherProfile.objects.get(user=_user)
            details_user_form = TeacherProfileForm(request.POST, instance=instance)
        elif is_customer(_user):
            instance = CustomerProfile.objects.get(user=_user)
            details_user_form = CustomerProfileForm(request.POST, instance=instance)

        if user_form.is_valid() and details_user_form.is_valid():
            user_form.save()
            details_user_form.save()
        '''

    user_form = UserEditForm(instance=_user, disabled=True)
    if is_teacher(_user):
        instance = TeacherProfile.objects.get(user=_user)
        details_user_form = TeacherProfileForm(instance=instance, disabled=True)
    elif is_customer(_user):
        _instance = CustomerProfile.objects.filter(user=_user)
        if len(_instance) > 0:
            instance = _instance[0]
        else:
            instance = None
        details_user_form = CustomerProfileForm(instance=instance, disabled=True)
    elif is_parent(_user):
        _instance = ParentProfile.objects.filter(user=_user)
        if len(_instance) > 0:
            instance = _instance[0]
        else:
            instance = None
        details_user_form = ParentProfileForm(instance=instance, disabled=True)
    context = {'details_user_form': details_user_form, 'user_form': user_form}
    context.update(_add_avatar(request))

    return render(request,
                  'my_profile.html', context,
                  )


def _add_avatar(request):
    _user = _get_selected_user(request)
    avatar, avatars = _get_avatars(_user)
    upload_avatar_form = UploadAvatarForm(request.POST or None,
                                          request.FILES or None,
                                          user=_user)
    if request.method == "POST" and 'avatar' in request.FILES:
        if upload_avatar_form.is_valid():
            avatar = Avatar(user=_user, primary=True)
            image_file = request.FILES['avatar']
            avatar.avatar.save(image_file.name, image_file)
            avatar.save()
    context = {
        'avatar': avatar,
        'avatars': avatars,
        'upload_avatar_form': upload_avatar_form,
    }
    return context


@login_required
def contact(request):
    message = None
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if _send_mail_contact_form(data) > 0:
                message = u'Thank You for submitting form. We will get back to You soon.'
            else:
                message = u'Sorry. Something went wrong. Try again later or send email directly to: {}'.format(
                    DEFAULT_FROM_EMAIL)
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form, 'msg': message})


@login_required
def portfolio(request):
    return render(request, 'portfolio.html')


@login_required
def logout(request):
    if is_parent(request.user):
        parent = ParentProfile.objects.get(user=request.user)
        parent.selected_child = None
        parent.save()

    _logout(request)
    return render(request, 'registration/logged_out.html')


def _set_session_user_data(request, user):
    request.session['avatar'] = user.username
    request.session['user_first_name'] = user.first_name


def _get_student_meetings(user):
    return Meeting.objects.filter(Q(student=user) |
                                  Q(student2=user) |
                                  Q(student3=user) |
                                  Q(student4=user) |
                                  Q(student5=user)).order_by('meeting_time')


def _get_selected_user(request):
    if is_parent(request.user):
        parent = ParentProfile.objects.get(user=request.user)
        if parent.selected_child:
            return parent.selected_child

    return request.user
