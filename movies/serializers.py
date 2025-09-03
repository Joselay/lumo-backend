from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi
from .models import Movie, Genre, Showtime, Theater, SeatLayout, Seat, SeatReservation


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


class SeatSerializer(serializers.ModelSerializer):
    """
    Serializer for individual seats.
    
    Provides seat information including position and type.
    """
    
    seat_identifier = serializers.ReadOnlyField(help_text="Seat identifier like \"A12\"")
    seat_type_display = serializers.CharField(source="get_seat_type_display", read_only=True)
    
    class Meta:
        model = Seat
        fields = [
            "id", "row", "number", "seat_identifier", "seat_type", "seat_type_display",
            "price_multiplier", "is_active"
        ]


class SeatLayoutSerializer(serializers.ModelSerializer):
    """
    Serializer for seat layout configuration.
    
    Provides theater screen layout with seat arrangement.
    """
    
    theater_name = serializers.CharField(source="theater.name", read_only=True)
    seat_count = serializers.SerializerMethodField(help_text="Number of seats in this layout")
    seat_map = serializers.SerializerMethodField(help_text="Visual seat map representation")
    
    class Meta:
        model = SeatLayout
        fields = [
            "id", "theater", "theater_name", "screen_number", "name",
            "total_rows", "total_seats", "row_configuration",
            "seat_count", "seat_map", "is_active"
        ]
    
    def get_seat_count(self, obj):
        """Get the actual number of seats in the database."""
        return obj.seats.filter(is_active=True).count()
    
    def get_seat_map(self, obj):
        """Get the visual seat map."""
        return obj.get_seat_map()


class SeatReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for seat reservations.
    
    Tracks which seats are reserved for specific showtimes.
    """
    
    seat_identifier = serializers.CharField(source="seat.seat_identifier", read_only=True)
    seat_type = serializers.CharField(source="seat.seat_type", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_expired = serializers.ReadOnlyField(help_text="Whether the reservation has expired")
    
    class Meta:
        model = SeatReservation
        fields = [
            "id", "seat", "seat_identifier", "seat_type", "status", "status_display",
            "reserved_at", "confirmed_at", "expires_at", "is_expired"
        ]


class ShowtimeSeatMapSerializer(serializers.ModelSerializer):
    """
    Serializer for showtime with seat availability map.
    
    Provides showtime information with real-time seat availability.
    """
    
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    theater_name = serializers.CharField(source="theater.name", read_only=True)
    seat_map = serializers.SerializerMethodField(help_text="Seat availability map")
    has_seat_selection = serializers.SerializerMethodField(help_text="Whether this showtime supports seat selection")
    
    class Meta:
        model = Showtime
        fields = [
            "id", "movie_title", "theater_name", "datetime", "screen_number",
            "ticket_price", "total_seats", "available_seats",
            "has_seat_selection", "seat_map"
        ]
    
    def get_has_seat_selection(self, obj):
        """Check if this showtime has seat selection enabled."""
        return obj.seat_layout is not None
    
    def get_seat_map(self, obj):
        """Get the seat availability map for this showtime."""
        return obj.get_available_seats_map()


class SeatReservationRequestSerializer(serializers.Serializer):
    """
    Serializer for seat reservation requests.
    
    Handles seat selection during booking process.
    """
    
    seat_ids = serializers.ListField(
        child=serializers.CharField(max_length=10),
        help_text="List of seat identifiers to reserve (e.g., [\"A12\", \"A13\"])"
    )
    expiry_minutes = serializers.IntegerField(
        default=15,
        min_value=5,
        max_value=60,
        help_text="Minutes until reservation expires"
    )
    
    def validate_seat_ids(self, value):
        """Validate seat identifiers format."""
        if not value:
            raise serializers.ValidationError("At least one seat must be selected.")
        
        # Validate seat ID format (e.g., \"A12\", \"B5\")
        import re
        pattern = r"^[A-Z]\d+$"
        for seat_id in value:
            if not re.match(pattern, seat_id):
                raise serializers.ValidationError(f"Invalid seat ID format: {seat_id}")
        
        return value

