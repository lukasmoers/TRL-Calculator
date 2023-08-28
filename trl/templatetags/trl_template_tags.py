import os
from django import template
from django.forms.models import model_to_dict
from trl.models import Level
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

register = template.Library()

@register.inclusion_tag('trl/roadmap.html')
def get_roadmap(project=None, current_level=-1, functional=False):
    return {'project': project,
            'levels': Level.objects.exclude(number=0).order_by('number'),
            'levels_json': [model_to_dict(level) for level in Level.objects.exclude(number=0)],
            'current_level': current_level,
            'functional': functional}

@register.simple_tag
def get_complete_cutoff():
    return Level.get_complete_cutoff()
    
@register.simple_tag
def get_semi_cutoff():
   return Level.get_semi_cutoff()
   
@register.simple_tag
def get_max_level():
   return Level.get_max()

@register.filter
def get_item(iterable, key):
    try:
        return iterable[key]
    except:
        return ""
        
@register.filter
def filter_category(requirement_set, category):
    try:
        cat_reqs = requirement_set.filter(requirement__category=category).order_by('pk')
        return cat_reqs
    except:
        return ""
        
@register.filter
def filter_level(requirement_set, level):
    try:
        level_reqs = requirement_set.filter(requirement__level=level).order_by('pk')
        return level_reqs
    except:
        return ""

@register.filter
def verbose_tech(technology):
    if technology.technology == 'both':
        return "Software & Hardware"
    else:
        return technology
        
@register.filter
def cat_list(iterable):
    return ", ".join([str(item).split(' ')[0] for item in iterable])
  
@register.filter
def is_not_max_level(number):
    return number < Level.get_max()
    
@register.filter
def is_complete(level_number, project):
    if not project:
        return False
    return level_number <= project.level.number
    
@register.filter
def is_semi(level_number, project):
    if not project:
        return False
    return level_number <= project.level_semi.number

@register.filter
def get_login_url(login_url):
    if os.environ.get('SERVER') == "True":
        return os.environ.get('SERVER_URL')
    else:
        return login_url


