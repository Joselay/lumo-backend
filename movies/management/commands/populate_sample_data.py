from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal
from movies.models import Movie, Genre, Showtime


class Command(BaseCommand):
    help = 'Populate database with sample movie and genre data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Showtime.objects.all().delete()
            Movie.objects.all().delete()
            Genre.objects.all().delete()

        # Create genres
        genres_data = [
            'Action', 'Adventure', 'Animation', 'Biography', 'Comedy',
            'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy',
            'History', 'Horror', 'Music', 'Mystery', 'Romance',
            'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western'
        ]

        genres = {}
        for genre_name in genres_data:
            genre, created = Genre.objects.get_or_create(name=genre_name)
            genres[genre_name] = genre
            if created:
                self.stdout.write(f'Created genre: {genre_name}')

        # Sample movies data
        movies_data = [
            {
                'title': 'Avengers: Endgame',
                'description': 'The epic conclusion to the Infinity Saga that will forever change the Marvel Cinematic Universe. After the devastating events of Infinity War, the universe is in ruins.',
                'duration': 181,
                'release_date': date.today() - timedelta(days=30),
                'rating': Decimal('8.4'),
                'poster_image': 'https://example.com/posters/avengers-endgame.jpg',
                'trailer_url': 'https://youtube.com/watch?v=TcMBFSGVi1c',
                'genres': ['Action', 'Adventure', 'Sci-Fi']
            },
            {
                'title': 'Spider-Man: No Way Home',
                'description': 'Peter Parker\'s secret identity is revealed, forcing him to ask Doctor Strange for help. When a spell goes wrong, dangerous foes from other worlds start to appear.',
                'duration': 148,
                'release_date': date.today() - timedelta(days=15),
                'rating': Decimal('8.2'),
                'poster_image': 'https://example.com/posters/spiderman-no-way-home.jpg',
                'trailer_url': 'https://youtube.com/watch?v=JfVOs4VSpmA',
                'genres': ['Action', 'Adventure', 'Sci-Fi']
            },
            {
                'title': 'The Batman',
                'description': 'Batman ventures into Gotham City\'s underworld when a sadistic killer leaves behind a trail of cryptic clues. As the evidence begins to lead closer to home.',
                'duration': 176,
                'release_date': date.today() - timedelta(days=5),
                'rating': Decimal('7.8'),
                'poster_image': 'https://example.com/posters/the-batman.jpg',
                'trailer_url': 'https://youtube.com/watch?v=mqqft2x_Aa4',
                'genres': ['Action', 'Crime', 'Drama']
            },
            {
                'title': 'Top Gun: Maverick',
                'description': 'After thirty years, Maverick is still pushing the envelope as a top naval aviator, but must confront ghosts of his past when he leads an elite group of graduates.',
                'duration': 130,
                'release_date': date.today() + timedelta(days=7),
                'rating': Decimal('8.6'),
                'poster_image': 'https://example.com/posters/top-gun-maverick.jpg',
                'trailer_url': 'https://youtube.com/watch?v=g4U4BQW9OEk',
                'genres': ['Action', 'Drama']
            },
            {
                'title': 'Dune',
                'description': 'Paul Atreides leads nomadic tribes in a revolt against the evil Harkonnen oppressors on the desert planet Arrakis.',
                'duration': 155,
                'release_date': date.today() + timedelta(days=14),
                'rating': Decimal('8.0'),
                'poster_image': 'https://example.com/posters/dune.jpg',
                'trailer_url': 'https://youtube.com/watch?v=n9xhJrPXop4',
                'genres': ['Adventure', 'Drama', 'Sci-Fi']
            },
            {
                'title': 'Everything Everywhere All at Once',
                'description': 'An aging Chinese immigrant is swept up in an insane adventure, in which she alone can save the world by exploring other universes.',
                'duration': 139,
                'release_date': date.today() - timedelta(days=60),
                'rating': Decimal('7.8'),
                'poster_image': 'https://example.com/posters/everything-everywhere.jpg',
                'trailer_url': 'https://youtube.com/watch?v=WLVFrL3pJpk',
                'genres': ['Action', 'Adventure', 'Comedy', 'Sci-Fi']
            },
            {
                'title': 'The Northman',
                'description': 'Young prince Amleth is on the verge of becoming a man when his father is brutally murdered by his uncle, who kidnaps the boy\'s mother.',
                'duration': 137,
                'release_date': date.today() + timedelta(days=21),
                'rating': Decimal('7.0'),
                'poster_image': 'https://example.com/posters/the-northman.jpg',
                'trailer_url': 'https://youtube.com/watch?v=oMSdFM12hOw',
                'genres': ['Action', 'Adventure', 'Drama', 'Fantasy']
            },
            {
                'title': 'Turning Red',
                'description': 'A thirteen-year-old girl named Mei is torn between staying her mother\'s dutiful daughter and the changes of adolescence.',
                'duration': 100,
                'release_date': date.today() - timedelta(days=90),
                'rating': Decimal('7.0'),
                'poster_image': 'https://example.com/posters/turning-red.jpg',
                'trailer_url': 'https://youtube.com/watch?v=XdKzUbAiswE',
                'genres': ['Animation', 'Adventure', 'Comedy', 'Family']
            },
            {
                'title': 'The Lost City',
                'description': 'A reclusive romance novelist on a book tour with her cover model gets swept up in a kidnapping attempt that lands them both in a jungle adventure.',
                'duration': 112,
                'release_date': date.today() + timedelta(days=28),
                'rating': Decimal('6.7'),
                'poster_image': 'https://example.com/posters/the-lost-city.jpg',
                'trailer_url': 'https://youtube.com/watch?v=nfKO9rYDmE8',
                'genres': ['Action', 'Adventure', 'Comedy', 'Romance']
            },
            {
                'title': 'Morbius',
                'description': 'Dangerously ill with a rare blood disorder and determined to save others suffering his same fate, Dr. Morbius attempts a desperate gamble.',
                'duration': 104,
                'release_date': date.today() + timedelta(days=35),
                'rating': Decimal('5.2'),
                'poster_image': 'https://example.com/posters/morbius.jpg',
                'trailer_url': 'https://youtube.com/watch?v=oZ6iiRrz1SY',
                'genres': ['Action', 'Adventure', 'Horror', 'Sci-Fi']
            }
        ]

        # Create movies
        for movie_data in movies_data:
            movie_genres = movie_data.pop('genres')
            movie, created = Movie.objects.get_or_create(
                title=movie_data['title'],
                defaults=movie_data
            )
            
            if created:
                # Add genres to the movie
                for genre_name in movie_genres:
                    if genre_name in genres:
                        movie.genres.add(genres[genre_name])
                
                self.stdout.write(f'Created movie: {movie.title}')
            else:
                self.stdout.write(f'Movie already exists: {movie.title}')

        # Create sample showtimes for movies
        self.stdout.write('Creating sample showtimes...')
        theaters = ['Main Theater', 'IMAX Theater', 'Premium Theater']
        base_prices = {'Main Theater': Decimal('12.50'), 'IMAX Theater': Decimal('18.00'), 'Premium Theater': Decimal('15.00')}
        
        movies = Movie.objects.all()
        showtimes_created = 0
        
        for movie in movies:
            # Create showtimes for the next 7 days
            for day_offset in range(7):
                show_date = date.today() + timedelta(days=day_offset)
                
                # Create 3-4 showtimes per day for each movie
                show_times = ['14:00', '17:30', '20:00', '22:30']
                
                for i, show_time in enumerate(show_times):
                    theater = theaters[i % len(theaters)]
                    screen_number = (i % 3) + 1
                    
                    # Create datetime object
                    show_datetime = timezone.make_aware(
                        datetime.combine(show_date, datetime.strptime(show_time, '%H:%M').time())
                    )
                    
                    showtime, created = Showtime.objects.get_or_create(
                        theater_name=theater,
                        screen_number=screen_number,
                        datetime=show_datetime,
                        defaults={
                            'movie': movie,
                            'total_seats': 100 if theater != 'IMAX Theater' else 150,
                            'available_seats': 75 if theater != 'IMAX Theater' else 120,
                            'ticket_price': base_prices[theater],
                            'is_active': True
                        }
                    )
                    
                    if created:
                        showtimes_created += 1
                    
                    if showtimes_created % 20 == 0:
                        self.stdout.write(f'Created {showtimes_created} showtimes...')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {Genre.objects.count()} genres, {Movie.objects.count()} movies, and {Showtime.objects.count()} showtimes'
            )
        )