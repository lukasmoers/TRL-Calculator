from django.urls import path
from trl import views

app_name = 'trl'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.local_register, name='register'),
    path('login/', views.local_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('about/', views.about, name='about'),
    path('how_to_use/', views.tutorial, name='tutorial'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('new_project/settings/', views.new_project_details, name='new_project_details'),
    path('project_<int:project_id>/settings/', views.update_project_details, name='update_project_details'),
    path('project_<int:project_id>/level_<int:level_no>/', views.project_level_requirements, name='project_level_requirements'),
    path('project_<int:project_id>/level_<int:level_no>/update', views.project_level_update, name='project_level_update'),
    path('project_<int:project_id>/report/', views.project_overview, name='project_overview'),
    path('project_<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project_<int:project_id>/pdf_report/', views.pdf_generator, name='pdf_generator'),
]