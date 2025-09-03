import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Theater(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    total_screens = models.PositiveIntegerField(default=1)
    parking_available = models.BooleanField(default=True)
    accessibility_features = models.TextField(blank=True, help_text="Describe accessibility features")
    amenities = models.TextField(blank=True, help_text="List amenities like concessions, IMAX, etc.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"


class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Movie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    release_date = models.DateField()
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        null=True,
        blank=True
    )
    poster_image = models.URLField(blank=True, null=True)
    trailer_url = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name='movies')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date', 'title']

    def __str__(self):
        return self.title


class Showtime(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showtimes')
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='showtimes')
    datetime = models.DateTimeField()
    screen_number = models.PositiveIntegerField(default=1)
    total_seats = models.PositiveIntegerField(default=100)
    available_seats = models.PositiveIntegerField(default=100)
    ticket_price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        help_text="Ticket price in dollars"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['datetime', 'theater__name', 'screen_number']
        unique_together = ['theater', 'screen_number', 'datetime']

    def __str__(self):
        return f"{self.movie.title} - {self.datetime.strftime('%Y-%m-%d %H:%M')} - {self.theater.name} Screen {self.screen_number}"
    
    @property
    def is_available(self):
        return self.is_active and self.available_seats > 0 and self.datetime > timezone.now()
    
    @property
    def seats_sold(self):
        return self.total_seats - self.available_seats
