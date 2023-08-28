import os, sys
from django.test import TestCase
from django.contrib.auth import get_user_model
from trl.models import UserProfile, Project, Technology, Category, Level, Requirement, ProjectLevelCompletion, ProjectRequirementCompletion

sys.stdout = open(os.devnull, 'w')

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user_profile = UserProfile.objects.create(guid="2506458d", full_name="John Doe")

    def test_user_profile_model(self):
        user = UserProfile.objects.get(guid="2506458d")
        self.assertEqual(str(user), user.guid)

class TechnologyModelTest(TestCase):
    def setUp(self):
        Technology.objects.create(technology='software', icon='test.png')

    def test_technology_model(self):
        technology = Technology.objects.get(technology='software')
        verbose_name = technology._meta.get_field('technology').verbose_name
        max_length = technology._meta.get_field('technology').max_length
        icon_field = technology._meta.get_field('icon').verbose_name
        expected_object_name = technology.get_technology_display()
        types = Technology.get_types()
        expected_types = (("software", "Software"), ("hardware", "Hardware"), ("both", "Both"))
        
        self.assertEqual(verbose_name, 'technology')
        self.assertEqual(max_length, 8)
        self.assertEqual(icon_field, 'icon')
        self.assertEqual(types, expected_types)
        self.assertEqual(expected_object_name, str(technology))
        self.assertEqual(str(Technology._meta.verbose_name_plural), "Technologies")

class CategoryModelTest(TestCase):
    def setUp(self):
        Category.objects.create(category='trl', icon='test.png')

    def test_category_model(self):
        category = Category.objects.get(category='trl')
        name_field = category._meta.get_field('category').verbose_name
        max_length = category._meta.get_field('category').max_length
        icon_field = category._meta.get_field('icon').verbose_name
        expected_object_name = category.get_category_display()
        categories = Category.get_categories()
        expected_categories = (("trl", "Technology Readiness"), 
                               ("mrl", "Manufacturing Readiness"), 
                               ("prl", "Programmatic Readiness"))
        
        self.assertEqual(str(Category._meta.verbose_name_plural), "Categories")
        self.assertEqual(expected_object_name, str(category))
        self.assertEqual(categories, expected_categories)
        self.assertEqual(icon_field, 'icon')
        self.assertEqual(name_field, 'category')
        self.assertEqual(max_length, 23)

class RequirementModelTest(TestCase):
    def setUp(self):
        both_technology = Technology.objects.create(technology = "both")
        trl_category = Category.objects.create(category = "trl")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")

        Requirement.objects.create(description = "Paper studies confirm basic principles",
                                    technology = both_technology,
                                    category = trl_category,
                                    level = level_1)

    def test_requirement_model(self):
        requirement = Requirement.objects.get(description = "Paper studies confirm basic principles")
        name_field = requirement._meta.get_field('description').verbose_name
        max_length = requirement._meta.get_field('description').max_length
        blank = requirement._meta.get_field('explanation').blank
        related_technology = requirement.technology
        related_category = requirement.category
        related_level = requirement.level
        
        self.assertEqual(name_field, 'description')
        self.assertEqual(max_length, 128)
        self.assertEqual(str(requirement), requirement.description)
        self.assertTrue(blank)
        self.assertIsInstance(related_technology, Technology)
        self.assertIsInstance(related_category, Category)
        self.assertIsInstance(related_level, Level)

class LevelModelTestCase(TestCase):
    def setUp(self):
        self.level = Level.objects.create(number=1, title="Basic Principles Observed", description= "Description of level 1")

    def test_level(self):
        self.assertEqual(str(self.level), 'TRL 1')
        self.assertEqual(Level.get_max(), 9)
        self.assertEqual(Level.get_complete_cutoff(), 80)
        self.assertEqual(Level.get_semi_cutoff(), 65)

class ProjectTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(guid = "2546875d", full_name = "John Doe", password = "1234")
        self.technology = Technology.objects.create(technology = "both")
        self.category = Category.objects.create(category = "trl")
        self.level = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")       
        project_1 = Project.objects.create(name = "Project 1",
                                technology = self.technology,
                                level = self.level,
                                manager = "Manager",
                                level_semi = level_2,
                                owner = self.user,)
        project_1.categories.add(self.category)  

    def test_project_model(self):
        self.project = Project.objects.get(name = "Project 1")
        project_created = Project.objects.count()
        self.assertEqual(project_created, 1)
        self.assertEqual(str(self.project), "Project 1")
        self.assertEqual(Project._meta.verbose_name_plural, 'Projects')
        self.assertEqual(self.project.technology, self.technology)
        self.assertEqual(self.project.manager, "Manager")
        self.assertEqual(self.project.level, self.level)
        self.assertEqual(self.project.owner, self.user)

    def test_project_uniqueness(self):
        with self.assertRaises(Exception):
            Project.objects.create(name='Test Project', owner=self.user)

       
class ProjectRequirementCompletionTest(TestCase):
    def setUp(self):
        john = get_user_model().objects.create(guid = "2546875d", full_name = "John Doe")
        both_technology = Technology.objects.create(technology = "both")
        trl_category = Category.objects.create(category = "trl")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")
        
        project_1 = Project.objects.create(name = "Project 1",
                                technology = both_technology,
                                level = level_1,
                                level_semi = level_2,
                                owner = john,)
        project_1.categories.add(trl_category)

        requirement = Requirement.objects.create(description = "Paper studies confirm basic principles",
                                    technology = both_technology,
                                    category = trl_category,
                                    level = level_1)
        ProjectRequirementCompletion.objects.create(project = project_1,
                                                    requirement = requirement,
                                                    percentage = 89,
                                                    comment = "Some comment",)

    def test_project_requirement_completion(self):
        project = Project.objects.get(name = "Project 1")
        requirement = Requirement.objects.get(description = "Paper studies confirm basic principles")
        project_requirement_completion = ProjectRequirementCompletion.objects.get(project = project)
        self.assertEqual(project_requirement_completion.project, project)
        self.assertEqual(project_requirement_completion.requirement, requirement)
        self.assertEqual(project_requirement_completion.percentage, 89)
        self.assertEqual(project_requirement_completion.comment, "Some comment")

class ProjectLevelCompletionTest(TestCase):
    def setUp(self):
        john = get_user_model().objects.create(guid = "2546875d", full_name = "John Doe")
        both_technology = Technology.objects.create(technology = "both")
        trl_category = Category.objects.create(category = "trl")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")
        
        project_1 = Project.objects.create(name = "Project 1",
                                technology = both_technology,
                                level = level_1,
                                level_semi = level_2,
                                owner = john,)
        project_1.categories.add(trl_category)
        ProjectLevelCompletion.objects.create(project = project_1,
                                                level = level_1,
                                                percentage = 100,)

    def test_project_level_completion(self):
        project = Project.objects.get(name = "Project 1")
        project_level_completion = ProjectLevelCompletion.objects.get(project = project)
        self.assertEqual(project_level_completion.project, project)
        self.assertEqual(project_level_completion.level.number, 1)
        self.assertEqual(project_level_completion.percentage, 100)
