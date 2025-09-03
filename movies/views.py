from rest_framework import generics, filters, status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, Showtime, Theater, SeatLayout, Seat, SeatReservation
from .serializers import (
    MovieListSerializer, MovieDetailSerializer, GenreSerializer, ShowtimeSerializer, 
    ShowtimeDetailSerializer, TheaterSerializer, TheaterDetailSerializer,
    SeatLayoutSerializer, SeatSerializer, SeatReservationSerializer, 
    ShowtimeSeatMapSerializer, SeatReservationRequestSerializer
)


class GenreListView(generics.ListAPIView):
    """
    API endpoint to retrieve all movie genres.
    
    Returns a list of all available genres that can be used to filter movies.
    This endpoint is useful for populating genre filters in the frontend.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="List all movie genres",
        operation_description="""
        Retrieve a complete list of movie genres available in the system.
        
        **Use Cases:**
        - Populate genre filter dropdowns
        - Display available genre options
        - Build movie category navigation
        
        **Response:**
        Returns a paginated list of genres with ID and name fields.
        """,
        responses={
            200: openapi.Response(
                description="List of genres retrieved successfully",
                schema=GenreSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 5,
                        "next": None,
                        "previous": None,
                        "results": [
                            {"id": 1, "name": "Action"},
                            {"id": 2, "name": "Comedy"},
                            {"id": 3, "name": "Drama"},
                            {"id": 4, "name": "Horror"},
                            {"id": 5, "name": "Sci-Fi"}
                        ]
                    }
                }
            )
        },
        tags=['Genres']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MovieListView(generics.ListAPIView):
    """
    API endpoint to retrieve a list of active movies.
    
    Supports filtering, searching, and ordering of movies.
    All movies returned are active (is_active=True) and available for booking.
    """
    queryset = Movie.objects.filter(is_active=True)
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genres', 'release_date']
    search_fields = ['title', 'description']
    ordering_fields = ['release_date', 'rating', 'title']
    ordering = ['-release_date']
    
    @swagger_auto_schema(
        operation_summary="List active movies",
        operation_description="""
        Retrieve a paginated list of active movies available for booking.
        
        **Features:**
        - **Filtering:** Filter by genres and release date
        - **Search:** Search in movie title and description
        - **Ordering:** Sort by release date, rating, or title
        - **Pagination:** Results are paginated (20 per page)
        
        **Query Parameters:**
        - `genres`: Filter by genre ID (can be used multiple times)
        - `release_date`: Filter by exact release date (YYYY-MM-DD)
        - `search`: Search in title and description
        - `ordering`: Sort results (`release_date`, `-release_date`, `rating`, `-rating`, `title`, `-title`)
        - `page`: Page number for pagination
        
        **Examples:**
        - `/api/v1/movies/?genres=1&genres=3` - Movies with Action OR Drama genres
        - `/api/v1/movies/?search=marvel` - Search for "marvel" in title/description
        - `/api/v1/movies/?ordering=-rating` - Sort by highest rating first
        - `/api/v1/movies/?release_date=2024-01-15` - Movies released on specific date
        """,
        manual_parameters=[
            openapi.Parameter(
                'genres',
                openapi.IN_QUERY,
                description="Filter by genre ID (multiple values allowed)",
                type=openapi.TYPE_INTEGER,
                collectionFormat='multi'
            ),
            openapi.Parameter(
                'release_date',
                openapi.IN_QUERY,
                description="Filter by release date (YYYY-MM-DD format)",
                type=openapi.TYPE_STRING,
                format='date'
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in movie title and description",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results by field (prefix with '-' for descending)",
                type=openapi.TYPE_STRING,
                enum=['release_date', '-release_date', 'rating', '-rating', 'title', '-title']
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Movies retrieved successfully",
                schema=MovieListSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 25,
                        "next": "http://localhost:8000/api/v1/movies/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 1,
                                "title": "Avengers: Endgame",
                                "description": "The epic conclusion to the Infinity Saga...",
                                "duration": 181,
                                "duration_formatted": "3h 1m",
                                "release_date": "2024-04-26",
                                "rating": "8.4",
                                "poster_image": "https://example.com/posters/avengers-endgame.jpg",
                                "genres": [
                                    {"id": 1, "name": "Action"},
                                    {"id": 5, "name": "Sci-Fi"}
                                ]
                            }
                        ]
                    }
                }
            )
        },
        tags=['Movies']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MovieDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve detailed information about a specific movie.
    
    Returns comprehensive movie details including trailer URL and timestamps.
    """
    queryset = Movie.objects.filter(is_active=True)
    serializer_class = MovieDetailSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get movie details",
        operation_description="""
        Retrieve detailed information about a specific movie by its ID.
        
        **Use Cases:**
        - Display full movie information on movie detail pages
        - Show movie details before booking
        - Access trailer and additional movie metadata
        
        **Response:**
        Returns complete movie details including trailer URL, creation timestamps,
        and formatted duration information.
        """,
        responses={
            200: openapi.Response(
                description="Movie details retrieved successfully",
                schema=MovieDetailSerializer(),
                examples={
                    "application/json": {
                        "id": 1,
                        "title": "Avengers: Endgame",
                        "description": "The epic conclusion to the Infinity Saga that will forever change the Marvel Cinematic Universe...",
                        "duration": 181,
                        "duration_formatted": "3h 1m",
                        "release_date": "2024-04-26",
                        "rating": "8.4",
                        "poster_image": "https://example.com/posters/avengers-endgame.jpg",
                        "trailer_url": "https://youtube.com/watch?v=TcMBFSGVi1c",
                        "genres": [
                            {"id": 1, "name": "Action"},
                            {"id": 5, "name": "Sci-Fi"}
                        ],
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T14:45:00Z"
                    }
                }
            ),
            404: openapi.Response(
                description="Movie not found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            )
        },
        tags=['Movies']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ShowtimeListView(generics.ListAPIView):
    """
    API endpoint to retrieve a list of available showtimes.
    
    Supports filtering by movie, date, theater, and availability.
    Returns only active showtimes for active movies.
    """
    queryset = Showtime.objects.filter(is_active=True, movie__is_active=True)
    serializer_class = ShowtimeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['movie', 'theater', 'screen_number']
    ordering_fields = ['datetime', 'ticket_price', 'available_seats']
    ordering = ['datetime']
    
    @swagger_auto_schema(
        operation_summary="List available showtimes",
        operation_description="""
        Retrieve a paginated list of available showtimes for booking.
        
        **Features:**
        - **Filtering:** Filter by movie, date, theater, and screen
        - **Ordering:** Sort by datetime, price, or available seats
        - **Availability:** Only shows active showtimes with available seats
        - **Pagination:** Results are paginated (20 per page)
        
        **Query Parameters:**
        - `movie`: Filter by movie ID
        - `datetime__date`: Filter by specific date (YYYY-MM-DD)
        - `theater_name`: Filter by theater name
        - `screen_number`: Filter by screen number
        - `ordering`: Sort results (`datetime`, `-datetime`, `ticket_price`, `-ticket_price`, `available_seats`, `-available_seats`)
        - `page`: Page number for pagination
        
        **Examples:**
        - `/api/v1/showtimes/?movie=123` - All showtimes for a specific movie
        - `/api/v1/showtimes/?datetime__date=2024-12-25` - All showtimes on Christmas
        - `/api/v1/showtimes/?theater_name=Main Theater&screen_number=1` - Specific theater and screen
        - `/api/v1/showtimes/?ordering=ticket_price` - Sort by lowest price first
        """,
        tags=['Showtimes']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ShowtimeDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve detailed information about a specific showtime.
    
    Returns comprehensive showtime details including complete movie information.
    """
    queryset = Showtime.objects.filter(is_active=True, movie__is_active=True)
    serializer_class = ShowtimeDetailSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get showtime details",
        operation_description="""
        Retrieve detailed information about a specific showtime by its ID.
        
        **Use Cases:**
        - Display full showtime information before booking
        - Show movie and theater details together
        - Access pricing and availability information
        
        **Response:**
        Returns complete showtime details including full movie information,
        theater details, pricing, and availability status.
        """,
        tags=['Showtimes']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MovieShowtimesView(generics.ListAPIView):
    """
    API endpoint to retrieve all showtimes for a specific movie.
    
    Returns available showtimes for a given movie, ordered by datetime.
    """
    serializer_class = ShowtimeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['theater', 'screen_number']
    ordering_fields = ['datetime', 'ticket_price', 'available_seats']
    ordering = ['datetime']
    
    def get_queryset(self):
        movie_id = self.kwargs['movie_id']
        return Showtime.objects.filter(
            movie_id=movie_id,
            is_active=True,
            movie__is_active=True
        )
    
    @swagger_auto_schema(
        operation_summary="List showtimes for a specific movie",
        operation_description="""
        Retrieve all available showtimes for a specific movie.
        
        **Features:**
        - **Filtering:** Filter by date, theater, and screen
        - **Ordering:** Sort by datetime, price, or available seats
        - **Movie-specific:** Only shows showtimes for the specified movie
        - **Pagination:** Results are paginated (20 per page)
        
        **Query Parameters:**
        - `datetime__date`: Filter by specific date (YYYY-MM-DD)
        - `theater_name`: Filter by theater name
        - `screen_number`: Filter by screen number
        - `ordering`: Sort results (`datetime`, `-datetime`, `ticket_price`, `-ticket_price`, `available_seats`, `-available_seats`)
        - `page`: Page number for pagination
        
        **Examples:**
        - `/api/v1/movies/123/showtimes/` - All showtimes for movie 123
        - `/api/v1/movies/123/showtimes/?datetime__date=2024-12-25` - Movie showtimes on Christmas
        - `/api/v1/movies/123/showtimes/?ordering=ticket_price` - Sort by price
        """,
        tags=['Movies', 'Showtimes']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TheaterListView(generics.ListAPIView):
    """
    API endpoint to retrieve a list of theaters.
    
    Returns all active theaters with location and amenity information.
    """
    queryset = Theater.objects.filter(is_active=True)
    serializer_class = TheaterSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'parking_available']
    search_fields = ['name', 'city', 'address']
    ordering_fields = ['name', 'city', 'total_screens']
    ordering = ['name']
    
    @swagger_auto_schema(
        operation_summary="List theaters",
        operation_description="""
        Retrieve a paginated list of active theater locations.
        
        **Features:**
        - **Filtering:** Filter by city, state, and parking availability
        - **Search:** Search in theater name, city, and address
        - **Ordering:** Sort by name, city, or number of screens
        - **Pagination:** Results are paginated (20 per page)
        
        **Query Parameters:**
        - `city`: Filter by city name
        - `state`: Filter by state
        - `parking_available`: Filter by parking availability (true/false)
        - `search`: Search in name, city, and address
        - `ordering`: Sort results (`name`, `-name`, `city`, `-city`, `total_screens`, `-total_screens`)
        - `page`: Page number for pagination
        
        **Examples:**
        - `/api/v1/theaters/?city=Los Angeles` - Theaters in Los Angeles
        - `/api/v1/theaters/?parking_available=true` - Theaters with parking
        - `/api/v1/theaters/?search=cinemark` - Search for Cinemark theaters
        - `/api/v1/theaters/?ordering=-total_screens` - Sort by most screens first
        """,
        manual_parameters=[
            openapi.Parameter(
                'city',
                openapi.IN_QUERY,
                description="Filter by city name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'state',
                openapi.IN_QUERY,
                description="Filter by state",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'parking_available',
                openapi.IN_QUERY,
                description="Filter by parking availability",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in theater name, city, and address",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order results by field",
                type=openapi.TYPE_STRING,
                enum=['name', '-name', 'city', '-city', 'total_screens', '-total_screens']
            )
        ],
        responses={
            200: openapi.Response(
                description="Theaters retrieved successfully",
                schema=TheaterSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 15,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": "uuid-here",
                                "name": "Lumo Cinema Downtown",
                                "address": "123 Main Street",
                                "city": "Los Angeles",
                                "state": "CA",
                                "zip_code": "90210",
                                "full_address": "123 Main Street, Los Angeles, CA 90210",
                                "phone_number": "+1-555-0123",
                                "email": "downtown@lumocinema.com",
                                "total_screens": 8,
                                "parking_available": True,
                                "accessibility_features": "Wheelchair accessible, Audio description available",
                                "amenities": "IMAX, Dolby Atmos, Concession stand, Bar",
                                "is_active": True
                            }
                        ]
                    }
                }
            )
        },
        tags=['Theaters']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TheaterDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve detailed information about a specific theater.
    
    Returns comprehensive theater details including active showtimes count.
    """
    queryset = Theater.objects.filter(is_active=True)
    serializer_class = TheaterDetailSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get theater details",
        operation_description="""
        Retrieve detailed information about a specific theater by its ID.
        
        **Use Cases:**
        - Display full theater information on theater detail pages
        - Show theater details when booking tickets
        - Access theater amenities and accessibility information
        
        **Response:**
        Returns complete theater details including location, amenities,
        accessibility features, and current active showtimes count.
        """,
        responses={
            200: openapi.Response(
                description="Theater details retrieved successfully",
                schema=TheaterDetailSerializer(),
                examples={
                    "application/json": {
                        "id": "uuid-here",
                        "name": "Lumo Cinema Downtown",
                        "address": "123 Main Street",
                        "city": "Los Angeles",
                        "state": "CA",
                        "zip_code": "90210",
                        "full_address": "123 Main Street, Los Angeles, CA 90210",
                        "phone_number": "+1-555-0123",
                        "email": "downtown@lumocinema.com",
                        "total_screens": 8,
                        "parking_available": True,
                        "accessibility_features": "Wheelchair accessible, Audio description available",
                        "amenities": "IMAX, Dolby Atmos, Concession stand, Bar",
                        "is_active": True,
                        "active_showtimes_count": 42,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            ),
            404: openapi.Response(
                description="Theater not found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            )
        },
        tags=['Theaters']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ShowtimeSeatMapView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve seat map for a specific showtime.
    
    Returns the visual seat layout with real-time availability.
    """
    queryset = Showtime.objects.filter(is_active=True, movie__is_active=True)
    serializer_class = ShowtimeSeatMapSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get showtime seat map",
        operation_description="""
        Retrieve the seat layout and availability for a specific showtime.
        
        **Use Cases:**
        - Display seat selection interface
        - Show real-time seat availability
        - Calculate pricing for different seat types
        
        **Seat Status:**
        - `is_available: true` - Seat can be selected
        - `is_available: false` - Seat is already reserved/confirmed
        - `is_blocked: true` - Seat is not available (maintenance, etc.)
        
        **Seat Types:**
        - `standard` - Regular seating (price_multiplier: 1.0)
        - `premium` - Premium seating (price_multiplier: 1.5+)
        - `accessible` - Wheelchair accessible
        - `couple` - Couple/love seats
        - `blocked` - Not available for booking
        
        **Response:**
        Returns showtime details with complete seat map showing availability and pricing.
        """,
        responses={
            200: openapi.Response(
                description="Seat map retrieved successfully",
                schema=ShowtimeSeatMapSerializer(),
                examples={
                    "application/json": {
                        "id": "uuid-here",
                        "movie_title": "Avengers: Endgame",
                        "theater_name": "Lumo Cinema Downtown",
                        "datetime": "2024-12-25T19:00:00Z",
                        "screen_number": 1,
                        "ticket_price": "15.99",
                        "total_seats": 120,
                        "available_seats": 85,
                        "has_seat_selection": True,
                        "seat_map": [
                            {
                                "row": "A",
                                "seats": [
                                    {
                                        "seat_id": "A1",
                                        "seat_type": "premium",
                                        "price_multiplier": 1.5,
                                        "is_available": True,
                                        "is_blocked": False
                                    },
                                    {
                                        "seat_id": "A2",
                                        "seat_type": "premium",
                                        "price_multiplier": 1.5,
                                        "is_available": False,
                                        "is_blocked": False
                                    }
                                ]
                            }
                        ]
                    }
                }
            ),
            404: openapi.Response(description="Showtime not found"),
            400: openapi.Response(
                description="Seat selection not available for this showtime",
                examples={
                    "application/json": {
                        "error": "This showtime does not support seat selection."
                    }
                }
            )
        },
        tags=['Seat Selection']
    )
    def get(self, request, *args, **kwargs):
        showtime = self.get_object()
        
        # Check if seat selection is available
        if not showtime.seat_layout:
            return Response(
                {'error': 'This showtime does not support seat selection.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().get(request, *args, **kwargs)


class SeatReservationView(generics.CreateAPIView):
    """
    API endpoint to reserve seats for a showtime.
    
    Creates temporary seat reservations during the booking process.
    """
    serializer_class = SeatReservationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Reserve seats for showtime",
        operation_description="""
        Reserve specific seats for a showtime during the booking process.
        
        **Reservation Process:**
        1. Seats are temporarily reserved for the specified duration (default: 15 minutes)
        2. Customer must complete booking before expiry
        3. Expired reservations are automatically released
        4. Confirmed bookings convert temporary reservations to permanent
        
        **Features:**
        - Real-time seat availability checking
        - Automatic expiry management
        - Conflict prevention (no double-booking)
        - Price calculation with seat type multipliers
        
        **Authentication Required**
        """,
        request_body=SeatReservationRequestSerializer,
        responses={
            201: openapi.Response(
                description="Seats reserved successfully",
                examples={
                    "application/json": {
                        "message": "Seats reserved successfully",
                        "reservations": [
                            {
                                "id": "reservation-uuid",
                                "seat_identifier": "A12",
                                "seat_type": "premium",
                                "status": "reserved",
                                "expires_at": "2024-12-25T19:15:00Z",
                                "price": "23.99"
                            }
                        ],
                        "total_price": "47.98",
                        "expires_at": "2024-12-25T19:15:00Z"
                    }
                }
            ),
            400: openapi.Response(
                description="Seat reservation failed",
                examples={
                    "application/json": {
                        "seat_ids": ["Seat A12 is already reserved"],
                        "non_field_errors": ["This showtime does not support seat selection"]
                    }
                }
            ),
            404: openapi.Response(description="Showtime not found"),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Seat Selection']
    )
    def create(self, request, *args, **kwargs):
        showtime_id = kwargs.get('showtime_id')
        
        try:
            showtime = Showtime.objects.get(
                id=showtime_id,
                is_active=True,
                movie__is_active=True
            )
        except Showtime.DoesNotExist:
            return Response(
                {'error': 'Showtime not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if seat selection is available
        if not showtime.seat_layout:
            return Response(
                {'error': 'This showtime does not support seat selection.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        seat_ids = serializer.validated_data['seat_ids']
        expiry_minutes = serializer.validated_data['expiry_minutes']
        
        try:
            # Reserve the seats
            reservations = showtime.reserve_seats(
                seat_ids=seat_ids,
                customer=request.user,
                expiry_minutes=expiry_minutes
            )
            
            # Calculate total price
            total_price = 0
            reservation_data = []
            
            for reservation in reservations:
                seat_price = showtime.calculate_seat_price(reservation.seat)
                total_price += seat_price
                
                reservation_data.append({
                    'id': str(reservation.id),
                    'seat_identifier': reservation.seat.seat_identifier,
                    'seat_type': reservation.seat.seat_type,
                    'status': reservation.status,
                    'expires_at': reservation.expires_at,
                    'price': str(seat_price)
                })
            
            return Response({
                'message': 'Seats reserved successfully',
                'reservations': reservation_data,
                'total_price': str(total_price),
                'expires_at': reservations[0].expires_at if reservations else None
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SeatLayoutListView(generics.ListAPIView):
    """
    API endpoint to list seat layouts for theaters.
    
    Returns available seat configurations for theater screens.
    """
    queryset = SeatLayout.objects.filter(is_active=True)
    serializer_class = SeatLayoutSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['theater', 'screen_number']
    
    @swagger_auto_schema(
        operation_summary="List seat layouts",
        operation_description="""
        Retrieve seat layout configurations for theater screens.
        
        **Use Cases:**
        - Display available theater configurations
        - Setup seat selection for showtimes
        - Understand theater capacity and layout
        
        **Filtering:**
        - Filter by theater ID
        - Filter by screen number
        
        **Response:**
        Returns list of seat layouts with configuration details and visual maps.
        """,
        responses={
            200: openapi.Response(
                description="Seat layouts retrieved successfully",
                schema=SeatLayoutSerializer(many=True)
            )
        },
        tags=['Seat Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)