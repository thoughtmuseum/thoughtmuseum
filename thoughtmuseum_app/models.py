from django.db import models
from django.contrib.auth.models import User
import pytz
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import datetime

REMINDER_TIME = (
        ('15', 15),
        ('30', 30),
        ('60', 60)        
    )
def get_first_name(self):
    return self.first_name

def get_name(self):
    return '{} {}'.format(self.first_name, self.last_name)

User.add_to_class("__str__", get_name)

class Timezone(models.Model):
    tzs = list(pytz.all_timezones_set)
    tzs.sort(key=str.lower)
    MY_CHOICES = tuple((str(idx), str(n)) for idx, n in enumerate(tzs))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=35, choices=MY_CHOICES)

    def __str__(self):
        return self.timezone
    
    def get_timezone(self):
        return pytz.timezone(Timezone.MY_CHOICES[int(self.timezone)][1])


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, related_name='teacher', on_delete=models.CASCADE)
    title = models.CharField(max_length=50, blank=True, default='')
    specialization = models.CharField(max_length=250, )
    highest_degree_earned = models.CharField(max_length=50, )
    address = models.TextField(max_length=250, )
    website = models.CharField(max_length=50, blank=True, default='')
    publications = models.CharField(max_length=250, blank=True, default='')
    photo = models.CharField(max_length=250, blank=True, default='')
    phone_number = models.CharField(max_length=250, )
    zoom_host_user_id = models.CharField(max_length=50, blank=True, default='')

    # This is the name in main admin overview of all registered Models
    class Meta:
        verbose_name = "Teacher Profile"
        verbose_name_plural = 'Teacher Profiles'

    # This changes the title of the Meetings object 
    def __str__(self):
        title = 'Profile of ' + str(self.user)
        return title

STUDENT_GENDER=(('M', 'Male'),
                ('F', 'Female'))

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, related_name='customer', on_delete=models.CASCADE,   limit_choices_to={'groups__name': u'customer'},)
    date_of_birth = models.DateField()   
    student_gender = models.CharField(max_length=1, choices=STUDENT_GENDER, blank=True, default='')
    grade_level = models.CharField(max_length=250, )
    semester = models.CharField(max_length=128, blank=True, default='')
    school_year = models.CharField(max_length=32, blank=True, default='') 
    reminder_time = models.CharField(max_length=2, choices=REMINDER_TIME, default='60')       
    street_address = models.CharField(max_length=250, blank=True, default='')
    street_address_line_2 = models.CharField(max_length=250, blank=True, default='')
    city =  models.CharField(max_length=128, blank=True, default='')
    state =  models.CharField(max_length=128, blank=True, default='')
    zip_code =  models.CharField(max_length=128, blank=True, default='')
    phone_number = models.CharField(max_length=16, blank=True, default='')
    home_phone_number = models.CharField(max_length=16, blank=True, default='')
    # This is the name in main admin overview of all registered Models
    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = 'Customer Profiles'

    # This changes the title of the Meetings object 
    def __str__(self):
        title = 'Profile of ' + str(self.user)
        return title


class ParentProfile(models.Model):
    user = models.OneToOneField(User, related_name='parent',
                                on_delete=models.CASCADE,
                                limit_choices_to={'groups__name': u'parent'},)
    children = models.ManyToManyField(User, limit_choices_to={'groups__name': u'customer'})
    street_address = models.CharField(max_length=250, blank=True, default='')
    street_address_line_2 = models.CharField(max_length=250, blank=True, default='')
    city =  models.CharField(max_length=128, blank=True, default='')
    state =  models.CharField(max_length=128, blank=True, default='')
    zip_code =  models.CharField(max_length=128, blank=True, default='')
    phone_number = models.CharField(max_length=16, blank=True, default='')
    selected_child = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='_selected_child')
    reminder_time = models.CharField(max_length=2, choices=REMINDER_TIME, default='60')

    def __str__(self):
        return 'Profile of ' + str(self.user)

def get_teacher():
    teachers = User.objects.filter(groups__name='teacher')
    if teachers:
        return teachers[0]
    return None

class Meeting(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name='meeting_origin',
                                limit_choices_to={'groups__name': u'teacher'},
                                default=get_teacher)
    student = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name='meeting_target',
                                limit_choices_to={'groups__name': u'customer'},
                                default='0')
    student2 = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name='meeting_target2',
                                 limit_choices_to={'groups__name': u'customer'},
                                 blank=True, null=True)
    student3 = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name='meeting_target3',
                                 limit_choices_to={'groups__name': u'customer'},
                                 blank=True, null=True)
    student4 = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name='meeting_target4',
                                 limit_choices_to={'groups__name': u'customer'},
                                 blank=True, null=True)
    student5 = models.ForeignKey(User, on_delete=models.PROTECT,
                                 related_name='meeting_target5',
                                 limit_choices_to={'groups__name': u'customer'},
                                 blank=True, null=True)
    meeting_time = models.DateTimeField(default=timezone.now, blank=True)
    meeting_date = models.DateField(default=timezone.now)
    setup_time = models.DateTimeField(default=timezone.now, blank=True)
    start_url = models.TextField(blank=True)
    join_url = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=32, null=True, blank=True)
    meeting_id = models.CharField(max_length=16, null=True, blank=True)
    duration = models.IntegerField(default=60)

    # This is the name in main admin overview of all registered Models
    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = 'Meetings'

    # This changes the title of the Meetings object
    def __str__(self):
        title = str(self.teacher) + ' with ' + str(self.student)
        if self.student2 or self.student3 or self.student4 or self.student5:
            title = title + ' +'
        return title

    def meeting_end_time(self):
        return self.meeting_time + datetime.timedelta(days=0, hours=0, minutes=self.duration)

    def get_students_name(self):
        name = self.student.get_full_name()
        if self.student2:
            name += ", " + self.student2.get_full_name()
        if self.student3:
            name += ", " + self.student3.get_full_name()
        if self.student4:
            name += ", " + self.student4.get_full_name()
        if self.student5:
            name += ", " + self.student5.get_full_name()
        return name

    def get_students_first_name_for_parent(self, parent):
        name = ''    
        if self.student in parent.children.all():
            name += self.student.first_name
        if self.student2 in parent.children.all():
            if len(name) > 1:
                name += ', '
            name += " " + self.student2.first_name
        if self.student3 in parent.children.all():
            if len(name) > 1:
                name += ', '
            name += " " + self.student3.first_name
        if self.student4 in parent.children.all():
            if len(name) > 1:
                name += ', '
            name += " " + self.student4.first_name
        if self.student5 in parent.children.all():
            if len(name) > 1:
                name += ', '
            name += " " + self.student5.first_name
        return name

    def get_more_students(self):
        name = ''
        if self.student2:
            name += self.student2.username
        if self.student3:
            name += ", " + self.student3.username
        if self.student4:
            name += ", " + self.student4.username
        if self.student5:
            name += ", " + self.student5.username
        return name

    def get_meeting_id(self):
        if self.meeting_id:
            return self.meeting_id
        s = self.join_url.split("/")
        return s[-1].strip()

    def get_meeting_date_time_for_the_user_time_zone(self, user):
        fmt_date = '%a, %B %d %Y'
        fmt_time = '%I:%M %p'
        tz = Timezone.objects.get(user=user).get_timezone()

        meeting_datetime = self.meeting_time.astimezone(tz)
        meeting_datetime = u'{} {}'.format( meeting_datetime.time().strftime(fmt_time), meeting_datetime.date().strftime(fmt_date))
        return meeting_datetime, tz

    def get_meeting_time_for_the_user_time_zone(self, user):
        fmt_time = '%I:%M %p'
        tz = Timezone.objects.get(user=user).get_timezone()

        meeting_datetime = self.meeting_time.astimezone(tz)
        meeting_datetime = u'{}'.format(meeting_datetime.time().strftime(fmt_time))
        return meeting_datetime, tz

    def get_meeting_time_for_the_student(self):
        meeting_datetime, tz = self.get_meeting_time_for_the_user_time_zone(self.student)
        return meeting_datetime

    def get_meeting_time_for_the_teacher(self):
        meeting_datetime, tz = self.get_meeting_time_for_the_user_time_zone(self.teacher)
        return meeting_datetime


    get_more_students.short_description = 'More students'


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Primary classification
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

class PrimaryClassification(models.Model):
    CHOICES = (
        ('1', 'Test Prep'),
        ('2', 'Career Planning'),
        ('3', 'Brain Training'),
        ('4', 'Leveled Reading'),
        ('5', 'Literacy and Assessment'),
        ('6', 'Education and Policy'),
    )
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Secondary classification
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

class SecondaryClassificationTestPrep(models.Model):
    CHOICES = (
        ('1', 'SSAT'),
        ('2', 'ISEE'),
        ('3', 'SAT'),
        ('4', 'ACT'),
        ('5', 'GRE'),
        ('6', 'GMAT'),
        ('7', 'OTHER'),
    )
    # Following are explanations for the secondary categories of the
    # test prep section. While they only appear in the rendered html
    # and therefore expressing them here might seem weird, it nonetheless
    # keeps the category list and the exlpanations together.
    EXPLANATIONS = ['Explanation for the SSAT', 'Explanation for the ISEE', 'Explanation for the SAT',
                    'Explanation for the ACT', 'Explanation for the GRE', 'Explanation for the GMAT',
                    "Explanation for the 'OTHER' category", ]
    classification = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


class SecondaryClassificationCareerPlanning(models.Model):
    CHOICES = (
        ('1', 'Cover Letters & Resumes'),
        ('2', 'Interview Preparation'),
        ('3', 'Industry Specific Studies'),
        ('4', 'Academic Planning'),
        ('5', 'Research & Internships'),
    )
    EXPLANATIONS = ['Explanation for Resume and Cover Letter Preparation',
                    'Explanation for Interview Preparation',
                    'Explanation for Industry Specific Studies',
                    'Explanation for Academic Planning',
                    'Explanation for Research & Internships',
                    ]
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


class SecondaryClassificationBrainTraining(models.Model):
    CHOICES = (
        ('1', 'Research Papers'),
        ('2', 'Exercises and Plans'),
        ('3', 'Helpful Links'),
    )
    EXPLANATIONS = ['Explanation for Research Papers',
                    'Explanation for Exercises and Plans',
                    'Explanation for Helpful Links',
                    ]
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


class SecondaryClassificationLeveledReading(models.Model):
    CHOICES = (
        ('1', 'Social Science'),
        ('2', 'Natural Science'),
        ('3', 'Psychology'),
        ('4', 'Philosophy'),
        ('5', 'Literature'),
        ('6', 'History'),
        ('7', 'Biography'),
        ('8', 'General (other)'),
    )

    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Tertiary classification
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


class TertiaryClassificationTestPrep(models.Model):
    CHOICES = (
        ('1', 'Math'),
        ('2', 'Quantitative Reasoning'),
        ('3', 'Math Achievement'),
        ('4', 'Vocabulary'),
        ('5', 'Analogies'),
        ('6', 'Reading'),
        ('7', 'Verbal Reasoning'),
        ('8', 'Logic'),
        ('9', 'Data Analysis'),
        ('10', 'Science'),
        ('11', 'Verbal Skills'),
        ('12', 'Writing Skills'),
    )
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


class TertiaryClassificationBrainTraining(models.Model):
    CHOICES = (
        ('1', 'Working Memory'),
        ('2', 'IQ'),
        ('3', 'Cognition & Learning'),
    )
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Grade level
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

class GradeLevel(models.Model):
    CHOICES = (
        ('1', 'K'),
        ('2', '1'),
        ('3', '2'),
        ('4', '3'),
        ('5', '4'),
        ('6', '5'),
        ('7', '6'),
        ('8', '7'),
        ('9', '8'),
        ('10', '9'),
        ('11', '10'),
        ('12', '11'),
        ('13', '12'),
        ('14', 'Lower'),
        ('15', 'Upper'),
        ('16', 'Graduate'),
        ('17', 'N/A'),
    )
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Difficulty level
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

class DifficultyLevel(models.Model):
    CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', 'N/A'),
    )
    classification = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    # This changes the title of the Subject object
    def __str__(self):
        return self.classification


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Tertiary classification
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# The main document
class Document(models.Model):
    # general information
    docfile = models.FileField(upload_to='documents/%Y/%m/%d', blank=True)
    file_type = models.CharField(max_length=250)
    link = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    # primary classification
    primary_classification = models.ManyToManyField(PrimaryClassification)
    # secondary classification
    secondary_classification_test_prep = models.ManyToManyField(SecondaryClassificationTestPrep, blank=True)
    secondary_classification_career_planning = models.ManyToManyField(SecondaryClassificationCareerPlanning, blank=True)
    secondary_classification_brain_training = models.ManyToManyField(SecondaryClassificationBrainTraining, blank=True)
    secondary_classification_leveled_reading = models.ManyToManyField(SecondaryClassificationLeveledReading, blank=True)
    # tertiary classification
    tertiary_classification_test_prep = models.ManyToManyField(TertiaryClassificationTestPrep, blank=True)
    tertiary_classification_brain_training = models.ManyToManyField(TertiaryClassificationBrainTraining, blank=True)
    # grade level classification
    grade_level = models.ManyToManyField(GradeLevel)
    # difficulty level classification
    difficulty_level = models.ManyToManyField(DifficultyLevel)

    # This changes the title of the Document object
    def __str__(self):
        return self.title

CONTACT_TYPE = (
        ('1', 'e-mail'),
        ('2', 'phone')        
    )


class Reminder(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, null=True, on_delete=models.CASCADE)
    date_send_utc = models.DateTimeField(default=timezone.now)
    contact_type = models.CharField(max_length=8, choices=CONTACT_TYPE)
    status = models.CharField(max_length=16, default='')

    def _meeting(self):
        time, tz = self.meeting.get_meeting_date_time_for_the_user_time_zone(self.user)
        return f'Teacher: {self.meeting.teacher}, user time : {time}'


class FlexiQuizUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='flexiquiz_user')
    flexiquiz_user_id = models.CharField(max_length=255)

    def __str__(self):
        return str(self.user)


class Exam(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)
    quiz_id = models.CharField(max_length=255)
    enrolled = models.ManyToManyField(User, blank=True, related_name='exams_enrolled',
                                      limit_choices_to={'groups__name': 'customer'})
    taken = models.ManyToManyField(User, blank=True, related_name='exams_taken',
                                   limit_choices_to={'groups__name': 'customer'})

    def __str__(self):
        return self.name

    def get_results(self, user):
        return FlexiquizResponse.objects.filter(quiz_id=self.quiz_id, user_name=user.username)


class Class(models.Model):
    name = models.CharField(max_length=255)
    exams = models.ManyToManyField(Exam, blank=True, related_name='exam_classes')
    students = models.ManyToManyField(User, blank=True, related_name='user_classes',
                                      limit_choices_to={'groups__name': 'customer'})

    class Meta:
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'

    def __str__(self):
        return self.name


class FlexiquizResponse(models.Model):
    response_id = models.CharField(max_length=255)
    quiz_id = models.CharField(max_length=255)
    quiz_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email_address = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    date_submitted = models.DateTimeField()
    points = models.PositiveIntegerField()
    available_points = models.PositiveIntegerField()
    percentage_score = models.PositiveIntegerField()
    grade = models.CharField(max_length=1)
    has_pass = models.BooleanField()
    duration = models.PositiveIntegerField()
    attempt = models.PositiveSmallIntegerField()
    ip_address = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    publish_type = models.CharField(max_length=255)
    certificate_url = models.TextField()
    response_report_url = models.TextField()
    registration_fields = models.TextField()




