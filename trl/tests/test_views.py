import os, sys, datetime
from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client
from django.utils.timezone import make_aware
from django.core.exceptions import PermissionDenied
from trl.views import validate_project, validate_level, advance_completed_and_semi_level, reduce_completed_and_semi_level, reduce_semi_level, update_project_level_completion                     
from trl.models import UserProfile, Project, Level, Technology, Category, Requirement, ProjectLevelCompletion, ProjectRequirementCompletion

sys.stdout = open(os.devnull, 'w')

class LocalLoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('trl:login')
        self.portfolio_url = reverse('trl:portfolio')
        self.user_data = {
            'guid': '2546875d',
            'full_name': 'Joe Bloggs',
            'password': '1234'
        }
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()

    def test_login_success(self):
        response = self.client.post(self.login_url, self.user_data)
        self.assertRedirects(response, self.portfolio_url, status_code=302, target_status_code=200, fetch_redirect_response=True)

    def test_login_failure(self):
        response = self.client.post(self.login_url, {'guid': 'invaliduser', 'password': 'invalidpass'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wrong username or password.')
        self.assertFalse('_auth_user_id' in self.client.session)

class LocalRegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('trl:register')
        self.portfolio_url = reverse('trl:portfolio')
        self.user_data = {
            'guid': '2546875d',
            'full_name': 'Joe Bloggs',
            'password': '1234'
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertRedirects(response, self.portfolio_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        self.assertTrue(UserProfile.objects.filter(guid='2546875d').exists())

    def test_register_failure(self):
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User with this GUID already exists.')
        self.assertFalse('_auth_user_id' in self.client.session)

class DeleteProjectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserProfile.objects.create_user(guid='2546875d',password='1234', full_name='Joe Bloggs')
        self.user.set_password('1234')
        self.user.save()
        
        owner = UserProfile.objects.get(guid = "2546875d")
        both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")    
        self.project = Project.objects.create(name = "Project 2",
                                technology = both_technology,
                                level = level_1,
                                level_semi = level_2,
                                owner = owner,)
        self.project.categories.add(trl_category)
        
        self.delete_url = reverse('trl:delete_project', args=[self.project.pk,])
        self.portfolio_url = reverse('trl:portfolio')

    def test_delete_project(self):
        self.client.login(guid='2546875d', password='1234')
        response = self.client.get(self.delete_url)
        self.assertRedirects(response, self.portfolio_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        self.assertFalse(Project.objects.filter(name = "Project 2").exists())

class UpdateLevelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserProfile.objects.create_user(guid='2546875d',password='1234', full_name='Joe Bloggs')
        
        for i in range(Level.get_max() + 1):
            Level.objects.create(number = i, title = f"Level {i}", description = f"Level {i} description")
        
        owner = UserProfile.objects.get(guid = "2546875d")
        both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        
        # Project to advance
        current_level = Level.objects.get(number=1)
        self.project_1 = Project.objects.create(name = "Project 1",
                                technology = both_technology,
                                level = current_level,
                                level_semi = current_level,
                                owner = owner,)
        self.project_1.categories.add(trl_category)
        ProjectLevelCompletion.objects.create(project=self.project_1, level=Level.objects.get(number=1), percentage=100)
        for i in range(3, 6):
            ProjectLevelCompletion.objects.create(project=self.project_1, level=Level.objects.get(number=i), percentage=Level.get_complete_cutoff())
        for i in range(6, 9):
            ProjectLevelCompletion.objects.create(project=self.project_1, level=Level.objects.get(number=i), percentage=Level.get_semi_cutoff())
        ProjectLevelCompletion.objects.create(project=self.project_1, level=Level.objects.get(number=9), percentage=0)
        
        # Project to reduce
        current_level = Level.objects.get(number=5)
        current_semi_level = Level.objects.get(number=8)
        self.project_2 = Project.objects.create(name = "Project 2",
                                technology = both_technology,
                                level = current_level,
                                level_semi = current_semi_level,
                                owner = owner,)
        self.project_2.categories.add(trl_category)
        for i in range(1, 4):
             ProjectLevelCompletion.objects.create(project=self.project_2, level=Level.objects.get(number=i), percentage=Level.get_complete_cutoff())
    
    def test_advance_success(self):
        new_level = Level.objects.get(number=2)
        new_level_completion = ProjectLevelCompletion.objects.create(project=self.project_1, level=new_level, percentage=Level.get_complete_cutoff())
        advance_completed_and_semi_level(self.project_1, new_level, new_level_completion.percentage)
        self.assertEqual(self.project_1.level.number, 5)
        self.assertEqual(self.project_1.level_semi.number, 8) 

    def test_advance_failure(self):
        new_level = Level.objects.get(number=2)
        new_level_completion = ProjectLevelCompletion.objects.create(project=self.project_1, level=new_level, percentage=(Level.get_semi_cutoff()-1))
        advance_completed_and_semi_level(self.project_1, new_level, new_level_completion.percentage)
        self.assertEqual(self.project_1.level.number, 1)
        self.assertEqual(self.project_1.level_semi.number, 1)
        
    def test_reduce_level(self):
        failed_level = Level.objects.get(number=4)
        failed_level_completion = ProjectLevelCompletion.objects.create(project=self.project_2, level=failed_level, percentage=(Level.get_semi_cutoff()-1))
        reduce_completed_and_semi_level(self.project_2, failed_level, failed_level_completion.percentage)
        self.assertEqual(self.project_2.level.number, 3)
        self.assertEqual(self.project_2.level_semi.number, 3) 

    def test_reduce_semi_level(self):
        failed_level = Level.objects.get(number=7)
        reduce_semi_level(self.project_2, failed_level)
        self.assertEqual(self.project_2.level.number, 5)
        self.assertEqual(self.project_2.level_semi.number, 6)
        
    def test_update_project_level_completion(self):
        new_level = Level.objects.get(number=2)
        ProjectLevelCompletion.objects.create(project=self.project_1, level=new_level, percentage=0)
        update_project_level_completion(self.project_1, new_level)
        self.assertEqual(self.project_1.level.number, 5)
        self.assertEqual(self.project_1.level_semi.number, 8) 

class ValidateUrlArgumentsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_1 = UserProfile.objects.create(guid = "2546875d", full_name = "John Doe", password = "1234")
        self.user_2 = UserProfile.objects.create(guid = "2546876f", full_name = "John Doe", password = "1234")
        self.superuser = UserProfile.objects.create_superuser("admin", "1234")

        owner = UserProfile.objects.get(guid="2546875d")
        both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        self.level_1 = level_1
        self.project = Project.objects.create(name = "Project 1",
                                           technology = both_technology,
                                           level = level_1,
                                           level_semi = level_1,
                                           owner = owner)
        self.project.categories.add(trl_category)
        
    def test_validate_project_success(self):
        project_obj = validate_project(self.user_1, self.project.pk)
        self.assertTrue(project_obj is not None)
        self.assertEqual(project_obj.pk, self.project.pk)
    
    def test_validate_project_superuser_success(self):
        project_obj = validate_project(self.superuser, self.project.pk)
        self.assertTrue(project_obj is not None)
        self.assertEqual(project_obj.pk, self.project.pk)
    
    def test_validate_project_failure(self):
        self.assertRaises(PermissionDenied, lambda: validate_project(self.user_2, self.project.pk))
        
    def test_validate_level_success(self):
        level_obj, redirection = validate_level(1, self.project.pk)
        self.assertTrue(level_obj is not None)
        self.assertIsNone(redirection)
        self.assertEqual(level_obj, self.level_1)
        
    def test_validate_level_failure(self):
        level_obj, redirection = validate_level(Level.get_max()+1, self.project.pk)
        self.assertIsNone(level_obj)
        self.assertTrue(redirection is not None)
    
  
class NewProjectDetailsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        for i in range(Level.get_max() + 1):
            Level.objects.create(number = i, title = f"Level {i}", description = f"Level {i} description")
        self.both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        self.trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        self.level_1 = Level.objects.get(number = 1)        
        
        self.project_data = {
            'name' : "Project 1",
            'technology' : self.both_technology.pk,
            'categories': self.trl_category.pk,
            'level' : self.level_1.pk,
            'sophia_numbers' : '1234-567'
        }

        self.user_data = {'guid': '2546875d', 'full_name': 'Joe Bloggs', 'password': '1234'}
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        
    def test_new_project(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        
        new_url = reverse('trl:new_project_details')
        response = self.client.post(new_url, self.project_data)
        project = Project.objects.filter(name=self.project_data['name'])
        
        self.assertTrue(project.exists())
        project = project.first()
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.name, self.project_data['name'])
        self.assertEqual(project.technology.pk, self.project_data['technology'])
        self.assertEqual(project.categories.first(), Category.objects.get(pk=self.project_data['categories']))
        self.assertEqual(project.sophia_numbers, self.project_data['sophia_numbers'])
        self.assertEqual(project.creation_date.date(), make_aware(datetime.datetime.now()).date())
        self.assertEqual(project.last_modified_date.date(), make_aware(datetime.datetime.now()).date())
        
        level_url = reverse('trl:project_level_requirements', args=[project.pk, 1])
        self.assertRedirects(response, level_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        
        
class UpdateProjectDetailsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {'guid': '2546875d', 'full_name': 'Joe Bloggs', 'password': '1234'}
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        
        for i in range(Level.get_max() + 1):
            Level.objects.create(number = i, title = f"Level {i}", description = f"Level {i} description")
        current_level = Level.objects.get(number=1)
        for (tech, full) in Technology.get_types():
            Technology.objects.create(technology = tech, icon = f"icons/{tech}.png")
        for (cat, full) in Category.get_categories():
            Category.objects.create(category = cat, icon = f"icons/{cat}.png")
        
        self.project = Project.objects.create(
            name = "Project 1",
            technology = Technology.objects.first(),
            level = current_level,
            level_semi = current_level,
            owner = self.user
        )
        
        self.project.categories.add(Category.objects.first())
        for i in range(Level.get_max() + 1):
            ProjectLevelCompletion.objects.create(project=self.project, level=Level.objects.get(number=i), percentage=0)
        
        self.project_data = {
            'name' : "Project 100",
            'technology' : Technology.objects.last().pk,
            'categories': Category.objects.last().pk,
            'sophia_numbers' : '7654-321'
        }
        
    def test_update_project(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        
        update_url = reverse('trl:update_project_details', args=[self.project.pk,])
        response = self.client.post(update_url, self.project_data)
        
        project = Project.objects.get(pk=self.project.pk)
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.name, self.project_data['name'])
        self.assertEqual(project.technology.pk, self.project_data['technology'])
        self.assertEqual(project.categories.first(), Category.objects.get(pk=self.project_data['categories']))
        self.assertEqual(project.sophia_numbers, self.project_data['sophia_numbers'])
        self.assertEqual(project.last_modified_date.date(), make_aware(datetime.datetime.now()).date())
        
        level_url = reverse('trl:project_level_requirements', args=[self.project.pk, 1])
        self.assertRedirects(response, level_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        
        
class ProjectLevelRequirementsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {'guid': '2546875d', 'full_name': 'Joe Bloggs', 'password': '1234'}
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        
        level_0 = Level.objects.create(number=0)
        level_1 = Level.objects.create(number=1)
        self.level_1 = level_1
        both_technology = Technology.objects.create(technology = "both", icon = f"icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = f"icons/trl.png")
        
        self.project = Project.objects.create(name="Project 1", technology=both_technology, level=level_1, level_semi=level_1, owner=self.user)
        self.project.categories.add(trl_category)
        
        ProjectLevelCompletion.objects.create(project=self.project, level=level_1, percentage=0)
        requirement = Requirement.objects.create(description="Requirement 1", level=level_1, technology=both_technology, category=trl_category,)
        self.req = ProjectRequirementCompletion.objects.create(project=self.project, requirement=requirement, percentage=0)
        
        self.req_data = {
            f"slider-{self.req.pk}" : 100,
            f"comment-{self.req.pk}" : "New comment.",
        }
        self.level_url = reverse('trl:project_level_requirements', args=[self.project.pk, 1])
    
    def test_project_level_requirements_get(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        response = self.client.get(self.level_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/project_level_requirements.html')
    
    def test_project_level_requirements_get_zero(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        level_url_0 = reverse('trl:project_level_requirements', args=[self.project.pk, 0])
        details_url = reverse('trl:update_project_details', args=[self.project.pk,])
        response = self.client.get(level_url_0)
        self.assertRedirects(response, details_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
    
    def test_project_level_requirements_post(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        response = self.client.post(self.level_url, self.req_data)
        
        project = Project.objects.get(pk=self.project.pk)
        requirement  = Requirement.objects.get(pk=self.req.requirement.pk)
        completion = ProjectRequirementCompletion.objects.get(project=project, requirement=requirement)
        level = ProjectLevelCompletion.objects.get(project=project, level=self.level_1)
        
        self.assertEqual(completion.percentage, self.req_data[f"slider-{self.req.pk}"])
        self.assertEqual(completion.comment, self.req_data[f"comment-{self.req.pk}"])
        self.assertEqual(level.percentage, 100)
        self.assertEqual(project.last_modified_date.date(), make_aware(datetime.datetime.now()).date())
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/roadmap.html')
        
        
class PdfGeneratorViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {'guid': '2546875d', 'full_name': 'Joe Bloggs', 'password': '1234'}
        self.user = UserProfile.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        
        for i in range(Level.get_max() + 1):
            Level.objects.create(number = i, title = f"Level {i}", description = f"Level {i} description")
        level_1 = Level.objects.get(number=1)
        self.level_1 = level_1
        both_technology = Technology.objects.create(technology = "both", icon = f"icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = f"icons/trl.png")
        self.project = Project.objects.create(name="Project 1", technology=both_technology, level=level_1, level_semi=level_1, owner=self.user)
        self.project.categories.add(trl_category)
        
        ProjectLevelCompletion.objects.create(project=self.project, level=level_1, percentage=0)
        requirement = Requirement.objects.create(description="Requirement 1", level=level_1, technology=both_technology, category=trl_category,)
        ProjectRequirementCompletion.objects.create(project=self.project, requirement=requirement, percentage=100, comment="New comment.")
        
        self.summary_data = {'version' : 'Summary'}
        self.extended_data = {'version' : 'Extended', 'from_level' : level_1.number, 'to_level' : level_1.number, 'comments' : 'Yes'}
        self.pdf_url = reverse('trl:pdf_generator', args=[self.project.pk,])
        
    def test_summary_pdf(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        response = self.client.post(self.pdf_url, self.summary_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual('application/pdf', response['Content-Type'])
        
    def test_extended_pdf(self):
        self.client.login(guid=self.user_data['guid'], password=self.user_data['password'])
        response = self.client.post(self.pdf_url, self.extended_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
class ErrorViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_1 = UserProfile.objects.create(guid = "2546875d", full_name = "John Doe", password = "1234")
        self.user_1.set_password("1234")
        self.user_1.save()
        self.user_2 = UserProfile.objects.create(guid = "2546876f", full_name = "Johnny Duh", password = "1234")
        self.user_2.set_password("1234")
        self.user_2.save()

        owner = UserProfile.objects.get(guid = "2546875d")
        both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")    
        level_9 = Level.objects.create(number = 9, title = "Level 9", description = "Level 9 description")  
        self.project_1 = Project.objects.create(name = "Project 1",
                                           technology = both_technology,
                                           level = level_1,
                                           level_semi = level_2,
                                           owner = owner)
        self.project_1.categories.add(trl_category)
    
    def test_404(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:project_overview', args=[2000,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/error_page_not_found.html')
        
    def test_403(self):
        self.client.login(guid='2546876f', password="1234")
        url = reverse('trl:project_overview', args=[self.project_1.pk,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/error_forbidden.html')
        
