from django.urls import path
from . import views

urlpatterns = [
    path('ai-chat/', views.ai_chat, name='ai-chat'),
]