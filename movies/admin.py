from django.contrib import admin
from django.utils.html import format_html
from .models import Movie, Genre, Showtime, Theater


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


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    """Admin interface for Theater model."""
    list_display = ['name', 'city', 'state', 'total_screens', 'parking_badge', 'active_showtimes_count', 'is_active']
    list_filter = ['is_active', 'state', 'city', 'parking_available', 'total_screens']
    search_fields = ['name', 'city', 'address', 'phone_number']
    readonly_fields = ['id', 'active_showtimes_count', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Theater Information', {
            'fields': ('name', 'total_screens', 'is_active')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email')
        }),
        ('Amenities & Features', {
            'fields': ('parking_available', 'accessibility_features', 'amenities')
        }),
        ('System Information', {
            'fields': ('id', 'active_showtimes_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def parking_badge(self, obj):
        """Display parking availability with colored badge."""
        if obj.parking_available:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Available</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Not Available</span>'
            )
    parking_badge.short_description = 'Parking'
    
    def active_showtimes_count(self, obj):
        """Display count of active showtimes."""
        from django.utils import timezone
        count = obj.showtimes.filter(
            is_active=True,
            datetime__gt=timezone.now()
        ).count()
        return count
    active_showtimes_count.short_description = 'Active Showtimes'


@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ['movie', 'datetime', 'theater_info', 'screen_number', 'available_seats', 'ticket_price', 'is_active']
    list_filter = ['is_active', 'theater__name', 'theater__city', 'screen_number', 'datetime']
    search_fields = ['movie__title', 'theater__name', 'theater__city']
    readonly_fields = ['created_at', 'updated_at', 'seats_sold', 'is_available']
    list_editable = ['is_active', 'available_seats', 'ticket_price']
    date_hierarchy = 'datetime'
    
    fieldsets = (
        ('Showtime Information', {
            'fields': ('movie', 'theater', 'datetime', 'screen_number', 'is_active')
        }),
        ('Seating & Pricing', {
            'fields': ('total_seats', 'available_seats', 'ticket_price')
        }),
        ('System Information', {
            'fields': ('seats_sold', 'is_available', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('movie', 'theater')
    
    def theater_info(self, obj):
        """Display theater name and city."""
        return f"{obj.theater.name} - {obj.theater.city}"
    theater_info.short_description = 'Theater'
