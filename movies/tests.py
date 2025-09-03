import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import Movie, Genre, Showtime, Theater, SeatLayout, Seat, SeatReservation
from .serializers import (
    MovieListSerializer, MovieDetailSerializer, 
    GenreSerializer, ShowtimeSerializer, ShowtimeDetailSerializer,
    TheaterSerializer, TheaterDetailSerializer, SeatSerializer,
    SeatLayoutSerializer, SeatReservationSerializer, ShowtimeSeatMapSerializer,
    SeatReservationRequestSerializer
)


class GenreModelTest(TestCase):
    """Test cases for the Genre model."""
    
    def setUp(self):
        self.genre = Genre.objects.create(name="Action")
    
    def test_genre_creation(self):
        """Test basic genre creation."""
        self.assertEqual(self.genre.name, "Action")
        self.assertIsInstance(self.genre.id, uuid.UUID)
        self.assertIsNotNone(self.genre.created_at)
        self.assertIsNotNone(self.genre.updated_at)
    
    def test_genre_str_method(self):
        """Test the string representation of Genre."""
        self.assertEqual(str(self.genre), "Action")
    
    def test_genre_unique_constraint(self):
        """Test that genre names must be unique."""
        with self.assertRaises(Exception):
            Genre.objects.create(name="Action")
    
    def test_genre_ordering(self):
        """Test that genres are ordered by name."""
        Genre.objects.create(name="Comedy")
        Genre.objects.create(name="Drama")
        
        genres = list(Genre.objects.all())
        genre_names = [g.name for g in genres]
        self.assertEqual(genre_names, ["Action", "Comedy", "Drama"])


class MovieModelTest(TestCase):
    """Test cases for the Movie model."""
    
    def setUp(self):
        self.genre1 = Genre.objects.create(name="Action")
        self.genre2 = Genre.objects.create(name="Sci-Fi")
        
        self.movie = Movie.objects.create(
            title="Avengers: Endgame",
            description="The epic conclusion to the Infinity Saga.",
            duration=181,
            release_date=date(2024, 4, 26),
            rating=Decimal('8.4'),
            poster_image="https://example.com/poster.jpg",
            trailer_url="https://youtube.com/watch?v=abc123",
            is_active=True
        )
        self.movie.genres.set([self.genre1, self.genre2])
    
    def test_movie_creation(self):
        """Test basic movie creation."""
        self.assertEqual(self.movie.title, "Avengers: Endgame")
        self.assertEqual(self.movie.duration, 181)
        self.assertEqual(self.movie.rating, Decimal('8.4'))
        self.assertTrue(self.movie.is_active)
        self.assertIsInstance(self.movie.id, uuid.UUID)
        
    def test_movie_str_method(self):
        """Test the string representation of Movie."""
        self.assertEqual(str(self.movie), "Avengers: Endgame")
    
    def test_movie_genres_relationship(self):
        """Test the many-to-many relationship with genres."""
        self.assertEqual(self.movie.genres.count(), 2)
        self.assertIn(self.genre1, self.movie.genres.all())
        self.assertIn(self.genre2, self.movie.genres.all())
    
    def test_movie_rating_validation(self):
        """Test rating validation constraints."""
        # Test valid rating
        movie = Movie(
            title="Test Movie",
            description="Test description",
            duration=120,
            release_date=date.today(),
            rating=Decimal('5.5')
        )
        movie.full_clean()  # This should not raise an exception
        
        # Test invalid rating (too high)
        movie.rating = Decimal('11.0')
        with self.assertRaises(ValidationError):
            movie.full_clean()
        
        # Test invalid rating (too low)
        movie.rating = Decimal('-1.0')
        with self.assertRaises(ValidationError):
            movie.full_clean()
    
    def test_movie_ordering(self):
        """Test that movies are ordered by release date (desc) then title."""
        movie2 = Movie.objects.create(
            title="Black Widow",
            description="A Natasha Romanoff story.",
            duration=134,
            release_date=date(2024, 5, 1)
        )
        movie3 = Movie.objects.create(
            title="Captain Marvel",
            description="Carol Danvers becomes one of the universe's most powerful heroes.",
            duration=123,
            release_date=date(2024, 4, 26)  # Same date as Avengers
        )
        
        movies = list(Movie.objects.all())
        # Should be ordered by: Black Widow (latest), then Avengers (A comes before C)
        expected_order = ["Black Widow", "Avengers: Endgame", "Captain Marvel"]
        actual_order = [movie.title for movie in movies]
        self.assertEqual(actual_order, expected_order)


class ShowtimeModelTest(TestCase):
    """Test cases for the Showtime model."""
    
    def setUp(self):
        self.genre = Genre.objects.create(name="Action")
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A test movie.",
            duration=120,
            release_date=date.today()
        )
        
        self.theater = Theater.objects.create(
            name="Showtime Model Test Theater",
            address="123 Main Street",
            city="Los Angeles",
            state="CA",
            zip_code="90210",
            phone_number="+1-555-0123"
        )
        
        # Create a showtime in the future
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time,
            screen_number=1,
            total_seats=100,
            available_seats=80,
            ticket_price=Decimal('15.99'),
            is_active=True
        )
    
    def test_showtime_creation(self):
        """Test basic showtime creation."""
        self.assertEqual(self.showtime.movie, self.movie)
        self.assertEqual(self.showtime.theater.name, "Showtime Model Test Theater")
        self.assertEqual(self.showtime.screen_number, 1)
        self.assertEqual(self.showtime.total_seats, 100)
        self.assertEqual(self.showtime.available_seats, 80)
        self.assertEqual(self.showtime.ticket_price, Decimal('15.99'))
        self.assertTrue(self.showtime.is_active)
    
    def test_showtime_str_method(self):
        """Test the string representation of Showtime."""
        expected = f"Test Movie - {self.showtime.datetime.strftime('%Y-%m-%d %H:%M')} - Showtime Model Test Theater Screen 1"
        self.assertEqual(str(self.showtime), expected)
    
    def test_is_available_property(self):
        """Test the is_available property logic."""
        # Should be available (active, seats available, future time)
        self.assertTrue(self.showtime.is_available)
        
        # Test inactive showtime
        self.showtime.is_active = False
        self.assertFalse(self.showtime.is_available)
        self.showtime.is_active = True
        
        # Test no available seats
        self.showtime.available_seats = 0
        self.assertFalse(self.showtime.is_available)
        self.showtime.available_seats = 80
        
        # Test past datetime
        past_time = timezone.now() - timedelta(hours=1)
        self.showtime.datetime = past_time
        self.assertFalse(self.showtime.is_available)
    
    def test_seats_sold_property(self):
        """Test the seats_sold property calculation."""
        expected_seats_sold = self.showtime.total_seats - self.showtime.available_seats
        self.assertEqual(self.showtime.seats_sold, expected_seats_sold)
        self.assertEqual(self.showtime.seats_sold, 20)
    
    def test_unique_together_constraint(self):
        """Test the unique constraint on theater, screen, and datetime."""
        with self.assertRaises(Exception):
            Showtime.objects.create(
                movie=self.movie,
                datetime=self.showtime.datetime,
                theater=self.theater,
                screen_number=1,  # Same theater, screen, and time
                total_seats=50,
                available_seats=50,
                ticket_price=Decimal('12.99')
            )


class GenreSerializerTest(TestCase):
    """Test cases for GenreSerializer."""
    
    def setUp(self):
        self.genre = Genre.objects.create(name="Horror")
    
    def test_genre_serialization(self):
        """Test genre serialization."""
        serializer = GenreSerializer(self.genre)
        expected_data = {
            'id': str(self.genre.id),
            'name': 'Horror'
        }
        self.assertEqual(serializer.data, expected_data)


class MovieSerializerTest(TestCase):
    """Test cases for Movie serializers."""
    
    def setUp(self):
        self.genre1 = Genre.objects.create(name="Action")
        self.genre2 = Genre.objects.create(name="Adventure")
        
        self.movie = Movie.objects.create(
            title="Indiana Jones",
            description="Adventure archaeologist.",
            duration=115,
            release_date=date(2024, 6, 30),
            rating=Decimal('7.8'),
            poster_image="https://example.com/poster.jpg",
            trailer_url="https://youtube.com/watch?v=xyz789"
        )
        self.movie.genres.set([self.genre1, self.genre2])
    
    def test_movie_list_serialization(self):
        """Test MovieListSerializer output."""
        serializer = MovieListSerializer(self.movie)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Indiana Jones')
        self.assertEqual(data['duration'], 115)
        self.assertEqual(data['duration_formatted'], '1h 55m')
        self.assertEqual(data['rating'], '7.8')
        self.assertEqual(len(data['genres']), 2)
        self.assertNotIn('trailer_url', data)  # trailer_url only in detail serializer
    
    def test_movie_detail_serialization(self):
        """Test MovieDetailSerializer output."""
        serializer = MovieDetailSerializer(self.movie)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Indiana Jones')
        self.assertEqual(data['duration_formatted'], '1h 55m')
        self.assertEqual(data['trailer_url'], 'https://youtube.com/watch?v=xyz789')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_duration_formatting(self):
        """Test duration formatting logic."""
        # Test movie with hours and minutes
        movie_long = Movie.objects.create(
            title="Long Movie",
            description="Very long.",
            duration=143,  # 2h 23m
            release_date=date.today()
        )
        serializer = MovieListSerializer(movie_long)
        self.assertEqual(serializer.data['duration_formatted'], '2h 23m')
        
        # Test movie with only minutes
        movie_short = Movie.objects.create(
            title="Short Movie",
            description="Very short.",
            duration=45,  # 45m
            release_date=date.today()
        )
        serializer = MovieListSerializer(movie_short)
        self.assertEqual(serializer.data['duration_formatted'], '45m')


class ShowtimeSerializerTest(TestCase):
    """Test cases for Showtime serializers."""
    
    def setUp(self):
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A test movie.",
            duration=120,
            release_date=date.today(),
            poster_image="https://example.com/poster.jpg"
        )
        
        self.theater2 = Theater.objects.create(
            name="Grand Theater",
            address="456 Grand Avenue",
            city="New York",
            state="NY",
            zip_code="10001",
            phone_number="+1-555-0456"
        )
        
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            datetime=datetime(2024, 12, 25, 19, 30, tzinfo=timezone.utc),
            theater=self.theater2,
            screen_number=2,
            total_seats=150,
            available_seats=120,
            ticket_price=Decimal('18.50')
        )
    
    def test_showtime_serialization(self):
        """Test ShowtimeSerializer output."""
        serializer = ShowtimeSerializer(self.showtime)
        data = serializer.data
        
        self.assertEqual(data['movie_title'], 'Test Movie')
        self.assertEqual(data['movie_duration'], 120)
        self.assertEqual(data['theater_name'], 'Grand Theater')
        self.assertEqual(data['screen_number'], 2)
        self.assertEqual(data['total_seats'], 150)
        self.assertEqual(data['available_seats'], 120)
        self.assertEqual(data['seats_sold'], 30)
        self.assertEqual(data['ticket_price'], '18.50')
        
        # Test formatted datetime fields
        self.assertEqual(data['date'], '2024-12-25')
        self.assertEqual(data['time'], '19:30')
        self.assertIn('datetime_formatted', data)
    
    def test_showtime_detail_serialization(self):
        """Test ShowtimeDetailSerializer output."""
        serializer = ShowtimeDetailSerializer(self.showtime)
        data = serializer.data
        
        # Should include full movie details
        self.assertIn('movie', data)
        self.assertEqual(data['movie']['title'], 'Test Movie')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)


class MovieAPITest(APITestCase):
    """Test cases for Movie API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test genres
        self.action_genre = Genre.objects.create(name="Action")
        self.comedy_genre = Genre.objects.create(name="Comedy")
        
        # Create test movies
        self.active_movie = Movie.objects.create(
            title="Active Movie",
            description="An active test movie.",
            duration=120,
            release_date=date(2024, 6, 15),
            rating=Decimal('8.0'),
            is_active=True
        )
        self.active_movie.genres.set([self.action_genre])
        
        self.inactive_movie = Movie.objects.create(
            title="Inactive Movie",
            description="An inactive test movie.",
            duration=90,
            release_date=date(2024, 5, 10),
            rating=Decimal('6.5'),
            is_active=False
        )
        self.inactive_movie.genres.set([self.comedy_genre])
    
    def test_movie_list_endpoint(self):
        """Test the movie list API endpoint."""
        url = reverse('movies:movie-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should only return active movies
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Active Movie')
    
    def test_movie_detail_endpoint(self):
        """Test the movie detail API endpoint."""
        url = reverse('movies:movie-detail', kwargs={'pk': str(self.active_movie.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Active Movie')
        self.assertIn('trailer_url', response.data)
        self.assertIn('created_at', response.data)
    
    def test_movie_detail_inactive_404(self):
        """Test that inactive movies return 404 on detail endpoint."""
        url = reverse('movies:movie-detail', kwargs={'pk': str(self.inactive_movie.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_movie_list_filtering_by_genre(self):
        """Test filtering movies by genre."""
        url = reverse('movies:movie-list')
        response = self.client.get(url, {'genres': str(self.action_genre.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Active Movie')
    
    def test_movie_list_search(self):
        """Test searching movies by title and description."""
        url = reverse('movies:movie-list')
        response = self.client.get(url, {'search': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Active Movie')
    
    def test_movie_list_ordering(self):
        """Test ordering movies."""
        # Create another active movie
        Movie.objects.create(
            title="Another Movie",
            description="Another test movie.",
            duration=100,
            release_date=date(2024, 7, 1),
            rating=Decimal('9.0'),
            is_active=True
        )
        
        url = reverse('movies:movie-list')
        response = self.client.get(url, {'ordering': '-rating'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        # Should be ordered by highest rating first
        self.assertEqual(results[0]['title'], 'Another Movie')
        self.assertEqual(results[1]['title'], 'Active Movie')


class GenreAPITest(APITestCase):
    """Test cases for Genre API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        Genre.objects.create(name="Action")
        Genre.objects.create(name="Comedy")
        Genre.objects.create(name="Drama")
    
    def test_genre_list_endpoint(self):
        """Test the genre list API endpoint."""
        url = reverse('movies:genre-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should return all genres, ordered by name
        results = response.data['results']
        self.assertEqual(len(results), 3)
        genre_names = [genre['name'] for genre in results]
        self.assertEqual(genre_names, ['Action', 'Comedy', 'Drama'])


class ShowtimeAPITest(APITestCase):
    """Test cases for Showtime API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A test movie.",
            duration=120,
            release_date=date.today(),
            is_active=True
        )
        
        self.theater = Theater.objects.create(
            name="API Test Main Theater",
            address="123 Main Street",
            city="Los Angeles",
            state="CA",
            zip_code="90210",
            phone_number="+1-555-0123"
        )
        
        self.theater3 = Theater.objects.create(
            name="Side Theater",
            address="789 Side Street",
            city="Los Angeles",
            state="CA",
            zip_code="90211",
            phone_number="+1-555-0789"
        )
        
        # Create future showtimes
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            datetime=future_time,
            theater=self.theater,
            screen_number=1,
            total_seats=100,
            available_seats=80,
            ticket_price=Decimal('15.99'),
            is_active=True
        )
        
        # Create inactive showtime
        self.inactive_showtime = Showtime.objects.create(
            movie=self.movie,
            datetime=future_time + timedelta(hours=2),
            theater=self.theater3,
            screen_number=2,
            total_seats=50,
            available_seats=50,
            ticket_price=Decimal('12.99'),
            is_active=False
        )
    
    def test_showtime_list_endpoint(self):
        """Test the showtime list API endpoint."""
        url = reverse('movies:showtime-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should only return active showtimes for active movies
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['theater_name'], 'API Test Main Theater')
    
    def test_showtime_detail_endpoint(self):
        """Test the showtime detail API endpoint."""
        url = reverse('movies:showtime-detail', kwargs={'pk': str(self.showtime.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['theater']['name'], 'API Test Main Theater')
        self.assertIn('movie', response.data)  # Should include full movie details
    
    def test_movie_showtimes_endpoint(self):
        """Test the movie-specific showtimes endpoint."""
        url = reverse('movies:movie-showtimes', kwargs={'movie_id': str(self.movie.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)  # Only active showtime
        self.assertEqual(results[0]['movie_title'], 'Test Movie')
    
    def test_showtime_filtering(self):
        """Test filtering showtimes by various parameters."""
        url = reverse('movies:showtime-list')
        
        # Filter by movie
        response = self.client.get(url, {'movie': str(self.movie.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Filter by theater
        response = self.client.get(url, {'theater': self.theater.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class TheaterModelTest(TestCase):
    """Test cases for the Theater model."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Test Theater",
            address="123 Test Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0123",
            total_screens=5,
            parking_available=True,
            accessibility_features="Wheelchair accessible",
            amenities="IMAX, Dolby Atmos"
        )
    
    def test_theater_creation(self):
        """Test basic theater creation."""
        self.assertEqual(self.theater.name, "Test Theater")
        self.assertEqual(self.theater.city, "Test City")
        self.assertEqual(self.theater.state, "TS")
        self.assertEqual(self.theater.total_screens, 5)
        self.assertTrue(self.theater.parking_available)
        self.assertTrue(self.theater.is_active)
    
    def test_theater_str_method(self):
        """Test the string representation of Theater."""
        expected = "Test Theater - Test City, TS"
        self.assertEqual(str(self.theater), expected)
    
    def test_full_address_property(self):
        """Test the full_address property."""
        expected = "123 Test Street, Test City, TS 12345"
        self.assertEqual(self.theater.full_address, expected)


class TheaterSerializerTest(TestCase):
    """Test cases for Theater serializers."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Grand Cinema",
            address="456 Grand Avenue",
            city="New York",
            state="NY",
            zip_code="10001",
            phone_number="+1-555-0456",
            email="info@grandcinema.com",
            total_screens=12,
            parking_available=True,
            accessibility_features="Full wheelchair access, audio descriptions",
            amenities="IMAX, 4DX, Premium seating, Bar & restaurant"
        )
    
    def test_theater_serialization(self):
        """Test TheaterSerializer output."""
        serializer = TheaterSerializer(self.theater)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Grand Cinema')
        self.assertEqual(data['city'], 'New York')
        self.assertEqual(data['state'], 'NY')
        self.assertEqual(data['total_screens'], 12)
        self.assertEqual(data['full_address'], '456 Grand Avenue, New York, NY 10001')
        self.assertTrue(data['parking_available'])
        self.assertEqual(data['amenities'], 'IMAX, 4DX, Premium seating, Bar & restaurant')
    
    def test_theater_detail_serialization(self):
        """Test TheaterDetailSerializer output."""
        serializer = TheaterDetailSerializer(self.theater)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Grand Cinema')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('active_showtimes_count', data)
        self.assertEqual(data['active_showtimes_count'], 0)  # No showtimes yet


class TheaterAPITest(APITestCase):
    """Test cases for Theater API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.theater1 = Theater.objects.create(
            name="Downtown Cinema",
            address="123 Main Street",
            city="Los Angeles",
            state="CA",
            zip_code="90210",
            phone_number="+1-555-0123",
            total_screens=8,
            parking_available=True
        )
        
        self.theater2 = Theater.objects.create(
            name="Uptown Theater",
            address="789 Broadway",
            city="New York",
            state="NY",
            zip_code="10001",
            phone_number="+1-555-0789",
            total_screens=6,
            parking_available=False
        )
    
    def test_theater_list_endpoint(self):
        """Test the theater list API endpoint."""
        url = reverse('movies:theater-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        results = response.data['results']
        self.assertEqual(len(results), 3)  # Includes the default "Main Theater" from migration
        
        # Should be ordered by name - Main Theater comes first alphabetically
        theater_names = [result['name'] for result in results]
        self.assertIn('Downtown Cinema', theater_names)
        self.assertIn('Uptown Theater', theater_names)
        self.assertIn('Main Theater', theater_names)  # From migration
    
    def test_theater_detail_endpoint(self):
        """Test the theater detail API endpoint."""
        url = reverse('movies:theater-detail', kwargs={'pk': str(self.theater1.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Downtown Cinema')
        self.assertEqual(response.data['city'], 'Los Angeles')
        self.assertIn('created_at', response.data)
    
    def test_theater_filtering(self):
        """Test filtering theaters by various parameters."""
        url = reverse('movies:theater-list')
        
        # Filter by city
        response = self.client.get(url, {'city': 'Los Angeles'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Main Theater + Downtown Cinema
        result_names = [result['name'] for result in response.data['results']]
        self.assertIn('Downtown Cinema', result_names)
        
        # Filter by parking availability
        response = self.client.get(url, {'parking_available': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Main Theater + Downtown Cinema both have parking
        result_names = [result['name'] for result in response.data['results']]
        self.assertIn('Downtown Cinema', result_names)
        
        # Search by name
        response = self.client.get(url, {'search': 'Downtown'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class SeatLayoutModelTest(TestCase):
    """Test cases for the SeatLayout model."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Seat Layout Test Theater",
            address="123 Test Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0123"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Standard Layout",
            total_rows=10,
            total_seats=120,
            row_configuration={
                "A": 12, "B": 12, "C": 12, "D": 12, "E": 12,
                "F": 12, "G": 12, "H": 12, "I": 12, "J": 12
            }
        )
    
    def test_seat_layout_creation(self):
        """Test basic seat layout creation."""
        self.assertEqual(self.seat_layout.theater, self.theater)
        self.assertEqual(self.seat_layout.screen_number, 1)
        self.assertEqual(self.seat_layout.name, "Standard Layout")
        self.assertEqual(self.seat_layout.total_rows, 10)
        self.assertEqual(self.seat_layout.total_seats, 120)
        self.assertTrue(self.seat_layout.is_active)
        self.assertIsInstance(self.seat_layout.id, uuid.UUID)
    
    def test_seat_layout_str_method(self):
        """Test the string representation of SeatLayout."""
        expected = "Seat Layout Test Theater Screen 1 - Standard Layout"
        self.assertEqual(str(self.seat_layout), expected)
    
    def test_unique_together_constraint(self):
        """Test the unique constraint on theater and screen_number."""
        with self.assertRaises(Exception):
            SeatLayout.objects.create(
                theater=self.theater,
                screen_number=1,  # Same theater and screen
                name="Another Layout",
                total_rows=8,
                total_seats=96,
                row_configuration={"A": 12, "B": 12}
            )
    
    def test_get_seat_map_method(self):
        """Test the get_seat_map method."""
        # Create some seats for the layout
        Seat.objects.create(
            seat_layout=self.seat_layout,
            row="A",
            number=1,
            seat_type="standard"
        )
        Seat.objects.create(
            seat_layout=self.seat_layout,
            row="A",
            number=2,
            seat_type="premium"
        )
        
        seat_map = self.seat_layout.get_seat_map()
        self.assertIsInstance(seat_map, list)
        self.assertTrue(len(seat_map) > 0)
        # Find row A in the seat map
        row_a = next((row for row in seat_map if row['row'] == 'A'), None)
        self.assertIsNotNone(row_a)
        self.assertIn('seats', row_a)


class SeatModelTest(TestCase):
    """Test cases for the Seat model."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Seat Model Test Theater",
            address="456 Test Avenue",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0456"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Test Layout",
            total_rows=5,
            total_seats=60,
            row_configuration={"A": 12, "B": 12, "C": 12, "D": 12, "E": 12}
        )
        
        self.seat = Seat.objects.create(
            seat_layout=self.seat_layout,
            row="A",
            number=12,
            seat_type="premium",
            price_multiplier=Decimal('1.5')
        )
    
    def test_seat_creation(self):
        """Test basic seat creation."""
        self.assertEqual(self.seat.seat_layout, self.seat_layout)
        self.assertEqual(self.seat.row, "A")
        self.assertEqual(self.seat.number, 12)
        self.assertEqual(self.seat.seat_type, "premium")
        self.assertEqual(self.seat.price_multiplier, Decimal('1.5'))
        self.assertTrue(self.seat.is_active)
        self.assertIsInstance(self.seat.id, uuid.UUID)
    
    def test_seat_str_method(self):
        """Test the string representation of Seat."""
        expected = "A12 (Premium)"
        self.assertEqual(str(self.seat), expected)
    
    def test_seat_identifier_property(self):
        """Test the seat_identifier property."""
        self.assertEqual(self.seat.seat_identifier, "A12")
    
    def test_unique_together_constraint(self):
        """Test the unique constraint on seat_layout, row, and number."""
        with self.assertRaises(Exception):
            Seat.objects.create(
                seat_layout=self.seat_layout,
                row="A",
                number=12,  # Same layout, row, and number
                seat_type="standard"
            )
    
    def test_seat_type_choices(self):
        """Test different seat type choices."""
        seat_types = ['standard', 'premium', 'accessible', 'couple', 'blocked']
        
        for i, seat_type in enumerate(seat_types, 1):
            seat = Seat.objects.create(
                seat_layout=self.seat_layout,
                row="B",
                number=i,
                seat_type=seat_type
            )
            self.assertEqual(seat.seat_type, seat_type)


class SeatReservationModelTest(TestCase):
    """Test cases for the SeatReservation model."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Reservation Test Theater",
            address="789 Test Boulevard",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0789"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Reservation Layout",
            total_rows=3,
            total_seats=36,
            row_configuration={"A": 12, "B": 12, "C": 12}
        )
        
        self.seat = Seat.objects.create(
            seat_layout=self.seat_layout,
            row="A",
            number=5,
            seat_type="standard"
        )
        
        self.movie = Movie.objects.create(
            title="Reservation Test Movie",
            description="A test movie for reservations.",
            duration=90,
            release_date=date.today(),
            is_active=True
        )
        
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time,
            screen_number=1,
            total_seats=36,
            available_seats=36,
            ticket_price=Decimal('12.99'),
            seat_layout=self.seat_layout
        )
        
        self.reservation = SeatReservation.objects.create(
            showtime=self.showtime,
            seat=self.seat,
            status='reserved',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
    
    def test_seat_reservation_creation(self):
        """Test basic seat reservation creation."""
        self.assertEqual(self.reservation.showtime, self.showtime)
        self.assertEqual(self.reservation.seat, self.seat)
        self.assertEqual(self.reservation.status, 'reserved')
        self.assertIsNotNone(self.reservation.reserved_at)
        self.assertIsNotNone(self.reservation.expires_at)
        self.assertIsNone(self.reservation.confirmed_at)
        self.assertIsNone(self.reservation.booking)
        self.assertIsInstance(self.reservation.id, uuid.UUID)
    
    def test_seat_reservation_str_method(self):
        """Test the string representation of SeatReservation."""
        expected = f"A5 - {self.showtime} (reserved)"
        self.assertEqual(str(self.reservation), expected)
    
    def test_is_expired_method(self):
        """Test the is_expired method."""
        # Should not be expired yet
        self.assertFalse(self.reservation.is_expired())
        
        # Create expired reservation
        expired_reservation = SeatReservation.objects.create(
            showtime=self.showtime,
            seat=Seat.objects.create(
                seat_layout=self.seat_layout,
                row="A",
                number=6,
                seat_type="standard"
            ),
            status='reserved',
            expires_at=timezone.now() - timedelta(minutes=5)
        )
        
        self.assertTrue(expired_reservation.is_expired())
    
    def test_confirm_reservation_method(self):
        """Test the confirm_reservation method."""
        self.reservation.confirm_reservation()
        
        self.assertEqual(self.reservation.status, 'confirmed')
        self.assertIsNotNone(self.reservation.confirmed_at)
    
    def test_cancel_reservation_method(self):
        """Test the cancel_reservation method."""
        self.reservation.cancel_reservation()
        
        self.assertEqual(self.reservation.status, 'cancelled')
    
    def test_unique_together_constraint(self):
        """Test the unique constraint on showtime and seat."""
        with self.assertRaises(Exception):
            SeatReservation.objects.create(
                showtime=self.showtime,
                seat=self.seat,  # Same showtime and seat
                status='reserved',
                expires_at=timezone.now() + timedelta(minutes=10)
            )


class SeatSerializerTest(TestCase):
    """Test cases for Seat serializers."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Serializer Test Theater",
            address="123 Serializer Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0123"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Test Layout",
            total_rows=5,
            total_seats=60,
            row_configuration={"A": 12, "B": 12}
        )
        
        self.seat = Seat.objects.create(
            seat_layout=self.seat_layout,
            row="A",
            number=8,
            seat_type="premium",
            price_multiplier=Decimal('1.25')
        )
    
    def test_seat_serialization(self):
        """Test SeatSerializer output."""
        serializer = SeatSerializer(self.seat)
        data = serializer.data
        
        self.assertEqual(data['row'], 'A')
        self.assertEqual(data['number'], 8)
        self.assertEqual(data['seat_identifier'], 'A8')
        self.assertEqual(data['seat_type'], 'premium')
        self.assertEqual(data['seat_type_display'], 'Premium')
        self.assertEqual(data['price_multiplier'], '1.25')
        self.assertTrue(data['is_active'])
    
    def test_seat_layout_serialization(self):
        """Test SeatLayoutSerializer output."""
        serializer = SeatLayoutSerializer(self.seat_layout)
        data = serializer.data
        
        self.assertEqual(data['theater_name'], 'Serializer Test Theater')
        self.assertEqual(data['screen_number'], 1)
        self.assertEqual(data['name'], 'Test Layout')
        self.assertEqual(data['total_rows'], 5)
        self.assertEqual(data['total_seats'], 60)
        self.assertEqual(data['seat_count'], 1)  # Only one seat created
        self.assertIn('seat_map', data)
        self.assertTrue(data['is_active'])


class ShowtimeSeatIntegrationTest(TestCase):
    """Test integration between Showtime and Seat functionality."""
    
    def setUp(self):
        self.theater = Theater.objects.create(
            name="Integration Test Theater",
            address="456 Integration Avenue",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0456"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Integration Layout",
            total_rows=3,
            total_seats=18,
            row_configuration={"A": 6, "B": 6, "C": 6}
        )
        
        # Create some seats
        self.seats = []
        for row in ['A', 'B', 'C']:
            for num in range(1, 7):
                seat_type = 'premium' if row == 'A' else 'standard'
                multiplier = Decimal('1.5') if seat_type == 'premium' else Decimal('1.0')
                seat = Seat.objects.create(
                    seat_layout=self.seat_layout,
                    row=row,
                    number=num,
                    seat_type=seat_type,
                    price_multiplier=multiplier
                )
                self.seats.append(seat)
        
        self.movie = Movie.objects.create(
            title="Integration Test Movie",
            description="Test movie for integration testing.",
            duration=120,
            release_date=date.today(),
            is_active=True
        )
        
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time,
            screen_number=1,
            total_seats=18,
            available_seats=18,
            ticket_price=Decimal('15.00'),
            seat_layout=self.seat_layout
        )
    
    def test_showtime_seat_map_generation(self):
        """Test generating seat availability map for showtime."""
        # Initially all seats should be available
        seat_map = self.showtime.get_available_seats_map()
        
        self.assertIsInstance(seat_map, list)
        self.assertEqual(len(seat_map), 3)  # 3 rows
        
        # Find row A and check it has 6 seats, all available
        row_a = next((row for row in seat_map if row['row'] == 'A'), None)
        self.assertIsNotNone(row_a)
        self.assertEqual(len(row_a['seats']), 6)
        for seat_info in row_a['seats']:
            self.assertTrue(seat_info['is_available'])
            self.assertEqual(seat_info['seat_type'], 'premium')
    
    def test_seat_reservation_affects_availability(self):
        """Test that seat reservations affect availability map."""
        # Reserve some seats
        seat_a1 = self.seats[0]  # A1
        seat_a2 = self.seats[1]  # A2
        
        SeatReservation.objects.create(
            showtime=self.showtime,
            seat=seat_a1,
            status='reserved',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        SeatReservation.objects.create(
            showtime=self.showtime,
            seat=seat_a2,
            status='confirmed',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        seat_map = self.showtime.get_available_seats_map()
        
        # Find row A and check that A1 and A2 are no longer available
        row_a = next((row for row in seat_map if row['row'] == 'A'), None)
        self.assertIsNotNone(row_a)
        
        # Create a mapping for easier testing
        row_a_seats = {seat['seat_id']: seat for seat in row_a['seats']}
        self.assertFalse(row_a_seats['A1']['is_available'])
        self.assertFalse(row_a_seats['A2']['is_available'])
        self.assertTrue(row_a_seats['A3']['is_available'])
    
    def test_seat_price_calculation(self):
        """Test seat-specific price calculation."""
        # Premium seat (A row) should cost more
        premium_seat = self.seats[0]  # A1 - premium
        standard_seat = self.seats[6]  # B1 - standard
        
        premium_price = self.showtime.calculate_seat_price(premium_seat)
        standard_price = self.showtime.calculate_seat_price(standard_seat)
        
        expected_premium = self.showtime.ticket_price * Decimal('1.5')
        expected_standard = self.showtime.ticket_price * Decimal('1.0')
        
        self.assertEqual(premium_price, expected_premium)
        self.assertEqual(standard_price, expected_standard)
        self.assertGreater(premium_price, standard_price)


class SeatAPITest(APITestCase):
    """Test cases for Seat-related API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user for authentication
        from django.contrib.auth import get_user_model
        from rest_framework.authtoken.models import Token
        User = get_user_model()
        
        self.user = User.objects.create_user(
            username='seatapi',
            email='seatapi@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.theater = Theater.objects.create(
            name="API Seat Test Theater",
            address="789 API Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0789"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="API Test Layout",
            total_rows=2,
            total_seats=12,
            row_configuration={"A": 6, "B": 6}
        )
        
        # Create some seats
        self.seats = []
        for row in ['A', 'B']:
            for num in range(1, 7):
                seat = Seat.objects.create(
                    seat_layout=self.seat_layout,
                    row=row,
                    number=num,
                    seat_type='standard'
                )
                self.seats.append(seat)
        
        self.movie = Movie.objects.create(
            title="API Test Movie",
            description="Test movie for API testing.",
            duration=100,
            release_date=date.today(),
            is_active=True
        )
        
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time,
            screen_number=1,
            total_seats=12,
            available_seats=12,
            ticket_price=Decimal('10.00'),
            seat_layout=self.seat_layout
        )
    
    def test_seat_layout_list_endpoint(self):
        """Test the seat layout list API endpoint."""
        url = reverse('movies:seat-layout-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'API Test Layout')
        self.assertEqual(results[0]['seat_count'], 12)
    
    def test_showtime_seat_map_endpoint(self):
        """Test the showtime seat map API endpoint."""
        url = reverse('movies:showtime-seat-map', kwargs={'pk': str(self.showtime.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['movie_title'], 'API Test Movie')
        self.assertEqual(response.data['theater_name'], 'API Seat Test Theater')
        self.assertTrue(response.data['has_seat_selection'])
        self.assertIn('seat_map', response.data)
        
        # Verify seat map structure
        seat_map = response.data['seat_map']
        self.assertIn('A', seat_map)
        self.assertIn('B', seat_map)
        self.assertEqual(len(seat_map['A']), 6)
        self.assertEqual(len(seat_map['B']), 6)
    
    def test_seat_reservation_endpoint(self):
        """Test the seat reservation API endpoint."""
        url = reverse('movies:reserve-seats', kwargs={'showtime_id': str(self.showtime.id)})
        
        data = {
            'seat_ids': ['A1', 'A2', 'B3'],
            'expiry_minutes': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['reservations']), 3)
        
        # Check that reservations were created
        self.assertEqual(SeatReservation.objects.count(), 3)
        
        # Check response structure
        for reservation in response.data['reservations']:
            self.assertIn('id', reservation)
            self.assertIn('seat_identifier', reservation)
            self.assertEqual(reservation['status'], 'Reserved')
            self.assertIn('expires_at', reservation)
    
    def test_seat_reservation_invalid_seats(self):
        """Test seat reservation with invalid seat identifiers."""
        url = reverse('movies:reserve-seats', kwargs={'showtime_id': str(self.showtime.id)})
        
        data = {
            'seat_ids': ['A1', 'Z99'],  # Z99 doesn't exist
            'expiry_minutes': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_seat_reservation_duplicate_seats(self):
        """Test seat reservation with already reserved seats."""
        # Create an existing reservation
        SeatReservation.objects.create(
            showtime=self.showtime,
            seat=self.seats[0],  # A1
            status='reserved',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        url = reverse('movies:reserve-seats', kwargs={'showtime_id': str(self.showtime.id)})
        
        data = {
            'seat_ids': ['A1', 'A2'],  # A1 is already reserved
            'expiry_minutes': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_seat_reservation_request_serializer_validation(self):
        """Test SeatReservationRequestSerializer validation."""
        # Test invalid seat ID format
        serializer = SeatReservationRequestSerializer(data={
            'seat_ids': ['A1', '1A', 'ABC'],  # Invalid formats
            'expiry_minutes': 10
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('seat_ids', serializer.errors)
        
        # Test empty seat list
        serializer = SeatReservationRequestSerializer(data={
            'seat_ids': [],
            'expiry_minutes': 10
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('seat_ids', serializer.errors)
        
        # Test valid data
        serializer = SeatReservationRequestSerializer(data={
            'seat_ids': ['A1', 'B2'],
            'expiry_minutes': 15
        })
        
        self.assertTrue(serializer.is_valid())
    
    def test_showtime_without_seat_layout(self):
        """Test showtime seat map endpoint for showtime without seat layout."""
        # Create a new theater for this showtime to avoid conflicts
        theater_no_seats = Theater.objects.create(
            name="No Seats Theater",
            address="999 No Seats Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-9999"
        )
        
        # Create showtime without seat layout
        showtime_no_seats = Showtime.objects.create(
            movie=self.movie,
            theater=theater_no_seats,
            datetime=timezone.now() + timedelta(days=3, hours=2),  # Different time to avoid conflicts
            screen_number=1,
            total_seats=50,
            available_seats=50,
            ticket_price=Decimal('10.00'),
            is_active=True
            # No seat_layout specified
        )
        
        url = reverse('movies:showtime-seat-map', kwargs={'pk': str(showtime_no_seats.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_seat_selection'])
        self.assertIsNone(response.data['seat_map'])
