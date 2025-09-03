from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi
from .models import Movie, Genre, Showtime, Theater


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for movie genres.
    
    Provides basic genre information including ID and name.
    """
    
    class Meta:
        model = Genre
        fields = ['id', 'name']
        
    def to_representation(self, instance):
        """
        Override to add swagger documentation examples.
        """
        return super().to_representation(instance)


class TheaterSerializer(serializers.ModelSerializer):
    """
    Serializer for movie theaters/cinemas.
    
    Provides theater information including location and amenities.
    """
    
    full_address = serializers.ReadOnlyField(help_text="Complete formatted address")
    
    class Meta:
        model = Theater
        fields = [
            'id', 'name', 'address', 'city', 'state', 'zip_code', 'full_address',
            'phone_number', 'email', 'total_screens', 'parking_available',
            'accessibility_features', 'amenities', 'is_active'
        ]


class TheaterDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual theater views.
    
    Includes complete theater information with timestamps.
    """
    
    full_address = serializers.ReadOnlyField(help_text="Complete formatted address")
    active_showtimes_count = serializers.SerializerMethodField(help_text="Number of active showtimes")
    
    class Meta:
        model = Theater
        fields = [
            'id', 'name', 'address', 'city', 'state', 'zip_code', 'full_address',
            'phone_number', 'email', 'total_screens', 'parking_available',
            'accessibility_features', 'amenities', 'is_active',
            'active_showtimes_count', 'created_at', 'updated_at'
        ]
    
    def get_active_showtimes_count(self, obj):
        """Get count of active showtimes for this theater."""
        from django.utils import timezone
        return obj.showtimes.filter(
            is_active=True,
            datetime__gt=timezone.now()
        ).count()


class MovieListSerializer(serializers.ModelSerializer):
    """
    Serializer for movie listing view.
    
    Provides essential movie information for display in movie lists.
    Includes basic details and associated genres.
    """
    
    genres = GenreSerializer(many=True, read_only=True, help_text="List of genres associated with the movie")
    duration = serializers.IntegerField(help_text="Movie duration in minutes")
    rating = serializers.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        allow_null=True,
        help_text="Movie rating from 0.0 to 10.0"
    )
    poster_image = serializers.URLField(
        allow_null=True, 
        allow_blank=True,
        help_text="URL to movie poster image"
    )
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'description', 'duration', 'release_date',
            'rating', 'poster_image', 'genres'
        ]
        
    def to_representation(self, instance):
        """
        Customize the output representation.
        """
        data = super().to_representation(instance)
        # Format duration for better readability
        if data['duration']:
            hours, minutes = divmod(data['duration'], 60)
            data['duration_formatted'] = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return data


class ShowtimeSerializer(serializers.ModelSerializer):
    """
    Serializer for movie showtimes.
    
    Provides showtime information including movie details, scheduling,
    theater information, and availability status.
    """
    
    movie_title = serializers.CharField(source='movie.title', read_only=True, help_text="Title of the movie")
    movie_duration = serializers.IntegerField(source='movie.duration', read_only=True, help_text="Movie duration in minutes")
    movie_poster = serializers.URLField(source='movie.poster_image', read_only=True, help_text="Movie poster image URL")
    theater_name = serializers.CharField(source='theater.name', read_only=True, help_text="Theater name")
    theater_city = serializers.CharField(source='theater.city', read_only=True, help_text="Theater city")
    is_available = serializers.ReadOnlyField(help_text="Whether the showtime is available for booking")
    seats_sold = serializers.ReadOnlyField(help_text="Number of seats already sold")
    ticket_price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Ticket price in dollars"
    )
    
    class Meta:
        model = Showtime
        fields = [
            'id', 'movie', 'movie_title', 'movie_duration', 'movie_poster',
            'theater', 'theater_name', 'theater_city', 'datetime', 'screen_number', 
            'total_seats', 'available_seats', 'seats_sold', 'ticket_price', 'is_available'
        ]
        
    def to_representation(self, instance):
        """
        Customize the output representation.
        """
        data = super().to_representation(instance)
        # Format the datetime for better readability
        if data['datetime']:
            from datetime import datetime
            dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            data['date'] = dt.strftime('%Y-%m-%d')
            data['time'] = dt.strftime('%H:%M')
            data['datetime_formatted'] = dt.strftime('%B %d, %Y at %I:%M %p')
        return data


class ShowtimeDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual showtime views.
    
    Includes complete movie information along with showtime details.
    """
    
    movie = MovieListSerializer(read_only=True)
    theater = TheaterSerializer(read_only=True)
    is_available = serializers.ReadOnlyField(help_text="Whether the showtime is available for booking")
    seats_sold = serializers.ReadOnlyField(help_text="Number of seats already sold")
    ticket_price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Ticket price in dollars"
    )
    
    class Meta:
        model = Showtime
        fields = [
            'id', 'movie', 'theater', 'datetime', 'screen_number',
            'total_seats', 'available_seats', 'seats_sold', 'ticket_price',
            'is_available', 'created_at', 'updated_at'
        ]
        
    def to_representation(self, instance):
        """
        Customize the output representation.
        """
        data = super().to_representation(instance)
        # Format the datetime for better readability
        if data['datetime']:
            from datetime import datetime
            dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            data['date'] = dt.strftime('%Y-%m-%d')
            data['time'] = dt.strftime('%H:%M')
            data['datetime_formatted'] = dt.strftime('%B %d, %Y at %I:%M %p')
        return data


class MovieDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed movie view.
    
    Provides complete movie information including trailer URL 
    and timestamp information for individual movie details.
    """
    
    genres = GenreSerializer(many=True, read_only=True, help_text="List of genres associated with the movie")
    duration = serializers.IntegerField(help_text="Movie duration in minutes")
    rating = serializers.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        allow_null=True,
        help_text="Movie rating from 0.0 to 10.0"
    )
    poster_image = serializers.URLField(
        allow_null=True, 
        allow_blank=True,
        help_text="URL to movie poster image"
    )
    trailer_url = serializers.URLField(
        allow_null=True, 
        allow_blank=True,
        help_text="URL to movie trailer video"
    )
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'description', 'duration', 'release_date',
            'rating', 'poster_image', 'trailer_url', 'genres',
            'created_at', 'updated_at'
        ]
        
    def to_representation(self, instance):
        """
        Customize the output representation.
        """
        data = super().to_representation(instance)
        # Format duration for better readability
        if data['duration']:
            hours, minutes = divmod(data['duration'], 60)
            data['duration_formatted'] = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return data