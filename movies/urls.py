from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('', views.MovieListView.as_view(), name='movie-list'),
    path('<int:pk>/', views.MovieDetailView.as_view(), name='movie-detail'),
]