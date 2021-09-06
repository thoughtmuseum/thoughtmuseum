from .models import Meeting, Reminder, ParentProfile, REMINDER_TIME, CustomerProfile
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.core.mail.message import EmailMessage
from Thoughtmuseum.settings import  DEFAULT_FROM_EMAIL
from django.core.exceptions import ObjectDoesNotExist

def reminder(request):
    _utc_now = datetime.utcnow()    
    _date_time = _utc_now + timedelta(hours=24)
    _date_time = _date_time.replace(second=0, microsecond=0)
    _success, _all_attempts = 0, 0

    # 24h before
    meetings = Meeting.objects.filter(meeting_time=_date_time)           
    _success, _all_attempts = _send_emails_for_meetings(meetings)

    for rt in REMINDER_TIME:        
        _date_time = _utc_now + timedelta(minutes=rt[1])
        _date_time = _date_time.replace(second=0, microsecond=0)        
        meetings = Meeting.objects.filter(meeting_time=_date_time)       
        _s, _all_a = _send_emails_for_meetings(meetings, rt[0])
        _success += _s
        _all_attempts += _all_a  
    
    html = f'Time: {datetime.now()} All attempts: {_all_attempts} Success: {_success} Errors: {_all_attempts-_success}'
    return HttpResponse(html)    


def _get_parent_text_email(meeting, user):
    try:
        parent = ParentProfile.objects.get(children = user)
        date_time, timezone = meeting.get_meeting_date_time_for_the_user_time_zone(parent.user)
    except ObjectDoesNotExist:
        return None
    
    return f'{user.first_name} has a meeting soon, {date_time} ({timezone})'


def _get_student_text_email(meeting, user):
    date_time, timezone = meeting.get_meeting_date_time_for_the_user_time_zone(user)    
    return f'You have a meeting soon, {date_time} ({timezone})'


def _send_email(meeting, user, is_parent):
    subject = 'Upcoming Meeting'
    if is_parent:
        try:
            parent = ParentProfile.objects.get(children = user)       
        except ObjectDoesNotExist:
            return None
        message = _get_parent_text_email(meeting, user)
        user_email = parent.user.email         
    else:
        message = _get_student_text_email(meeting, user)
        user_email = user.email     
           
    mail = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, [user_email,] )
    result = mail.send(fail_silently=True) 
    return result

def _create_reminder_object(meeting, user, email_sent_result):
    status = 'Success' if email_sent_result > 0  else 'Error'
    Reminder.objects.create(user=user,
                            meeting=meeting,
                            contact_type='1',
                            status=status
                            )


def _send_emails_for_meetings(meetings, reminder_time=None):
    _success, _all_attempts = 0, 0
    students = ['student', 'student2', 'student3', 'student4', 'student5']
    for meeting in meetings:
        for student in students:
            user = getattr(meeting, student)
            if user:
                if reminder_time:
                    try:
                        parent = ParentProfile.objects.get(children = user)
                        if parent.reminder_time == reminder_time:
                            email_sent_result = _send_email(meeting, user, True)
                            _create_reminder_object(meeting, parent.user, email_sent_result) 
                            _success += email_sent_result 
                            _all_attempts += 1
                    except ObjectDoesNotExist:                    
                        pass    
                    try:
                        student = CustomerProfile.objects.get(user=user)
                        if student.reminder_time == reminder_time:
                            email_sent_result = _send_email(meeting, user, False)  
                            _create_reminder_object(meeting, user, email_sent_result) 
                            _success += email_sent_result 
                            _all_attempts += 1
                    except ObjectDoesNotExist:                    
                        pass 
                else:    
                    try:
                        parent = ParentProfile.objects.get(children = user)
                        email_sent_result = _send_email(meeting, user, True)
                        _create_reminder_object(meeting, parent.user, email_sent_result)  
                        _success += email_sent_result 
                        _all_attempts += 1
                    except ObjectDoesNotExist:                    
                        pass                        
                    email_sent_result = _send_email(meeting, user, False)  
                    _create_reminder_object(meeting, user, email_sent_result) 
                    _success += email_sent_result 
                    _all_attempts += 1 
    
    return _success, _all_attempts 
