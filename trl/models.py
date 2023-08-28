from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from .managers import CustomUserManager

# Fake user for offline/local usage
class UserProfile(AbstractUser, PermissionsMixin):
    username = None
    guid = models.CharField(max_length=10, primary_key=True, unique=True)
    full_name = models.CharField(max_length=80, default="Anonymous")

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'guid'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
    backend = 'trl.authentication.guidAuthenticationBackEnd'

    def __str__(self):
        return self.guid
        

class Level(models.Model):
    MAX_LEVEL = 9
    number = models.IntegerField(default=0, primary_key=True, unique=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(MAX_LEVEL)])
    title = models.CharField(max_length=128)
    description  = models.CharField(max_length=1024, default="")
    
    def __str__(self):
        return f"TRL {self.number}"
    
    @classmethod
    def get_max(cls):
        return cls.MAX_LEVEL
    
    @classmethod
    def get_complete_cutoff(cls):
        return 80
    
    @classmethod
    def get_semi_cutoff(cls):
        return 65


class Technology(models.Model):
    TYPES = (("software", "Software"),
            ("hardware", "Hardware"),
            ("both", "Both"))
    
    technology = models.CharField(max_length=8, unique=True, choices=TYPES)
    icon = models.ImageField()
    
    def __str__(self):
        return self.get_technology_display()
        
    @classmethod
    def get_types(cls):
        return cls.TYPES
    
    class Meta:
        verbose_name_plural = "Technologies"


class Category(models.Model):
    CATEGORIES = (("trl", "Technology Readiness"),
                 ("mrl", "Manufacturing Readiness"),
                 ("prl", "Programmatic Readiness"))
    
    category = models.CharField(max_length=23, unique=True, choices=CATEGORIES)
    icon = models.ImageField()

    def __str__(self):
        return self.get_category_display()
        
    @classmethod
    def get_categories(cls):
        return cls.CATEGORIES
    
    class Meta:
        verbose_name_plural = "Categories"
        

class Requirement(models.Model):   
    description = models.CharField(max_length=128, unique=True)
    explanation = models.CharField(max_length=1024, blank=True, null=True)
    technology = models.ForeignKey(Technology, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    level = models.ForeignKey(Level, on_delete=models.PROTECT)

    def __str__(self):
        return self.description


class Project(models.Model):
    name = models.CharField(max_length=128)
    technology = models.ForeignKey(Technology, on_delete=models.PROTECT)
    categories = models.ManyToManyField(Category)
    manager = models.CharField(max_length=128, blank=True)
    level = models.ForeignKey(Level, default=0, on_delete=models.PROTECT)
    level_semi = models.ForeignKey(Level, default=0, on_delete=models.PROTECT, related_name='+')
    level_completions = models.ManyToManyField(Level, through='ProjectLevelCompletion', related_name='+')
    requirements = models.ManyToManyField(Requirement, through='ProjectRequirementCompletion')
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now_add=True)
    sophia_numbers = models.CharField(max_length=128, validators=[RegexValidator(r'([0-9]{4}-[0-9]{3})(, [0-9]{4}-[0-9]{3})*',)], blank=True, null=True)
    
    def __str__(self):
        return self.name
        
    class Meta:
        unique_together = [['name', 'owner']]
        verbose_name_plural = "Projects"

class ProjectRequirementCompletion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    comment = models.CharField(max_length=1024, blank=True, default="")
    
    class Meta:
        unique_together = [['project', 'requirement']]
    
    class Meta:
        verbose_name_plural = "Project requirement completions"


class ProjectLevelCompletion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.PROTECT)
    percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completion_date = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = [['project', 'level']]
    
    class Meta:
        verbose_name_plural = "Project level completions"
    
    