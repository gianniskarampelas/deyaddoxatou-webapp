from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. Η αρχική σελίδα (Dashboard)
    path('', views.dashboard, name='dashboard'),
    
    # 2. Η σελίδα για τη Νέα Αίτηση (Γραμματεία)
    path('new/', views.create_application, name='create_application'), 
    
    # 3. Η διαδρομή για το Login
    path('login/', auth_views.LoginView.as_view(template_name='applications/login.html'), name='login'),
    
    # 4. Η διαδρομή για το Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('application/<int:pk>/', views.application_detail, name='application_detail'),
]