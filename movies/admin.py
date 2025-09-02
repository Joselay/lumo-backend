from django.contrib import admin
from .models import Movie, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_date', 'duration', 'rating', 'is_active']
    list_filter = ['is_active', 'release_date', 'genres']
    search_fields = ['title', 'description']
    filter_horizontal = ['genres']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
