from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from trl.forms import UserProfileCreationForm, UserProfileEditForm
from trl.models import UserProfile, Project, Level, Technology, Category, Requirement, ProjectRequirementCompletion, ProjectLevelCompletion
# Register your models here.

class UserProfileAdmin(UserAdmin):
    add_form = UserProfileCreationForm
    form = UserProfileEditForm
    model = UserProfile
    list_display = ("guid", "is_staff", "is_active",)
    list_filter = ("guid", "is_staff", "is_active",)
    fieldsets = (
        (None, {"fields": ('guid', "full_name",)}),
        ("Permissions", {"fields": ("is_staff", "is_active")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("guid", "full_name","is_staff", "is_active")}
        ),
    )

    search_fields = ("guid",)
    ordering = ("guid",)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'owner', 'level', 'creation_date', 'last_modified_date')
    
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('pk', 'level', 'description')

class ProjectRequirementCompletionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'project', 'requirement', 'percentage')
    
class ProjectLevelCompletionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'project', 'level', 'percentage', 'completion_date')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Level)
admin.site.register(Technology)
admin.site.register(Category)
admin.site.register(Requirement, RequirementAdmin)
admin.site.register(ProjectRequirementCompletion, ProjectRequirementCompletionAdmin)
admin.site.register(ProjectLevelCompletion, ProjectLevelCompletionAdmin)