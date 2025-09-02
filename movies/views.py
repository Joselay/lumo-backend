from rest_framework import generics, filters, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, Showtime
from .serializers import MovieListSerializer, MovieDetailSerializer, GenreSerializer, ShowtimeSerializer, ShowtimeDetailSerializer


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
    filterset_fields = ['movie', 'theater_name', 'screen_number']
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
    filterset_fields = ['theater_name', 'screen_number']
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