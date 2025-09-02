from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi
from .models import Movie, Genre


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