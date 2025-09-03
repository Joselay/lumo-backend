import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import Movie, Genre, Showtime, Theater
from .serializers import (
    MovieListSerializer, MovieDetailSerializer, 
    GenreSerializer, ShowtimeSerializer, ShowtimeDetailSerializer,
    TheaterSerializer, TheaterDetailSerializer
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
