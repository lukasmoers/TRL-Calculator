import io, os, sys, random
from django.test import TestCase
from trl.models import UserProfile, Project, Level, Technology, Category, ProjectLevelCompletion, ProjectRequirementCompletion
from trl.population import basic_structure_population, mock_data_population

sys.stdout = open(os.devnull, 'w')

class PopulationTest(TestCase):
    
    def setUp(self):
        random.seed(2019)
        basic_structure_population.populate(verbose=True)
        self.TECHNOLOGIES = Technology.objects.all()
        self.CATEGORIES = Category.objects.all()
        self.LEVELS = Level.objects.all()
        self.users = [
            {"guid":"2506458d", "password":"1234", "full_name":"Ben Diesel"},
            {"guid":"2354792r", "password":"1234", "full_name":"Michelle RedHood"},
            {"guid":"2501456d", "password":"1234", "full_name":"Lilian Denver"},
            {"guid":"2157452b", "password":"1234", "full_name":"Susan Boyle"},
            {"guid":"2259812m", "password":"1234", "full_name":"Donald McDonalds"},
            {"guid":"2154870r", "password":"1234", "full_name":"Toble Rone"},
            {"guid":"1234567b", "password":"1234", "full_name":"Joe Bloggs"},
        ]

    def test_basic_structure_population(self):
        for tech in Technology.get_types():
            self.assertTrue(self.TECHNOLOGIES.filter(technology=tech[0]).exists())
        for cat in Category.get_categories():
            self.assertTrue(self.CATEGORIES.filter(category=cat[0]).exists())
        for i in range(Level.get_max()+1):
            self.assertTrue(self.LEVELS.filter(number=i).exists())
    
    def test_mock_data_population(self):
        random.seed(2019)
        mock_data_population.populate(verbose=True)
        
        # Assert that each test user was created with the correct details
        for i, test_user in enumerate(self.users):
            user = UserProfile.objects.get(guid=test_user['guid'])
            self.assertEqual(user.full_name, test_user['full_name'])
            self.assertTrue(user.check_password(test_user['password']))
            
            # Assert that a project was created for each test user
            project = Project.objects.get(owner=user)
            self.assertEqual(project.name, f"Project {i+1}")
            self.assertIn(project.technology, self.TECHNOLOGIES)
            self.assertIn(project.categories.all()[0], self.CATEGORIES)
            self.assertIn(project.level, self.LEVELS)
            self.assertEqual(project.owner, user)
            
            # Assert that each project requirement was completed at some percentage
            for req in project.requirements.all():
                project_req = ProjectRequirementCompletion.objects.get(project=project, requirement=req)
                self.assertGreaterEqual(project_req.percentage, 0)
                self.assertLessEqual(project_req.percentage, 100)
                
            # Assert that each project level was completed at 100%
            for i in range(project.level.number + 1):
                update_level = Level.objects.get(number=i)
                project_level = ProjectLevelCompletion.objects.get(project=project, level=update_level)
                self.assertEqual(project_level.percentage, 100)
                for project_req in ProjectRequirementCompletion.objects.filter(project=project, requirement__level=update_level):
                    self.assertEqual(project_req.percentage, 100)
        
