import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sh30-main.settings")

import argparse
parser = argparse.ArgumentParser(
    description='Populate database with basic structural elements.'
)
parser.add_argument("-v","--verbose", action="store_true", help="to see updates throughout the population process")

import django
django.setup()

import random
from trl.models import Technology, Category, Level, Requirement
from trl.population.level_requirements_data import get_level

def populate(verbose=False):
    print("Populating basic structure...")
    
    TECHNOLOGIES = Technology.get_types()
    CATEGORIES = Category.get_categories()
    LEVELS = Level.get_max()

    for tech in TECHNOLOGIES:
        if verbose:
            print(f"Adding technology: {tech}...")
        technology = add_technology(tech[0])
        
    if verbose:
        print("__________________________________________________________")  

    for cat in CATEGORIES:
        if verbose:
            print(f"Adding category: {cat}...")
        category = add_category(cat[0])
        
        
    if verbose:    
        print("__________________________________________________________")  

    for i in range(LEVELS + 1):
        if verbose:
            print(f"Adding level: {i}...")
            
        level_requirements = get_level(i)
        level = add_level(i, level_requirements['title'], level_requirements['description'])
        
        if i != 0:
            for req in level_requirements['requirements']:
                if verbose:
                    print(f"Adding requirement: {req['description']}...")
                add_requirement(level, **req)
                
        if verbose:
            print("__________________________________________________________")

def add_technology(technology):
    tech = Technology.objects.get_or_create(technology=technology)[0]
    tech.icon = 'icons/' + technology + '.png'
    tech.save()
    return tech
    
def add_category(category):
    cat = Category.objects.get_or_create(category=category)[0]
    cat.icon = 'icons/' + category + '.png'
    cat.save()
    return cat
    
def add_level(number, title, description):
    level = Level.objects.get_or_create(number=number, title=title, description=description)[0]
    level.save()
    return level
    
def add_requirement(level, description, category, technology):
    cat = Category.objects.get(category=category)
    tech = Technology.objects.get(technology=technology)
    req = Requirement.objects.get_or_create(description=description, technology=tech, category=cat, level=level)[0]
    req.save()
    return req   

# Start execution here!
if __name__ == '__main__':
    args = parser.parse_args()
    populate(verbose=args.verbose)