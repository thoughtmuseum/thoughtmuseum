from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from django import forms

from thoughtmuseum_app import models


class DocumentForm(forms.ModelForm):
    primary_classification = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.PrimaryClassification.CHOICES,
        label='Primary classification', )
    secondary_classification_test_prep = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.SecondaryClassificationTestPrep.CHOICES,
        label='Test Prep (Secondary classification)', required=False)
    secondary_classification_career_planning = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.SecondaryClassificationCareerPlanning.CHOICES,
        label='Career Planning (Secondary classification)', required=False)
    secondary_classification_brain_training = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.SecondaryClassificationBrainTraining.CHOICES,
        label='Brain Training (Secondary classification)', required=False)
    secondary_classification_leveled_reading = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.SecondaryClassificationLeveledReading.CHOICES,
        label='Leveled Reading (Secondary classification)', required=False)
    tertiary_classification_test_prep = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.TertiaryClassificationTestPrep.CHOICES,
        label='Test Prep (Tertiary classification)', required=False)
    tertiary_classification_brain_training = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.TertiaryClassificationBrainTraining.CHOICES,
        label='Brain Training (Tertiary classification)', required=False)
    grade_level = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.GradeLevel.CHOICES)
    difficulty_level = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.DifficultyLevel.CHOICES)
    FILE_CHOICES = (
        ('1', 'Link'),
        ('2', 'File')
    )
    file_type = forms.ChoiceField(choices=FILE_CHOICES, initial='2', widget=forms.RadioSelect, )
    docfile = forms.FileField(label='Select a file', required=False)
    link = forms.URLField(required=False,
                          widget=forms.TextInput({"placeholder": "The link to your resource.",
                                                  "class": "col-sm-10"}))
    title = forms.CharField(required=True, max_length=50,
                            widget=forms.TextInput(
                                {"placeholder": "A concise title for your upload (max. 50 characters).",
                                 "class": "col-sm-10"}))
    description = forms.CharField(required=True, max_length=250,
                                  widget=forms.Textarea({
                                                            "placeholder": "Provide a short description (max. 250 characters) of the content.",
                                                            "class": "col-sm-10", "cols": "50", "rows": "5"}))

    class Meta:
        model = models.Document
        # fields = '__all__'
        exclude = ('owner',)

    # change layout of cripsy form
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'file_type',
            'docfile',
            'link',
            'title',
            'description',
            InlineCheckboxes('primary_classification'),
            Div(
                Div('secondary_classification_test_prep', css_class='col-sm-3 ', css_id='upload_form'),
                Div('secondary_classification_career_planning', css_class='col-sm-3 ', css_id='upload_form'),
                Div('secondary_classification_brain_training', css_class='col-sm-3 ', css_id='upload_form'),
                Div('secondary_classification_leveled_reading', css_class='col-sm-3 ', css_id='upload_form'),
                css_class='row'),
            Div(
                Div('tertiary_classification_test_prep', css_class='col-sm-3 ', css_id='upload_form'),
                Div('tertiary_classification_brain_training', css_class='col-sm-3 col-sm-offset-3',
                    css_id='upload_form'),
                css_class='col-sm-12', css_id='upload_form'),
            Div(
                InlineCheckboxes('grade_level'),
                css_class='col-sm-12', css_id='upload_form'),
            Div(
                InlineCheckboxes('difficulty_level'),
                css_class='col-sm-12', css_id='upload_form'),
            Submit('upload', u'Upload', css_class='btn btn-block btn-primary'),
        )
        super(DocumentForm, self).__init__(*args, **kwargs)


class LevelAdjustForm(forms.ModelForm):
    grade_level = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.GradeLevel.CHOICES,
        label='Grade',
        required=False)
    # all_grades = forms.ChoiceField(widget=forms.CheckboxSelectMultiple,
    #     label='All',
    #     choices=(('1','All'),),
    #     required=False)
    difficulty_level = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=models.DifficultyLevel.CHOICES,
        label='Difficulty',
        required=False)

    class Meta:
        model = models.Document
        # fields = '__all__'
        fields = ('grade_level', 'difficulty_level')

    # change layout of cripsy form
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('grade_level',
                    HTML('<div class="custom-control custom-checkbox">\
                            <input type="checkbox"\
                                class="custom-control-input"\
                                checked="checked"\
                                name="select-all-grades" \
                                id="id-select-all-grades" \
                                value="all"/>  \
                            <label class="custom-control-label" for="id-select-all-grades">All</label> \
                    </div>'),
                    css_class='col-sm-6', css_id='upload_form'),
                Div('difficulty_level',
                    HTML('<div class="custom-control custom-checkbox">\
                            <input type="checkbox"\
                                class="custom-control-input" \
                                checked="checked"\
                                name="select-all-difficulties" \
                                id="id-select-all-diff" \
                                value="all"/> \
                            <label class="custom-control-label" for="id-select-all-diff">All</label> \
                    </div>'),
                    css_class='col-sm-6', css_id='upload_form'),
                css_class='row'),
            Div(
                Submit('level-adjust', u'Apply', css_class='btn btn-block btn-primary'),
                css_class='col-sm-9 offset-sm-1'),
        )
        super(LevelAdjustForm, self).__init__(*args, **kwargs)
