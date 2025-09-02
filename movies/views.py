from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Movie, Genre
from .serializers import MovieListSerializer, MovieDetailSerializer, GenreSerializer


class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.filter(is_active=True)
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_fields = ['genres', 'release_date']
    search_fields = ['title', 'description']
    ordering_fields = ['release_date', 'rating', 'title']
    ordering = ['-release_date']


class MovieDetailView(generics.RetrieveAPIView):
    queryset = Movie.objects.filter(is_active=True)
    serializer_class = MovieDetailSerializer
    permission_classes = [AllowAny]
