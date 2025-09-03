import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from movies.models import Showtime
from accounts.models import Customer


class Booking(models.Model):
    """
    Booking model for cinema ticket reservations.
    
    Links customers to showtimes with seat quantity and payment tracking.
    """
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings')
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    number_of_seats = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of seats booked"
    )
    total_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total amount for the booking"
    )
    
    # Booking status and tracking
    status = models.CharField(
        max_length=10,
        choices=BOOKING_STATUS_CHOICES,
        default='pending',
        help_text="Current status of the booking"
    )
    booking_reference = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique booking reference number"
    )
    
    # Seat information (for future seat mapping)
    seat_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of specific seat numbers (if applicable)"
    )
    
    # Pricing breakdown
    base_price_per_seat = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Base price per seat at time of booking"
    )
    discount_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total discount applied to booking"
    )
    loyalty_points_used = models.PositiveIntegerField(
        default=0,
        help_text="Loyalty points used for discount"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    special_requests = models.TextField(
        blank=True,
        help_text="Any special requests from customer"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.customer.full_name} - {self.showtime}"

    def save(self, *args, **kwargs):
        # Generate booking reference if not exists
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Update timestamps based on status
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
            
        super().save(*args, **kwargs)

    def generate_booking_reference(self):
        """Generate a unique booking reference."""
        import random
        import string
        timestamp = str(int(timezone.now().timestamp()))[-6:]  # Last 6 digits of timestamp
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"BK{timestamp}{random_part}"

    @property
    def is_active(self):
        """Check if booking is active (confirmed and not past showtime)."""
        return (
            self.status == 'confirmed' and
            self.showtime.datetime > timezone.now()
        )

    @property
    def can_cancel(self):
        """Check if booking can be cancelled (confirmed and more than 2 hours before showtime)."""
        if self.status != 'confirmed':
            return False
        
        time_until_showtime = self.showtime.datetime - timezone.now()
        return time_until_showtime.total_seconds() > 2 * 3600  # 2 hours in seconds

    def confirm_booking(self):
        """Confirm the booking and update showtime availability."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            
            # Update showtime seat availability
            self.showtime.available_seats -= self.number_of_seats
            self.showtime.save()
            
            # Award loyalty points (1 point per dollar spent)
            points_earned = int(self.total_amount)
            self.customer.add_loyalty_points(points_earned)
            
            self.save()

    def cancel_booking(self):
        """Cancel the booking and restore showtime availability."""
        if self.can_cancel:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            
            # Restore showtime seat availability
            self.showtime.available_seats += self.number_of_seats
            self.showtime.save()
            
            self.save()
            return True
        return False


class Payment(models.Model):
    """
    Payment model for tracking booking payments.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    
    # Payment details
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Payment amount"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text="Payment status"
    )
    
    # Transaction tracking
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External payment processor transaction ID"
    )
    processor_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Response from payment processor"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.booking.booking_reference} - {self.status}"

    def mark_completed(self, transaction_id=None):
        """Mark payment as completed."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
        
        # Confirm the associated booking
        self.booking.confirm_booking()

    def mark_failed(self, reason=None):
        """Mark payment as failed."""
        self.status = 'failed'
        if reason:
            self.processor_response['failure_reason'] = reason
        self.save()
