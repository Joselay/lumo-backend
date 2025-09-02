from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('', views.MovieListView.as_view(), name='movie-list'),
    path('<uuid:pk>/', views.MovieDetailView.as_view(), name='movie-detail'),
    path('<uuid:movie_id>/showtimes/', views.MovieShowtimesView.as_view(), name='movie-showtimes'),
    path('showtimes/', views.ShowtimeListView.as_view(), name='showtime-list'),
    path('showtimes/<uuid:pk>/', views.ShowtimeDetailView.as_view(), name='showtime-detail'),
]