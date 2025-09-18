import requests
import json
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.dateparse import parse_date
from movies.models import Movie, Genre


class Command(BaseCommand):
    help = 'Sync movies from The Movie Database (TMDB) API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to fetch from TMDB (default: 5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing movies before syncing'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing movies with new data'
        )

    def handle(self, *args, **options):
        # Get TMDB API key from environment
        api_key = getattr(settings, 'TMDB_API_KEY', None)
        if not api_key:
            raise CommandError('TMDB_API_KEY not found in settings or environment variables')

        self.api_key = api_key
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/w500'

        pages = options['pages']
        clear_existing = options['clear']
        update_existing = options['update_existing']

        if clear_existing:
            self.stdout.write('Clearing existing movies...')
            Movie.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing movies'))

        # First sync genres
        self.sync_genres()

        # Then sync movies
        self.sync_movies(pages, update_existing)

    def make_tmdb_request(self, endpoint, params=None):
        """Make a request to TMDB API"""
        if params is None:
            params = {}
        params['api_key'] = self.api_key

        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching from TMDB: {str(e)}')
            )
            return None

    def sync_genres(self):
        """Sync genres from TMDB"""
        self.stdout.write('Syncing genres from TMDB...')

        data = self.make_tmdb_request('genre/movie/list')
        if not data or 'genres' not in data:
            self.stdout.write(self.style.ERROR('Failed to fetch genres'))
            return

        genres_created = 0
        for genre_data in data['genres']:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name']
            )
            if created:
                genres_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Synced {genres_created} new genres')
        )

    def sync_movies(self, pages, update_existing):
        """Sync movies from TMDB"""
        self.stdout.write(f'Syncing movies from TMDB ({pages} pages)...')

        movies_created = 0
        movies_updated = 0
        movies_skipped = 0

        for page in range(1, pages + 1):
            self.stdout.write(f'Processing page {page}/{pages}...')

            # Get popular movies
            data = self.make_tmdb_request('movie/popular', {'page': page})
            if not data or 'results' not in data:
                self.stdout.write(self.style.ERROR(f'Failed to fetch page {page}'))
                continue

            for movie_data in data['results']:
                try:
                    result = self.process_movie(movie_data, update_existing)
                    if result == 'created':
                        movies_created += 1
                    elif result == 'updated':
                        movies_updated += 1
                    else:
                        movies_skipped += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing movie {movie_data.get("title", "Unknown")}: {str(e)}')
                    )
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Movies sync complete: {movies_created} created, {movies_updated} updated, {movies_skipped} skipped'
            )
        )

    def process_movie(self, movie_data, update_existing):
        """Process a single movie from TMDB data"""
        title = movie_data.get('title', '').strip()
        if not title:
            return 'skipped'

        # Get detailed movie info
        movie_id = movie_data['id']
        detailed_data = self.make_tmdb_request(f'movie/{movie_id}')
        if not detailed_data:
            return 'skipped'

        # Map TMDB data to our model fields
        mapped_data = self.map_tmdb_data(movie_data, detailed_data)

        # Check if movie already exists
        existing_movie = Movie.objects.filter(title=title).first()

        if existing_movie:
            if update_existing:
                # Update existing movie
                for field, value in mapped_data.items():
                    if field != 'genres':
                        setattr(existing_movie, field, value)
                existing_movie.save()

                # Update genres
                if 'genres' in mapped_data:
                    existing_movie.genres.clear()
                    existing_movie.genres.add(*mapped_data['genres'])

                return 'updated'
            else:
                return 'skipped'
        else:
            # Create new movie
            genres = mapped_data.pop('genres', [])
            movie = Movie.objects.create(**mapped_data)

            # Add genres
            if genres:
                movie.genres.add(*genres)

            return 'created'

    def map_tmdb_data(self, movie_data, detailed_data):
        """Map TMDB API data to our Movie model fields"""
        # Parse release date
        release_date_str = movie_data.get('release_date')
        release_date = None
        if release_date_str:
            try:
                release_date = parse_date(release_date_str)
            except:
                pass

        # Get poster image URL
        poster_path = movie_data.get('poster_path')
        poster_image = f"{self.image_base_url}{poster_path}" if poster_path else None

        # Get trailer URL from videos
        trailer_url = self.get_trailer_url(detailed_data['id'])

        # Map genres
        genre_objects = []
        for genre_data in detailed_data.get('genres', []):
            try:
                genre = Genre.objects.get(name=genre_data['name'])
                genre_objects.append(genre)
            except Genre.DoesNotExist:
                # Create genre if it doesn't exist
                genre = Genre.objects.create(name=genre_data['name'])
                genre_objects.append(genre)

        # Map rating (TMDB uses 0-10 scale, which matches our model)
        rating = movie_data.get('vote_average')
        if rating:
            rating = round(Decimal(str(rating)), 1)

        mapped_data = {
            'title': movie_data.get('title', '').strip(),
            'description': movie_data.get('overview', '').strip() or 'No description available',
            'duration': detailed_data.get('runtime') or 120,  # Default to 120 minutes if not available
            'release_date': release_date or datetime.now().date(),
            'rating': rating,
            'poster_image': poster_image,
            'trailer_url': trailer_url,
            'genres': genre_objects,
            'is_active': True
        }

        return mapped_data

    def get_trailer_url(self, tmdb_movie_id):
        """Get trailer URL for a movie"""
        data = self.make_tmdb_request(f'movie/{tmdb_movie_id}/videos')
        if not data or 'results' not in data:
            return None

        # Look for YouTube trailers
        for video in data['results']:
            if (video.get('site', '').lower() == 'youtube' and
                video.get('type', '').lower() == 'trailer'):
                key = video.get('key')
                if key:
                    return f"https://www.youtube.com/watch?v={key}"

        return None