from django import forms
from django.forms import TextInput, RadioSelect, CheckboxSelectMultiple, Select
from django.utils.safestring import mark_safe
from django.core.validators import RegexValidator
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from trl.models import Project, Technology, Category, Level
from django.contrib.auth import get_user_model


# -----------------------------------------------------------------------------------
# HELPER METHODS
# -----------------------------------------------------------------------------------

def add_autosave_attributes(other_attrs):
    autosave_attrs = {'hx-post':".", 'hx-swap':"none", 'hx-trigger':"change"}
    for key, value in other_attrs.items():
        autosave_attrs[key] = value
    return autosave_attrs

class ModelChoiceFieldWithIcon(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(f"<img class='icon-selecton' src='{obj.icon.url}'/><p class='explanation'>{obj}</span>")
        
class ModelMultipleChoiceFieldWithIcon(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(f"<img class='icon-selecton' src='{obj.icon.url}'/><p class='explanation'>{obj}</span>")

class LevelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(f"{obj.number}")

class UserProfileCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("guid", "full_name")

class UserProfileEditForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ("guid", "full_name",)


# -----------------------------------------------------------------------------------
# FORMS
# -----------------------------------------------------------------------------------

class ProjectDetailsForm(forms.ModelForm):
    name = forms.CharField(max_length=128,
           widget=TextInput(attrs={'class':"long-info", 'title':"", 'autocomplete': "off", 'oninput': "validateProjectName(this)"}),
           help_text="Project Name")    
    technology = ModelChoiceFieldWithIcon(queryset=Technology.objects.all(),
                 widget=RadioSelect(attrs={'class':"radio-tech", 'oninvalid':"setCustomValidity('Please select a Technology Type.')"}), 
                 help_text="Technology Type")
    categories = ModelMultipleChoiceFieldWithIcon(queryset=Category.objects.all(),
                 widget=CheckboxSelectMultiple(attrs={'class':"multi-cat", 'onchange': "validateProjectCategory()"}), 
                 help_text="Readiness Level Categories")
    level = LevelChoiceField(queryset=Level.objects.exclude(number=0),
            widget=RadioSelect(attrs={'class':"radio-level", 'oninvalid':"setCustomValidity('Please select a starting TRL.')"}),
            help_text="Starting TRL")
    sophia_numbers = forms.CharField(max_length=128, required=False, validators=[RegexValidator(r'([0-9]{4}-[0-9]{3})( *, *[0-9]{4}-[0-9]{3})*',),],
               widget=TextInput(attrs={'class':"long-info", 'autocomplete': "off", 'oninput': "validateProjectSophiaNumber(this)",
               'placeholder': "e.g. 1234-567", 'onfocus': "this.placeholder = ''", 'onblur': "this.placeholder = 'e.g. 1234-567'"}),
               help_text="Sophia Number(s)")  

    def __init__(self, *args, **kwargs):
        super(ProjectDetailsForm, self).__init__(*args, **kwargs)
        self.fields['technology'].initial =  Technology.objects.get(technology='both')
        self.fields['categories'].initial = Category.objects.all()
        self.fields['level'].initial =  Level.objects.get(number=1)
        
    def clean(self):
        cleaned_data = self.cleaned_data
        sophia_numbers = cleaned_data.get('sophia_numbers')

        if sophia_numbers:
            clean_sophia_numbers = ", ".join(sorted(list({number.strip() for number in sophia_numbers.split(',')})))
            cleaned_data['sophia_numbers'] = clean_sophia_numbers 

        return cleaned_data
    
    class Meta:
        model = Project
        fields = ('name', 'technology', 'categories', 'level', 'sophia_numbers',)


# Subclass of ProjectDetailsForm, initialises form values to the ones stored for the project
class UpdateProjectDetailsForm(ProjectDetailsForm):
    def __init__(self, project_id, *args, **kwargs):
        super(UpdateProjectDetailsForm, self).__init__(*args, **kwargs)
        self.fields.pop('level')
        project = Project.objects.get(pk=project_id)
        
        # Set initial values
        self.fields['name'].initial = project.name
        self.fields['sophia_numbers'].initial = project.sophia_numbers
        self.fields['technology'].initial = project.technology
        self.fields['categories'].initial = [cat for cat in project.categories.all()]
        
        # Make into auto-save fields
        for field_name in ['name', 'technology', 'categories']:
            self.fields[field_name].widget.attrs = add_autosave_attributes(self.fields[field_name].widget.attrs)
    
    class Meta:
        model = Project
        fields = ('name', 'technology', 'categories', 'sophia_numbers',)
        
class GeneratePDFForm(forms.Form):
    COMMENT_CHOICES = [("Yes", "Yes"),
                       ("No", "No")]
    VERSION_CHOICES = [("Summary", "Summary"),
                        ("Extended", "Extended")]
    
    version = forms.ChoiceField(help_text="Version", choices=VERSION_CHOICES,
                                widget=RadioSelect(attrs={'onchange':"activateFields(this)"}))
    from_level = forms.ModelChoiceField(help_text="From level", queryset=Level.objects.exclude(number=0), required=False, empty_label=None, 
                                        widget=Select(attrs={'disabled':"disabled", 'title':"Extended version only"}))
    to_level = forms.ModelChoiceField(help_text="To level", queryset=Level.objects.exclude(number=0), required=False, empty_label=None,
                                      widget=Select(attrs={'disabled':"disabled", 'title':"Extended version only"}))
    comments = forms.ChoiceField(help_text="Include comments", choices=COMMENT_CHOICES, required=False, 
                                         widget=RadioSelect(attrs={'disabled':"disabled", 'title':"Extended version only"}))
    
    def __init__(self, *args, **kwargs):
        super(GeneratePDFForm, self).__init__(*args, **kwargs)
        self.fields['version'].initial = ("Summary", "Summary")
        self.fields['from_level'].initial = Level.objects.get(number=1)
        self.fields['to_level'].initial = Level.objects.get(number=9)
        self.fields['comments'].initial = ("No", "No")