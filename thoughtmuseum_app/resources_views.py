"""

When changes to the model fields in resources.models are made,
navigate to "novellumeducation.com/resources/upload" (type into URL bar
in your browser). This will propage the changes you made into the
database. (See code at the end of 'upload' function below.)

Caution: If you changed wording or deleted classifications, you will
need to go into the respective model in the admin interface to delete
the obsolete fields. This may be automated in a future version of the
code below.

Edits CL:

June 2, 2016:
Uploaded 'link' resources were not properly represented in the resources
browser. Edit code to check for 'file_type' (link or file) and serve URL
for link-enabled title based on this.

"""
import os

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify
from pytz import unicode

from thoughtmuseum_app import models
from thoughtmuseum_app.forms_resources import LevelAdjustForm, DocumentForm


def not_in_upload_group(user):
    if user:
        return user.groups.filter(name='visitor').count() == 0
    return False


@login_required
@user_passes_test(not_in_upload_group)  # , login_url='/')
def upload(request):
    # Handle file upload
    if request.method == 'POST':
        if 'upload' in request.POST:
            if not request.FILES:
                form = DocumentForm(request.POST)
                if form.is_valid():
                    newdoc = form.save(commit=False)
                    # add uploading user
                    newdoc.owner = request.user
                    # grab file type from form
                    file_type = form.cleaned_data.get('file_type')
                    file_type = dict(form.fields['file_type'].choices)[file_type]
                    newdoc.file_type = file_type
                    newdoc.save()
                    form.save_m2m()
                    # Use the following to redirect to the EMPTY upload form after POST / Submit
                    # Or comment out the line and after submission the form will retain all selections
                    # minus the selected file
                    return HttpResponseRedirect(reverse('upload'))
            else:
                form = DocumentForm(request.POST, request.FILES)
                if form.is_valid():
                    newdoc = form.save(commit=False)
                    # add uploading user
                    newdoc.owner = request.user
                    # grab file type from form
                    file_type = form.cleaned_data.get('file_type')
                    file_type = dict(form.fields['file_type'].choices)[file_type]
                    newdoc.file_type = file_type
                    newdoc.save()
                    form.save_m2m()
                    # Use the following to redirect to the EMPTY upload form after POST / Submit
                    # Or comment out the line and after submission the form will retain all selections
                    # minus the selected file
                    return HttpResponseRedirect(reverse('upload'))
    else:
        # A GET request is usually issued the first time the 'upload' page is requested. If uploads
        # are being performed, the page is re-rendered in the 'POST' part of the if-else and the
        # following is not executed. Therefore, we here include the code to check that the
        # manytomany relationships are properly populated according to the model choices.
        model_list = [models.PrimaryClassification,
                      models.SecondaryClassificationTestPrep,
                      models.SecondaryClassificationCareerPlanning,
                      models.SecondaryClassificationBrainTraining,
                      models.SecondaryClassificationLeveledReading,
                      models.TertiaryClassificationTestPrep,
                      models.TertiaryClassificationBrainTraining,
                      models.GradeLevel,
                      models.DifficultyLevel]
        for tmp_model in model_list:
            for tmp_choice_tuple in tmp_model.CHOICES:
                tmp_choice = tmp_choice_tuple[1]
                slug = slugify(tmp_choice)
                try:
                    obj = tmp_model.objects.get(classification=tmp_choice)
                except tmp_model.DoesNotExist:
                    obj = tmp_model(classification=tmp_choice, slug=slug)
                    obj.save()
                # obj, created = tmp_model.objects.get_or_create(classification=tmp_choice,slug=slug)

        # Serve an empty, unbound form
        form = DocumentForm()

        return render(request,
                      'resources/upload.html',
                      {'form': form},
                      )


def resources_overview(request):
    # find all primary classifications
    # ===========================================================================
    # classification = []
    # for choice in models.PrimaryClassification.CHOICES:
    #     tmp = str(choice[1]).split(' ')
    #     tmp_slug =  models.PrimaryClassification.objects.filter(
    #         classification=choice[1]).values_list('slug',flat=True)
    #     classification.append([tmp,tmp_slug[0]])
    # ===========================================================================

    # classification = PrimaryClassification.objects.all()
    return render(request,
                  'resources/resources_overview.html',
                  {})


# We have to make different views and templates for some of the
# secondary categories because of varying styles for the layout.

def resources_overview_second_level(request, slug):
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug))

    if slug == 'test-prep':
        secondary_class = models.SecondaryClassificationTestPrep
        template = 'resources_overview_test-prep.html'
    elif slug == 'brain-training':
        secondary_class = models.SecondaryClassificationBrainTraining
        template = 'resources_overview_brain-training.html'
    elif slug == 'leveled-reading':
        secondary_class = models.GradeLevel
        template = 'resources_overview_leveled-reading.html'
    elif slug == 'career-planning':
        return resources_index(request, slug)
    elif slug == 'literacy-and-assessment':
        return resources_index(request, slug)
    elif slug == 'education-and-policy':
        return resources_index(request, slug)
    classification = []
    for idx, choice in enumerate(secondary_class.CHOICES):
        if slug == 'test-prep' or slug == 'brain-training':
            explanation = secondary_class.EXPLANATIONS[idx]
        else:
            explanation = ''
        tmp = str(choice[1]).split(' ')
        tmp_slug = secondary_class.objects.filter(
            classification=choice[1]).values_list('slug', flat=True)
        if tmp_slug:
            classification.append([tmp, str(explanation), os.path.join(slug, tmp_slug[0])])
    # remove "N/A" from list of items to be displayed
    if slug == 'leveled-reading' and classification:
        del classification[-1]
    # Reset session information on grade/difficulty selection
    if request.session.get('level_data'):
        del request.session['level_data']
    return render(request,
                  os.path.join('resources', template),
                  {'tmp_primary': primary[0] if primary else None,
                   'classification': classification,
                   })


def resources_index_test_prep(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    tags = models.TertiaryClassificationTestPrep.objects.all()
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    secondary = (models.SecondaryClassificationTestPrep.objects
                 .filter(slug=slug_secondary))
    if slug_tertiary:
        tertiary = (models.TertiaryClassificationTestPrep.objects
                    .filter(slug=slug_tertiary))
    else:
        tertiary = None
    if not tertiary:  # Overview, i.e. no tertiary selected / all
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(secondary_classification_test_prep__in=secondary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    else:  # select for specific tertiary category, if selected
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(secondary_classification_test_prep__in=secondary)
                   .filter(tertiary_classification_test_prep__in=tertiary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}
    return results_dict


def resources_index_leveled_reading(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    # tags needed for sidenav menue
    tags = models.SecondaryClassificationLeveledReading.objects.all()
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    secondary = primary
    if slug_tertiary:
        tertiary = (models.SecondaryClassificationLeveledReading.objects
                    .filter(slug=slug_tertiary))
    else:
        tertiary = None
    if slug_secondary in [x[0] for x in models.DifficultyLevel.CHOICES]:
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(difficulty_level=slug_secondary)
                   .distinct().values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    else:
        if not tertiary:  # Overview, i.e. no tertiary selected / all
            results = (models.Document.objects
                       .filter(primary_classification__in=primary)
                       .filter(combined_q_objects)
                       .distinct().values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
        else:
            results = (models.Document.objects
                       .filter(primary_classification__in=primary)
                       .filter(secondary_classification_leveled_reading__in=tertiary)
                       .filter(combined_q_objects)
                       .distinct().values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))

    print(primary, secondary, tertiary, tags)
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}

    return results_dict


def resources_index_brain_training(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    # tags needed for sidenav menue
    tags = models.TertiaryClassificationBrainTraining.objects.all()
    # print tags
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    secondary = (models.SecondaryClassificationBrainTraining.objects
                 .filter(slug=slug_secondary))
    if slug_tertiary:
        tertiary = (models.TertiaryClassificationBrainTraining.objects
                    .filter(slug=slug_tertiary))
    else:
        tertiary = None
    if not tertiary:  # Overview, i.e. no tertiary selected / all
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(secondary_classification_brain_training__in=secondary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    else:  # select for specific tertiary category, if selected
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(secondary_classification_brain_training__in=secondary)
                   .filter(tertiary_classification_brain_training__in=tertiary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}
    return results_dict


def resources_index_literacy_assessment(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    # tags needed for sidenav menue
    tags = []
    # print tags
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    if not slug_secondary:
        secondary = None
    if not slug_tertiary:
        tertiary = None
    if not tertiary:  # Overview, i.e. no tertiary selected / all
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}
    return results_dict


def resources_index_education_policy(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    # tags needed for sidenav menue
    tags = []
    # print tags
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    if not slug_secondary:
        secondary = None
    if not slug_tertiary:
        tertiary = None
    if not tertiary:  # Overview, i.e. no tertiary selected / all
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(combined_q_objects)
                   .distinct()
                   .values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}

    return results_dict


def resources_index_career_planning(slug_primary, slug_secondary, slug_tertiary, combined_q_objects):
    # tags needed for sidenav menue
    tags = models.SecondaryClassificationCareerPlanning.objects.all()
    # print tags
    primary = (models.PrimaryClassification.objects
               .filter(slug=slug_primary))
    secondary = primary
    if slug_tertiary:
        tertiary = (models.SecondaryClassificationCareerPlanning.objects
                    .filter(slug=slug_tertiary))
    else:
        tertiary = None
    if not tertiary:  # Overview, i.e. no tertiary selected / all
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(combined_q_objects)
                   .distinct().values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    else:  # select for specific tertiary category, if selected
        results = (models.Document.objects
                   .filter(primary_classification__in=primary)
                   .filter(secondary_classification_career_planning__in=tertiary)
                   .filter(combined_q_objects)
                   .distinct().values_list('id', 'title', 'docfile', 'description', 'file_type', 'link'))
    results_dict = {
        'primary': primary,
        'secondary': secondary,
        'tertiary': tertiary,
        'tags': tags,
        'results': results}
    return results_dict


@login_required
def resources_index(request, slug):
    slug_primary = slug.split("/")[0]
    slug_secondary = slug.split("/")[1] if len(slug.split("/")) > 1 else None
    slug_tertiary = slug.split("/")[2] if len(slug.split("/")) > 2 else None

    if request.method == 'POST':
        if 'level-adjust' in request.POST:
            form = LevelAdjustForm(request.POST)
            if form.is_valid():
                tmp_grades = form.cleaned_data.get('grade_level')
                tmp_difficulty = form.cleaned_data.get('difficulty_level')
                level_data = {
                    'grade_level': tmp_grades,
                    'difficulty_level': tmp_difficulty,
                }

                request.session['level_data'] = level_data

    else:
        # Allow for pre-selected grade level (coming to index from 'leveled reading')
        if slug_primary == 'leveled-reading' and slug_secondary in [str(x[1]).lower() for x in
                                                                    models.GradeLevel.CHOICES]:
            match = models.GradeLevel.objects.filter(slug=str(slug_secondary)).values_list('id', flat=True)
            match = [unicode(x) for x in match]
            level_data = {
                'grade_level': match,
                'difficulty_level': [x[0] for x in models.DifficultyLevel.CHOICES],
            }

            if not request.session.get('level_data'):
                request.session['level_data'] = level_data
        else:
            # check if session has information on grade/difficulty level
            if request.session.get('level_data'):
                level_data = request.session.get('level_data')

            # we only want to keep the session data on grade/difficulty when
            # navigating within the index page. When we go back to primary/secondary,
            # level_data should reset.
            else:
                level_data = {
                    'grade_level': [x[0] for x in models.GradeLevel.CHOICES],
                    'difficulty_level': [x[0] for x in models.DifficultyLevel.CHOICES],
                }
        form = LevelAdjustForm(initial=level_data)
        # Turn list of values into list of Q objects
    # init our q objects variable to use .add() on it
    q_objects_grade = Q()
    q_objects_difficulty = Q()
    # loop trough the list and create an OR condition for each item
    for item in level_data['grade_level']:
        q_objects_grade.add(Q(grade_level=item), Q.OR)
    for item in level_data['difficulty_level']:
        q_objects_difficulty.add(Q(difficulty_level=item), Q.OR)
    if len(q_objects_grade) == 0 and len(q_objects_difficulty) == 0:
        combined_q_objects = (q_objects_grade & q_objects_difficulty)
    elif len(q_objects_grade) == 0 and len(q_objects_difficulty) != 0:
        combined_q_objects = q_objects_difficulty
    elif len(q_objects_difficulty) == 0 and len(q_objects_grade) != 0:
        combined_q_objects = q_objects_grade
    else:
        combined_q_objects = (q_objects_grade & q_objects_difficulty)
    #     # for our list_with_strings we can do the following
    #     # q_objects.add(Q(**{item: 1}), Q.OR)

    if slug_primary == 'test-prep':
        results_dict = resources_index_test_prep(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)
    if slug_primary == 'leveled-reading':
        results_dict = resources_index_leveled_reading(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)
    if slug_primary == 'brain-training':
        results_dict = resources_index_brain_training(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)
    if slug_primary == 'literacy-and-assessment':
        results_dict = resources_index_literacy_assessment(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)
    if slug_primary == 'education-and-policy':
        results_dict = resources_index_education_policy(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)
    if slug_primary == 'career-planning':
        results_dict = resources_index_career_planning(
            slug_primary,
            slug_secondary,
            slug_tertiary,
            combined_q_objects)

    primary = results_dict['primary']
    secondary = results_dict['secondary']
    tertiary = results_dict['tertiary']
    tags = results_dict['tags']
    results = results_dict['results']

    titles = []
    descriptions = []
    urls = []
    # As a reminder, we queried:
    # .values_list('id','title','docfile','description','file_type','link'))
    for item in results:
        titles.append(item[1])
        if item[4] == 'Link':
            urls.append(item[5])
        else:
            urls.append(os.path.join('/media', item[2]))
        descriptions.append(item[3])
    matching_ti = zip(urls, titles, descriptions)

    return_dict = {
        'form': form,
        'tmp_primary': primary[0] if primary else None,
        'tags': tags,
        'results_ti': results,
        'matching_ti': matching_ti,
    }
    if not secondary:
        return_dict['tmp_secondary'] = secondary
    else:
        return_dict['tmp_secondary'] = secondary[0]
    if not tertiary:
        return_dict['tmp_tertiary'] = tertiary
    else:
        return_dict['tmp_tertiary'] = tertiary[0]
    return render(request,
                  'resources/resources_subject.html',
                  return_dict)
