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


class MovieGenre(models.Model):
    """Through model for Movie-Genre many-to-many relationship with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['movie', 'genre']
        ordering = ['movie__title', 'genre__name']

    def __str__(self):
        return f"{self.movie.title} - {self.genre.name}"


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
    genres = models.ManyToManyField(Genre, through='MovieGenre', related_name='movies')
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
    seat_layout = models.ForeignKey('SeatLayout', on_delete=models.CASCADE, related_name='showtimes', null=True, blank=True)
    total_seats = models.PositiveIntegerField(default=100)
    available_seats = models.PositiveIntegerField(default=100)
    ticket_price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        help_text="Base ticket price in dollars"
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
    
    def get_available_seats_map(self):
        """Get a map of available seats for this showtime."""
        if not self.seat_layout:
            return None
        
        # Get all confirmed/reserved seat reservations for this showtime
        reserved_seats = set()
        for reservation in self.seat_reservations.filter(status__in=['reserved', 'confirmed']):
            reserved_seats.add(reservation.seat.seat_identifier)
        
        seat_map = []
        for row_data in self.seat_layout.get_seat_map():
            row_seats = []
            for seat_id in row_data['seats']:
                seat = self.seat_layout.seats.filter(
                    row=row_data['row'], 
                    number=int(seat_id[1:])  # Extract number from 'A12' -> 12
                ).first()
                
                if seat:
                    row_seats.append({
                        'seat_id': seat_id,
                        'seat_type': seat.seat_type,
                        'price_multiplier': float(seat.price_multiplier),
                        'is_available': seat_id not in reserved_seats and seat.is_active,
                        'is_blocked': not seat.is_active or seat.seat_type == 'blocked'
                    })
                else:
                    # Seat doesn't exist in database, mark as blocked
                    row_seats.append({
                        'seat_id': seat_id,
                        'seat_type': 'blocked',
                        'price_multiplier': 1.0,
                        'is_available': False,
                        'is_blocked': True
                    })
            
            seat_map.append({
                'row': row_data['row'],
                'seats': row_seats
            })
        
        return seat_map
    
    def calculate_seat_price(self, seat):
        """Calculate the price for a specific seat."""
        return self.ticket_price * seat.price_multiplier
    
    def reserve_seats(self, seat_ids, customer, expiry_minutes=15):
        """Reserve specific seats for a customer."""
        from django.utils import timezone
        from datetime import timedelta
        
        reserved_seats = []
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        for seat_id in seat_ids:
            # Parse seat_id like 'A12' into row='A', number=12
            row = seat_id[0]
            number = int(seat_id[1:])
            
            seat = self.seat_layout.seats.filter(row=row, number=number).first()
            if not seat:
                raise ValueError(f"Seat {seat_id} does not exist")
            
            # Check if seat is already reserved
            existing_reservation = self.seat_reservations.filter(
                seat=seat,
                status__in=['reserved', 'confirmed']
            ).first()
            
            if existing_reservation:
                raise ValueError(f"Seat {seat_id} is already reserved")
            
            # Create reservation
            reservation = SeatReservation.objects.create(
                showtime=self,
                seat=seat,
                status='reserved',
                expires_at=expires_at
            )
            reserved_seats.append(reservation)
        
        return reserved_seats


class SeatLayout(models.Model):
    """Defines the seat layout configuration for a theater screen."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seat_layouts')
    screen_number = models.PositiveIntegerField()
    name = models.CharField(max_length=100, help_text="Layout name (e.g., 'Standard', 'IMAX', 'Premium')")
    total_rows = models.PositiveIntegerField()
    total_seats = models.PositiveIntegerField()
    row_configuration = models.JSONField(
        help_text="JSON configuration of seats per row, e.g., {'A': 12, 'B': 14, 'C': 16}"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['theater__name', 'screen_number']
        unique_together = ['theater', 'screen_number']

    def __str__(self):
        return f"{self.theater.name} Screen {self.screen_number} - {self.name}"

    def get_seat_map(self):
        """Generate a visual representation of the seat layout."""
        seat_map = []
        for row_letter, seat_count in self.row_configuration.items():
            row_seats = []
            for seat_num in range(1, seat_count + 1):
                row_seats.append(f"{row_letter}{seat_num}")
            seat_map.append({
                'row': row_letter,
                'seats': row_seats
            })
        return seat_map


class Seat(models.Model):
    """Individual seat in a theater."""
    SEAT_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('accessible', 'Accessible'),
        ('couple', 'Couple Seat'),
        ('blocked', 'Blocked/Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seat_layout = models.ForeignKey(SeatLayout, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=2, help_text="Seat row (e.g., 'A', 'B', 'C')")
    number = models.PositiveIntegerField(help_text="Seat number within the row")
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default='standard')
    price_multiplier = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=1.00,
        help_text="Price multiplier for this seat type (1.0 = base price, 1.5 = 50% premium)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['row', 'number']
        unique_together = ['seat_layout', 'row', 'number']

    def __str__(self):
        return f"{self.row}{self.number} ({self.get_seat_type_display()})"

    @property
    def seat_identifier(self):
        """Returns seat identifier like 'A12'."""
        return f"{self.row}{self.number}"


class SeatReservation(models.Model):
    """Tracks seat reservations for specific showtimes."""
    STATUS_CHOICES = [
        ('reserved', 'Reserved'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='seat_reservations')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='reservations')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='seat_reservations', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved')
    reserved_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="Temporary reservation expires after this time")
    
    class Meta:
        ordering = ['showtime__datetime', 'seat__row', 'seat__number']
        unique_together = ['showtime', 'seat']

    def __str__(self):
        return f"{self.seat.seat_identifier} - {self.showtime} ({self.status})"

    def is_expired(self):
        """Check if the reservation has expired."""
        from django.utils import timezone
        return self.status == 'reserved' and timezone.now() > self.expires_at

    def confirm_reservation(self):
        """Confirm the seat reservation."""
        from django.utils import timezone
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()

    def cancel_reservation(self):
        """Cancel the seat reservation."""
        self.status = 'cancelled'
        self.save()
