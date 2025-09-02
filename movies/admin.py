from django.contrib import admin
from .models import Movie, Genre, Showtime


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


@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ['movie', 'datetime', 'theater_name', 'screen_number', 'available_seats', 'ticket_price', 'is_active']
    list_filter = ['is_active', 'theater_name', 'screen_number', 'datetime']
    search_fields = ['movie__title', 'theater_name']
    readonly_fields = ['created_at', 'updated_at', 'seats_sold', 'is_available']
    list_editable = ['is_active', 'available_seats', 'ticket_price']
    date_hierarchy = 'datetime'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('movie')
