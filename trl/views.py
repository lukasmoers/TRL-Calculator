import datetime, json, os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from django.urls import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, FieldDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.template.loader import get_template
from django_htmx.http import trigger_client_event
from trl.models import Project, Technology, Level, Requirement, ProjectRequirementCompletion, ProjectLevelCompletion, UserProfile
from trl.forms import ProjectDetailsForm, UpdateProjectDetailsForm, GeneratePDFForm
from weasyprint import HTML
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# -----------------------------------------------------------------------------------
# HELPER METHODS
# -----------------------------------------------------------------------------------

# Finds requested project,
# throws 404 if project doesn't exist or not owned by current user (unless superuser)
def validate_project(user_accessing, project_id):
    if user_accessing.is_superuser:
        project = get_object_or_404(Project, pk=project_id)
    else:
        project = get_object_or_404(Project, pk=project_id)
        if project.owner != user_accessing:
            raise PermissionDenied
    return project


# Finds requested level,
# creates redirection to project's next level page if level doesn't exist
def validate_level(level_no, project_id):
    level = Level.objects.filter(number=level_no).first()
    project = get_object_or_404(Project, pk=project_id)
    if not level:
        next_project_level = min([project.level.number + 1, Level.get_max()])
        return None, redirect(reverse('trl:project_level_requirements', args=(project_id, next_project_level)))
    elif level.number == 0:
        # if TRL0 is requested, redirect to project details page
        return None, redirect(reverse('trl:update_project_details', args=(project_id,)))
    return level, None
    
    
# Gets the requirement completions of the given level,
# relevant to the given project's technology and category types
def filter_relevant_requirements(project, from_level, to_level=None):
    to_level = from_level if to_level == None else to_level
    BOTH = Technology.objects.get(technology='both')
    
    relevant_requirements = ProjectRequirementCompletion.objects.filter(
        project=project,
        requirement__category__in=project.categories.all(), 
        requirement__level__number__gte=from_level.number, 
        requirement__level__number__lte=to_level.number 
    )
    
    if project.technology == BOTH:
        return relevant_requirements.order_by('pk') 
    else:
        return relevant_requirements.filter(
            Q(requirement__technology=project.technology) | Q(requirement__technology=BOTH)
        ).order_by('pk')


# All possible circumstances for updating the completed and semi-completed levels of the given project
def reduce_semi_level(project, incomplete_level):
    new_semi_number = incomplete_level.number - 1
    project.level_semi = Level.objects.get(number=new_semi_number)


def advance_semi_level(project, new_level, new_level_completion):
    # Advance semi-completed level as much as possible (last consecutive level with >=67% completion) 
    while new_level_completion >= Level.get_semi_cutoff():
        project.level_semi = new_level
        new_number = new_level.number + 1
        if new_number > Level.get_max():
            break
        new_level = Level.objects.get(number=new_number)
        new_level_completion = ProjectLevelCompletion.objects.get(project=project, level=new_level).percentage
        
        
def reduce_completed_and_semi_level(project, incomplete_level, old_level_completion):
    new_complete_number = incomplete_level.number - 1
    if old_level_completion >= Level.get_semi_cutoff():
        if project.level_semi.number < incomplete_level.number:
            project.level_semi = project.level
    else:
        project.level_semi = Level.objects.get(number=new_complete_number)
    project.level = Level.objects.get(number=new_complete_number)
    ProjectLevelCompletion.objects.filter(project=project, level__number__gt=new_complete_number).update(completion_date=None)
    
    
def advance_completed_and_semi_level(project, new_level, new_level_completion):
    # Advance completed level as much as possible (last consecutive level with 100% completion)
    while new_level_completion >= Level.get_complete_cutoff():
        if project.level.number < new_level.number:
            ProjectLevelCompletion.objects.filter(project=project, level=new_level).update(completion_date=make_aware(datetime.datetime.now()))
        project.level = new_level
        if new_level.number >= project.level_semi.number:
            project.level_semi = new_level
            
        new_number = new_level.number + 1
        if new_number > Level.get_max():
            break
        new_level = Level.objects.get(number=new_number)
        new_level_completion = ProjectLevelCompletion.objects.get(project=project, level=new_level).percentage
    
    # Advance semi-completed level from that point onward
    advance_semi_level(project, new_level, new_level_completion)

        
def update_project_level_completion(project, level):
    relevant_requirements = filter_relevant_requirements(project, level)
    if relevant_requirements:
        ratio_completed = (100 * relevant_requirements.filter(percentage__gte=100).count()) // relevant_requirements.count()
    else:
        ratio_completed = 100
    
    ProjectLevelCompletion.objects.filter(project=project, level=level).update(percentage=ratio_completed)
    
    if level.number <= project.level.number and ratio_completed < Level.get_complete_cutoff():
        reduce_completed_and_semi_level(project, level, ratio_completed)

    elif level.number == project.level.number + 1 and ratio_completed >= Level.get_complete_cutoff():
        advance_completed_and_semi_level(project, level, ratio_completed)
            
    elif level.number <= project.level_semi.number and ratio_completed < Level.get_semi_cutoff():
        reduce_semi_level(project, level)
        
    elif level.number == project.level_semi.number + 1 and ratio_completed >= Level.get_semi_cutoff():
        advance_semi_level(project, level, ratio_completed)
        
    project.save()
    
def back_or_home(request):
    source = request.META.get('HTTP_REFERER')
    if source:
        return source
    else:
        return "home"
    

# -----------------------------------------------------------------------------------
# VIEWS
# -----------------------------------------------------------------------------------


def home(request):
    if os.environ.get('SERVER') == "True":
        if "Dh75Hdyt76" in request.headers:
            guid = request.headers['Dh75Hdyt76']
            get_name= request.headers['Dh75Hdyt77']
            try:
                user = authenticate(guid=guid)
                if user:
                    if user.is_active:
                        login(request, user, backend='trl.authentication.guidAuthenticationBackEnd' )
                        return render(request, 'trl/home.html', context = {})
                    else:
                        return HttpResponse("Your TRL account is disabled.")
                else:
                    raise UserProfile.DoesNotExist
            except(User.DoesNotExist, UserProfile.DoesNotExist):
                user = UserProfile.objects.get_or_create(guid=guid, full_name = get_name)[0]
                user.save()
                login(request,user, backend='trl.authentication.guidAuthenticationBackEnd' )
    
    return render(request, 'trl/home.html', context={})

def about(request):
    context_dict = {}
    context_dict['levels'] = Level.objects.exclude(number=0)
    return render(request, 'trl/about.html', context=context_dict)

def tutorial(request):
    return render(request, 'trl/tutorial.html', context={})

def local_register(request):
    if os.environ.get('SERVER') == "True":
        return redirect(os.environ.get('SERVER_URL'))
    
    context_dict = {}
    context_dict["guid"] = ""
    context_dict["full_name"] = ""
    
    if request.method == 'POST':
        guid = request.POST.get('guid')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        
        context_dict["guid"] = guid
        context_dict["full_name"] = full_name

        existing = UserProfile.objects.filter(guid=guid)
        if existing:
            print(f"User with GUID {guid} already exists.")
            context_dict["error"] = "User with this GUID already exists."
        else:
            print(f"Registered user with GUID {guid}.")
            user = UserProfile.objects.get_or_create(guid=guid, full_name=full_name, password=password)[0]
            user.set_password(password)
            user.save()
            login(request, user)
            return redirect(reverse('trl:portfolio'))
    
    return render(request, 'trl/local_register.html', context=context_dict)

def local_login(request):
    if os.environ.get('SERVER') == "True":
        return redirect(os.environ.get('SERVER_URL'))
    
    context_dict = {}
    context_dict["guid"] = ""
    
    if request.method == 'POST':
        guid = request.POST.get('guid')
        context_dict["guid"] = guid
        
        password = request.POST.get('password')  
        user = authenticate(guid=guid, password=password)

        if user:
            if user.is_active:
                login(request, user)
                print(f"User {guid} login successful.")
                return redirect(reverse('trl:portfolio'))
            else:
                print(f"User {guid} disabled.")
                context_dict["error"] = "Your account is disabled."
        else:
            print(f"Invalid login details for user {guid}.")
            context_dict["error"] = "Wrong username or password."
    
    return render(request, 'trl/local_login.html', context=context_dict)


@login_required
def user_logout(request):
    logout(request)
    return render(request, 'trl/local_login.html')
    
    
@login_required
def portfolio(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'trl/portfolio.html', context={'projects' : projects})
    

@login_required
def delete_project(request, project_id):
    project = validate_project(request.user, project_id)
    project.delete()
    return redirect(reverse('trl:portfolio'))

    
@login_required
def new_project_details(request):
    context_dict = {}
    # For project name validation
    context_dict['project_names'] = json.dumps(list(Project.objects.filter(owner=request.user).values_list('name', flat=True)))
    
    if request.method == 'POST':
        details_form = ProjectDetailsForm(request.POST)
        context_dict['details_form'] = details_form
        
        if details_form.is_valid():
            try:
                project = details_form.save(commit=False)
                
                level_number_completed = int(details_form.cleaned_data['level'].number) - 1
                level_completed = Level.objects.get(number=level_number_completed)
                project.level = level_completed
                project.level_semi = level_completed
                project.creation_date = make_aware(datetime.datetime.now())
                project.last_modified_date = make_aware(datetime.datetime.now())
                project.owner = request.user
                project.save()
                
                # Save many-to-many fields now that project has id
                details_form.save_m2m()
                project.requirements.add(*Requirement.objects.all())
                project.level_completions.add(*Level.objects.all())
                
                # Set all completed levels & requirements to 100% completion
                completed_levels = ProjectLevelCompletion.objects.filter(project=project, level__number__lte=level_number_completed)
                completed_levels.update(percentage=100)
                completed_levels.update(completion_date=make_aware(datetime.datetime.now()))
                
                completed_requirements = filter_relevant_requirements(project, from_level=Level.objects.get(number=0), to_level=level_completed)
                completed_requirements.update(percentage=100)
                
                # Mark complete any other levels that contain no requirements for the given settings
                for level in Level.objects.filter(number__gt=level_number_completed):
                    update_project_level_completion(project, level)
                    project.save()
                
                return redirect(reverse('trl:project_level_requirements', args=(project.pk, level_completed.number + 1)))

            except (ObjectDoesNotExist, FieldDoesNotExist, IntegrityError) as e:
                print(e)
                if project and project.pk != None:
                    project.delete()
                context_dict['error'] = True
                return render(request, 'trl/new_project_details.html', context=context_dict)
        else:
            print(details_form.errors)
            
    else:
        context_dict['details_form'] = ProjectDetailsForm()
        
    return render(request, 'trl/new_project_details.html', context=context_dict)


@login_required
def update_project_details(request, project_id):
    project = validate_project(request.user, project_id)
    
    context_dict = {}
    context_dict['project'] = project
    # For project name validation
    context_dict['project_names'] = json.dumps(list(Project.objects.filter(owner=request.user).exclude(pk=project.pk).values_list('name', flat=True)))
    
    if request.method == 'POST':
        details_form = UpdateProjectDetailsForm(project_id, request.POST)
        context_dict['details_form'] = details_form
        
        if details_form.is_valid():
            try:
                project.name = details_form.cleaned_data['name']
                project.sophia_numbers = details_form.cleaned_data['sophia_numbers']
                project.technology = details_form.cleaned_data['technology']
                project.categories.set(details_form.cleaned_data['categories'])
                project.last_modified_date = make_aware(datetime.datetime.now())
                project.save()
                
                for level in Level.objects.exclude(number=0):
                    update_project_level_completion(project, level)
                    project.save()
                
                return redirect(reverse('trl:project_level_requirements', args=(project.pk, 1)))
                
            except (ObjectDoesNotExist, FieldDoesNotExist, IntegrityError) as e:
                print(e)
                context_dict['error'] = True
                return render(request, 'trl/update_project_details.html', context=context_dict)
        else:
            print(details_form.errors)
            
    else:
        context_dict['details_form'] = UpdateProjectDetailsForm(project_id)
        
    return render(request, 'trl/update_project_details.html', context=context_dict)
    
    
@login_required
def project_level_requirements(request, project_id, level_no):
    project = validate_project(request.user, project_id)
    level, next_level_page = validate_level(level_no, project_id)
    if not level:
        return next_level_page
    
    context_dict = {}
    context_dict['project'] = project
    context_dict['level'] = level
    context_dict['previous'] = level.number - 1
    context_dict['next'] = level.number + 1
    context_dict['categories'] = project.categories.all()
    context_dict['requirements'] = filter_relevant_requirements(project, level)
    
    # For roadmap updates
    context_dict['project_level_completions'] = ProjectLevelCompletion.objects.filter(project=project).order_by('level__number').values_list('percentage', flat=True)
    
    if request.method == 'POST':
        try:
            # Save new percentages for each requirement
            for req in context_dict['requirements']:
                req.percentage = int(request.POST.get("slider-" + str(req.pk), req.percentage))
                req.comment = request.POST.get("comment-" + str(req.pk), req.comment)
                req.save()
                
            update_project_level_completion(project, level)
            project.last_modified_date = make_aware(datetime.datetime.now())
            project.save()
            
            response = render(request, 'trl/roadmap.html', context=context_dict)
            return trigger_client_event(response, "levelUpdate")
            
        except Exception as e:
            print(e)
            context_dict['error'] = True
            return render(request, 'trl/project_level_requirements.html', context=context_dict)
    
    return render(request, 'trl/project_level_requirements.html', context=context_dict)

@login_required
def project_level_update(request, project_id, level_no):
    if request.META.get('HTTP_REFERER'):
        project = validate_project(request.user, project_id)
        level, next_level_page = validate_level(level_no, project_id)
        if not level:
            return next_level_page
        
        context_dict = {}
        context_dict['project'] = project
        context_dict['current_level'] = level
        context_dict['levels'] = Level.objects.exclude(number=0).order_by('number')
        context_dict['functional'] = True
        return render(request, 'trl/roadmap.html', context=context_dict)
    else:
        return redirect(reverse('trl:project_level_requirements', args=(project_id, level_no)))
    
@login_required
def project_overview(request, project_id):
    project = validate_project(request.user, project_id)

    next_level_number = min([project.level.number + 1, Level.get_max()])
    next_level = Level.objects.get(number=next_level_number)
    relevant_requirements = filter_relevant_requirements(project, next_level)
    incomplete = relevant_requirements.filter(percentage__lt=Level.get_complete_cutoff()).order_by('-percentage')

    context_dict = {}
    context_dict['project'] = project
    context_dict['next_level'] = next_level
    context_dict['categories'] = project.categories.all()
    context_dict['requirements'] = incomplete[:3] if len(incomplete) > 3 else incomplete
    context_dict['pdf_form'] = GeneratePDFForm()

    return render(request, 'trl/project_overview.html', context=context_dict)

@login_required
def pdf_generator(request, project_id):
    if request.method == 'POST':
        project = validate_project(request.user, project_id) 
        pdf_form = GeneratePDFForm(request.POST)

        if pdf_form.is_valid():
            try: 
                next_level_number = min([project.level.number + 1, Level.get_max()])
                next_level = Level.objects.get(number=next_level_number)

                context_dict = {}
                context_dict['project'] = project
                context_dict['categories'] = project.categories.all()
                context_dict['next_level'] = next_level
                context_dict['levels'] = Level.objects.exclude(number=0).order_by('number')
                context_dict['project_levels'] = ProjectLevelCompletion.objects.filter(project=project).exclude(level__number=0).order_by('level__number')
   
                version = pdf_form.cleaned_data['version']
                context_dict['version'] = version

                if version == 'Extended':
                    from_level = pdf_form.cleaned_data['from_level']
                    to_level = pdf_form.cleaned_data['to_level']
                    context_dict['from_level'] = from_level
                    context_dict['to_level'] = to_level
                    context_dict['levels_extended'] = Level.objects.filter(number__gte=from_level.number, number__lte=to_level.number).order_by('number')
                    context_dict['requirements'] = filter_relevant_requirements(project, from_level=from_level, to_level=to_level)
                    if pdf_form.cleaned_data['comments'] == 'Yes':
                        context_dict['comments'] = True

                html_template = get_template('trl/pdf_generator.html').render(context_dict)
                pdf_file = HTML(string=html_template, encoding='utf-8').write_pdf()
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'filename="TRL Report - {project.name}.pdf"'
                return response
                    
            except (ObjectDoesNotExist, FieldDoesNotExist, IntegrityError) as e:
                print(e)
                context_dict['error'] = True
        else:
            print(pdf_form.errors)
    return redirect(reverse('trl:project_overview', args=(project_id,)))
    
    
def page_not_found(request, exception):
    context_dict = {'button': back_or_home(request)}
    return render(request, 'trl/error_page_not_found.html', context=context_dict)

def server_error(request):
    context_dict = {'button': back_or_home(request)}
    return render(request, 'trl/error_with_request.html', context=context_dict)
    
def bad_request(request, exception):
    context_dict = {'button': back_or_home(request)}
    return render(request, 'trl/error_with_request.html', context=context_dict)
    
def forbidden(request, exception):
    context_dict = {'button': back_or_home(request)}
    return render(request, 'trl/error_forbidden.html', context=context_dict)