import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sh30-main.settings")

import argparse
parser = argparse.ArgumentParser(
    description='Populate database with mock data for testing.'
)
parser.add_argument("-v","--verbose", action="store_true", help="to see updates throughout the population process")

import django
django.setup()

import random
from trl.models import UserProfile, Project, Requirement, Level, ProjectRequirementCompletion, ProjectLevelCompletion, Technology, Category
from trl.population import basic_structure_population

random.seed(2019)

def populate(verbose=False):
    basic_structure_population.populate(verbose)
    
    print("Populating mock data...")
    users = [ {"guid":"2506458d", "password":"1234", "full_name":"Ben Diesel"},
              {"guid":"2354792r", "password":"1234", "full_name":"Michelle RedHood"},
              {"guid":"2501456d", "password":"1234", "full_name":"Lilian Denver"},
              {"guid":"2157452b", "password":"1234", "full_name":"Susan Boyle"},
              {"guid":"2259812m", "password":"1234", "full_name":"Donald McDonalds"},
              {"guid":"2154870r", "password":"1234", "full_name":"Toble Rone"},
              {"guid":"1234567b", "password":"1234", "full_name":"Joe Bloggs"},]
    
    TECHNOLOGIES = Technology.objects.all()
    CATEGORIES = Category.objects.all()
    LEVELS = Level.objects.all()

    for i, test_user in enumerate(users):
        user = add_user(**test_user)
        if verbose:
            print("Adding user...")
            print("GUID: ", user.guid)
            print("Name: ", user.full_name)
        
        project = add_project(f"Project {i+1}",
                              TECHNOLOGIES[random.randint(0, TECHNOLOGIES.count()-1)],
                              CATEGORIES[random.randint(0, CATEGORIES.count()-1)],
                              LEVELS[random.randint(0, LEVELS.count()-1)],
                              user)
        if verbose:
            print(f"Adding project for user...")
            print("Project Name: ", project.name)
            print("Project Technology: ", project.technology)
            print("Project Categories: ", project.categories.all()[0])
            print("Project TRL Level: ", project.level)
            print("Project Owner: ", project.owner.guid)
            print("__________________________________________________________\n")
       

def add_user(guid, password, full_name):
    user = UserProfile.objects.get_or_create(guid=guid,
                                             password=password,
                                             full_name=full_name)[0]
    user.set_password(password)
    user.save()
    return user

def add_project(name, technology, category, level, owner):
    project = Project.objects.get_or_create(name=name, 
                                            technology=technology, 
                                            level=level,
                                            level_semi=level,
                                            owner=owner)[0]
    project.save()
    project.categories.add(category)
    project.requirements.add(*Requirement.objects.all())
    project.level_completions.add(*Level.objects.all())
    project.save()
    for req in project.requirements.all():
        project_req = ProjectRequirementCompletion.objects.get(project=project, requirement=req)
        project_req.percentage = random.randint(0,100)
        project_req.save()

    for i in range(level.number + 1):
        update_level = Level.objects.get(number=i)
        project_level = ProjectLevelCompletion.objects.get(project=project, level=update_level)
        project_level.percentage = 100
        project_level.save()
        for project_req in ProjectRequirementCompletion.objects.filter(project=project, requirement__level=update_level):
            project_req.percentage = 100
            project_req.save()
    
    return project

# Start execution here!
if __name__ == '__main__':
    args = parser.parse_args()
    populate(verbose=args.verbose)