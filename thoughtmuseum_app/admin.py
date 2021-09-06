from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .flexiquiz import FlexiQuizAPI
from .models import Timezone, TeacherProfile, CustomerProfile, Meeting, Document, PrimaryClassification, \
    SecondaryClassificationBrainTraining, SecondaryClassificationCareerPlanning, SecondaryClassificationLeveledReading, \
    SecondaryClassificationTestPrep, TertiaryClassificationBrainTraining, TertiaryClassificationTestPrep, GradeLevel, \
    DifficultyLevel, ParentProfile, Reminder, Class, Exam, FlexiQuizUser, FlexiquizResponse
from .zoom import ZoomAPI


class ExtendedActionsMixin(object):
    # actions that can be executed with no items selected on the admin change list.
    # The filtered queryset displayed to the user will be used instead
    extended_actions = []

    def changelist_view(self, request, extra_context=None):
        # if a extended action is called and there's no checkbox selected, select one with
        # invalid id, to get an empty queryset
        if 'action' in request.POST and request.POST['action'] in self.extended_actions:
            if not request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                post.update({admin.helpers.ACTION_CHECKBOX_NAME: 0})
                request._set_post(post)
        return super(ExtendedActionsMixin, self).changelist_view(request, extra_context)

    def get_changelist_instance(self, request):
        """
        Returns a simple ChangeList view instance of the current ModelView.
        (It's a simple instance since we don't populate the actions and list filter
        as expected since those are not used by this class)
        """
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        list_select_related = self.get_list_select_related(request)

        ChangeList = self.get_changelist(request)

        return ChangeList(
            request, self.model, list_display,
            list_display_links, list_filter, self.date_hierarchy,
            search_fields, list_select_related, self.list_per_page,
            self.list_max_show_all, self.list_editable, self, self.sortable_by,
        )

    def get_filtered_queryset(self, request):
        """
        Returns a queryset filtered by the URLs parameters
        """
        cl = self.get_changelist_instance(request)
        return cl.get_queryset(request)


class TimezoneInline(admin.StackedInline):
    model = Timezone
    can_delete = False
    verbose_name_plural = 'timezones'
    min_num = 1
    max_num = 1


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (TimezoneInline,)

    def save_model(self, request, obj, form, change):
        if change:
            if obj.first_name != '' and obj.last_name != '':
                api = FlexiQuizAPI()
                flexiquiz_user_id = None
                try:
                    flexiquiz_user = FlexiQuizUser.objects.get(user=obj)
                    flexiquiz_user_id = flexiquiz_user.flexiquiz_user_id
                except ObjectDoesNotExist:
                    pass
                if not flexiquiz_user_id:
                    try:
                        create_user = api.create_user(obj)
                        flexiquiz_user_id = create_user.get('user_id')
                        if flexiquiz_user_id:
                            flexi_user = FlexiQuizUser(user=obj, flexiquiz_user_id=flexiquiz_user_id)
                            flexi_user.save()
                            messages.info(request, 'Flexiquiz user created successfully')
                    except:
                        messages.error(request, 'Flexiquiz user NOT created. Username already taken')
        super().save_model(request, obj, form, change)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# admin.site.register(TeacherProfile)
admin.site.register(CustomerProfile)


class TeacherProfileAdmin(admin.ModelAdmin):
    # list_display = ['title', 'status']
    # ordering = ['title']
    actions = ['create_user']

    def create_user(self, request, queryset, dept='Teacher'):
        zoom = ZoomAPI()
        accounts_created = 0
        accounts_updated = 0
        for query in queryset:
            existing_email = []
            existing_id = []
            for user in zoom.get_users():
                exist_email = user['email']
                existing_email.append(str(exist_email))
                exist_id = user['id']
                existing_id.append(str(exist_id))
            # User exists at Zoom
            # THE ZOOM API RESPONSE MAKES ALL EMAIL ADDRESSES LOWER CASE.
            # This is even the case if on the web interface the upper/lower case is preserved.
            if query.user.email.lower() in existing_email:
                host_id = [existing_id[ix] for ix, x in enumerate(existing_email) if x == query.user.email.lower()][0]
                query.zoom_host_user_id = host_id
                query.save(update_fields=['zoom_host_user_id'])
                accounts_updated += 1
            else:
                query.zoom_host_user_id = zoom.create_user(query.user)
                query.save(update_fields=['zoom_host_user_id'])
                accounts_created += 1
        # super().create_user(self, request, queryset,dept='Teacher')

        message_bit = ''
        if accounts_updated == 1:
            message_bit = message_bit + "Updated %s account. " % accounts_updated
        else:
            message_bit = message_bit + "Updated %s accounts. " % accounts_updated
        if accounts_created == 1:
            message_bit = message_bit + "Created %s  account." % accounts_created
        else:
            message_bit = message_bit + "Created %s accounts. " % accounts_created

        self.message_user(request, " Successfully: %s " % message_bit)

    # Set name of new action
    create_user.short_description = "Create user on Zoom.us"


admin.site.register(TeacherProfile, TeacherProfileAdmin)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'student', 'meeting_date', 'meeting_time']
    list_display_links = list_display


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    pass


@admin.register(PrimaryClassification)
class PrimaryClassificationAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(SecondaryClassificationBrainTraining)
class SecondaryBrainAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(SecondaryClassificationCareerPlanning)
class SecondaryCareerAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(SecondaryClassificationLeveledReading)
class SecondaryLeveledAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(SecondaryClassificationTestPrep)
class SecondaryTestAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(TertiaryClassificationBrainTraining)
class TertiaryBrainAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(TertiaryClassificationTestPrep)
class TertiaryTestAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ['classification', 'slug']
    list_display_links = list_display


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    exclude = ('selected_child',)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['user', '_meeting', 'contact_type', 'status', 'date_send_utc']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('exams', 'students')


@admin.register(Exam)
class ExamAdmin(ExtendedActionsMixin, admin.ModelAdmin):
    filter_horizontal = ('enrolled', 'taken')
    list_display = ('name', 'date', 'quiz_id', 'active')
    actions = ['get_quizzes']
    extended_actions = ['get_quizzes']

    def get_quizzes(self, request, queryset):
        if not queryset:
            # if not queryset use the queryset filtered by the URL parameters
            queryset = self.get_filtered_queryset(request)

        api = FlexiQuizAPI()
        quizzes = api.get_all_quizzes()
        for q in quizzes:
            Exam.objects.get_or_create(name=q['name'], quiz_id=q['quiz_id'])

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        if 'active' in form.changed_data:
            api = FlexiQuizAPI()
            api.change_quiz_status(obj.quiz_id, obj.active)
        super().save_model(request, obj, form, change)


@admin.register(FlexiquizResponse)
class FlexiquizResponseAdmin(admin.ModelAdmin):
    list_display = ('date_submitted', 'quiz_name', 'first_name', 'last_name', 'points', 'grade', 'has_pass')

    # def has_add_permission(self, request):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return False


@admin.register(FlexiQuizUser)
class FlexiQuizUserAdmin(ExtendedActionsMixin, admin.ModelAdmin):
    list_display = ('user', 'flexiquiz_user_id')
    actions = ['get_flexiquiz_users']
    extended_actions = ['get_flexiquiz_users']

    def get_flexiquiz_users(self, request, queryset):
        if not queryset:
            # if not queryset use the queryset filtered by the URL parameters
            queryset = self.get_filtered_queryset(request)

        api = FlexiQuizAPI()
        flexi_users = api.get_all_users()
        for u in flexi_users:
            user = User.objects.filter(username=u['user_name'])
            if user:
                FlexiQuizUser.objects.get_or_create(user=user[0], flexiquiz_user_id=u['user_id'])
