"""
Base test classes and utilities for movies app testing.
"""

import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from .models import Movie, Genre, Showtime


class BaseTestCase(TestCase):
    """Base test case with common test data setup."""
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.setup_genres()
        self.setup_movies()
    
    def setup_genres(self):
        """Create test genres."""
        self.action_genre = Genre.objects.create(name="Action")
        self.comedy_genre = Genre.objects.create(name="Comedy")
        self.drama_genre = Genre.objects.create(name="Drama")
        self.horror_genre = Genre.objects.create(name="Horror")
        self.scifi_genre = Genre.objects.create(name="Sci-Fi")
    
    def setup_movies(self):
        """Create test movies."""
        # Active movie 1
        self.movie1 = Movie.objects.create(
            title="Avengers: Endgame",
            description="The epic conclusion to the Infinity Saga.",
            duration=181,
            release_date=date(2024, 4, 26),
            rating=Decimal('8.4'),
            poster_image="https://example.com/posters/avengers.jpg",
            trailer_url="https://youtube.com/watch?v=abc123",
            is_active=True
        )
        self.movie1.genres.set([self.action_genre, self.scifi_genre])
        
        # Active movie 2
        self.movie2 = Movie.objects.create(
            title="The Dark Knight",
            description="Batman faces the Joker.",
            duration=152,
            release_date=date(2024, 3, 15),
            rating=Decimal('9.0'),
            poster_image="https://example.com/posters/batman.jpg",
            trailer_url="https://youtube.com/watch?v=def456",
            is_active=True
        )
        self.movie2.genres.set([self.action_genre, self.drama_genre])
        
        # Inactive movie
        self.inactive_movie = Movie.objects.create(
            title="Old Movie",
            description="An inactive movie.",
            duration=90,
            release_date=date(2020, 1, 1),
            rating=Decimal('6.0'),
            is_active=False
        )
        self.inactive_movie.genres.set([self.comedy_genre])


class BaseAPITestCase(APITestCase, BaseTestCase):
    """Base API test case with authentication and common setup."""
    
    def setUp(self):
        """Set up API client and test data."""
        super().setUp()
        self.client = APIClient()
        self.setup_showtimes()
    
    def setup_showtimes(self):
        """Create test showtimes."""
        future_time = timezone.now() + timedelta(days=1)
        
        # Active showtime for movie1
        self.showtime1 = Showtime.objects.create(
            movie=self.movie1,
            datetime=future_time,
            theater_name="Main Theater",
            screen_number=1,
            total_seats=100,
            available_seats=80,
            ticket_price=Decimal('15.99'),
            is_active=True
        )
        
        # Active showtime for movie2
        self.showtime2 = Showtime.objects.create(
            movie=self.movie2,
            datetime=future_time + timedelta(hours=2),
            theater_name="Side Theater",
            screen_number=2,
            total_seats=150,
            available_seats=150,
            ticket_price=Decimal('18.50'),
            is_active=True
        )
        
        # Inactive showtime
        self.inactive_showtime = Showtime.objects.create(
            movie=self.movie1,
            datetime=future_time + timedelta(hours=4),
            theater_name="Old Theater",
            screen_number=1,
            total_seats=50,
            available_seats=30,
            ticket_price=Decimal('12.99'),
            is_active=False
        )


class MovieTestMixin:
    """Mixin providing movie-related test utilities."""
    
    def create_test_movie(self, title="Test Movie", is_active=True, **kwargs):
        """Create a test movie with default values."""
        defaults = {
            'description': f"Description for {title}",
            'duration': 120,
            'release_date': date.today(),
            'rating': Decimal('7.5'),
            'is_active': is_active
        }
        defaults.update(kwargs)
        
        return Movie.objects.create(title=title, **defaults)
    
    def create_test_genre(self, name="Test Genre"):
        """Create a test genre."""
        return Genre.objects.create(name=name)
    
    def create_test_showtime(self, movie=None, **kwargs):
        """Create a test showtime with default values."""
        if movie is None:
            movie = self.create_test_movie()
        
        defaults = {
            'datetime': timezone.now() + timedelta(days=1),
            'theater_name': 'Test Theater',
            'screen_number': 1,
            'total_seats': 100,
            'available_seats': 100,
            'ticket_price': Decimal('15.00'),
            'is_active': True
        }
        defaults.update(kwargs)
        
        return Showtime.objects.create(movie=movie, **defaults)
    
    def assert_movie_data(self, movie_data, movie_instance):
        """Assert movie API data matches model instance."""
        self.assertEqual(movie_data['id'], str(movie_instance.id))
        self.assertEqual(movie_data['title'], movie_instance.title)
        self.assertEqual(movie_data['description'], movie_instance.description)
        self.assertEqual(movie_data['duration'], movie_instance.duration)
        self.assertEqual(movie_data['release_date'], movie_instance.release_date.strftime('%Y-%m-%d'))
        
        if movie_instance.rating:
            self.assertEqual(movie_data['rating'], str(movie_instance.rating))
        else:
            self.assertIsNone(movie_data['rating'])


class ShowtimeTestMixin:
    """Mixin providing showtime-related test utilities."""
    
    def assert_showtime_data(self, showtime_data, showtime_instance):
        """Assert showtime API data matches model instance."""
        self.assertEqual(showtime_data['id'], str(showtime_instance.id))
        self.assertEqual(showtime_data['theater_name'], showtime_instance.theater_name)
        self.assertEqual(showtime_data['screen_number'], showtime_instance.screen_number)
        self.assertEqual(showtime_data['total_seats'], showtime_instance.total_seats)
        self.assertEqual(showtime_data['available_seats'], showtime_instance.available_seats)
        self.assertEqual(showtime_data['ticket_price'], str(showtime_instance.ticket_price))
        self.assertEqual(showtime_data['seats_sold'], showtime_instance.seats_sold)
        self.assertEqual(showtime_data['is_available'], showtime_instance.is_available)


# Custom assertions for better test readability
class CustomAssertionsMixin:
    """Mixin providing custom assertions for testing."""
    
    def assertContainsKeys(self, dictionary, keys):
        """Assert that dictionary contains all specified keys."""
        missing_keys = [key for key in keys if key not in dictionary]
        if missing_keys:
            self.fail(f"Dictionary is missing keys: {missing_keys}")
    
    def assertValidUUID(self, uuid_string):
        """Assert that string is a valid UUID."""
        try:
            uuid.UUID(uuid_string)
        except ValueError:
            self.fail(f"'{uuid_string}' is not a valid UUID")
    
    def assertTimestampFormat(self, timestamp_string):
        """Assert that string is in expected timestamp format."""
        try:
            datetime.fromisoformat(timestamp_string.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"'{timestamp_string}' is not in expected timestamp format")


class FullTestCase(BaseAPITestCase, MovieTestMixin, ShowtimeTestMixin, CustomAssertionsMixin):
    """Full-featured test case combining all mixins."""
    pass