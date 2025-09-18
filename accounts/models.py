import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class UserProfile(models.Model):
    """
    User profile model extending Django's User with role-based access.
    """
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        help_text="User role for access control"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_admin(self):
        """Check if user has admin privileges."""
        return self.role == 'admin'
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    class Meta:
        ordering = ['-created_at']


# Add is_admin property to User model
def user_is_admin(self):
    try:
        return self.user_profile.is_admin
    except UserProfile.DoesNotExist:
        return False

def user_role(self):
    try:
        return self.user_profile.role
    except UserProfile.DoesNotExist:
        return 'customer'

User.add_to_class('is_admin', property(user_is_admin))
User.add_to_class('role', property(user_role))


class Customer(models.Model):
    """
    Customer profile extending Django's User model.
    
    Stores additional customer information for cinema bookings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="Customer's phone number for booking notifications"
    )
    date_of_birth = models.DateField(null=True, blank=True, help_text="Customer's date of birth")
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
        ],
        default='en',
        help_text="Customer's preferred language for communications"
    )
    receive_marketing_emails = models.BooleanField(
        default=False,
        help_text="Whether customer wants to receive marketing emails"
    )
    receive_booking_notifications = models.BooleanField(
        default=True,
        help_text="Whether customer wants to receive booking confirmation emails"
    )
    loyalty_points = models.PositiveIntegerField(
        default=0,
        help_text="Loyalty points earned by customer"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.user.email}"

    @property
    def full_name(self):
        """Return the customer's full name."""
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        """Return the customer's email address."""
        return self.user.email

    def add_loyalty_points(self, points):
        """Add loyalty points to customer account."""
        self.loyalty_points += points
        self.save()

    def can_redeem_points(self, points_needed):
        """Check if customer has enough points for redemption."""
        return self.loyalty_points >= points_needed
