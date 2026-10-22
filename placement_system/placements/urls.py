
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),

    
    path('add-student/', views.add_student, name='add_student'),
    path('students/', views.view_students, name='view_students'),

  
    path('companies/', views.view_companies, name='view_companies'),

    
    path('register/', views.register, name='register'),
    path('student-login/', views.student_login, name='student_login'),
    path('student-home/', views.student_home, name='student_home'),
    path('student-logout/', views.student_logout, name='student_logout'),

    path('apply/<int:company_id>/', views.apply_job, name='apply_job'),
    path('my-applications/', views.my_applications, name='my_applications'),

  
    path('dashboard/', views.student_dashboard, name='student_dashboard'),

   
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('profile/', views.student_profile, name='student_profile'),
]