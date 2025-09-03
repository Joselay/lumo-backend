from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile management endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('customer-profile/', views.CustomerProfileView.as_view(), name='customer-profile'),
]