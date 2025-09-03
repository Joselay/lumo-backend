from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import Booking, Payment
from movies.serializers import ShowtimeSerializer
from movies.models import SeatReservation
from accounts.serializers import CustomerSerializer


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings.
    
    Handles booking creation with automatic total calculation and seat selection.
    """
    seat_reservation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of seat reservation IDs to confirm with this booking"
    )
    
    class Meta:
        model = Booking
        fields = [
            'showtime', 'number_of_seats', 'seat_numbers', 
            'special_requests', 'loyalty_points_used', 'seat_reservation_ids'
        ]

    def validate_number_of_seats(self, value):
        """Validate seat quantity is reasonable."""
        if value > 10:
            raise serializers.ValidationError("Maximum 10 seats per booking.")
        return value

    def validate(self, data):
        """Validate booking constraints."""
        showtime = data['showtime']
        number_of_seats = data['number_of_seats']
        
        # Check if showtime is still available
        if not showtime.is_available:
            raise serializers.ValidationError("This showtime is no longer available.")
        
        # Check seat availability
        if showtime.available_seats < number_of_seats:
            raise serializers.ValidationError(
                f"Only {showtime.available_seats} seats available for this showtime."
            )
        
        # Check if showtime is not in the past
        if showtime.datetime <= timezone.now():
            raise serializers.ValidationError("Cannot book for past showtimes.")
        
        return data

    def create(self, validated_data):
        """Create booking with calculated pricing and seat reservation handling."""
        customer = self.context['request'].user.customer_profile
        showtime = validated_data['showtime']
        number_of_seats = validated_data['number_of_seats']
        loyalty_points_used = validated_data.get('loyalty_points_used', 0)
        seat_reservation_ids = validated_data.pop('seat_reservation_ids', [])
        
        # Handle seat selection if provided
        selected_seats = []
        if seat_reservation_ids:
            # Validate seat reservations belong to this showtime and user
            reservations = SeatReservation.objects.filter(
                id__in=seat_reservation_ids,
                showtime=showtime,
                status='reserved'
            )
            
            if len(reservations) != len(seat_reservation_ids):
                raise serializers.ValidationError("Invalid seat reservations provided.")
            
            # Check if reservations are expired
            for reservation in reservations:
                if reservation.is_expired():
                    raise serializers.ValidationError(f"Seat reservation {reservation.seat.seat_identifier} has expired.")
            
            selected_seats = list(reservations)
            
            # Update number of seats to match reservations
            number_of_seats = len(selected_seats)
            validated_data['number_of_seats'] = number_of_seats
        
        # Calculate pricing (considering seat-specific pricing if seats selected)
        if selected_seats:
            # Calculate with seat-specific pricing
            total_amount = Decimal('0')
            seat_identifiers = []
            
            for reservation in selected_seats:
                seat_price = showtime.calculate_seat_price(reservation.seat)
                total_amount += seat_price
                seat_identifiers.append(reservation.seat.seat_identifier)
            
            base_price = total_amount / number_of_seats  # Average price
            validated_data['seat_numbers'] = seat_identifiers
        else:
            # Standard pricing calculation
            base_price = showtime.ticket_price
            total_amount = base_price * number_of_seats
        
        # Apply loyalty points discount (1 point = $0.10)
        points_discount = min(loyalty_points_used * Decimal('0.10'), total_amount * Decimal('0.50'))  # Max 50% discount
        
        # Validate customer has enough points
        if loyalty_points_used > customer.loyalty_points:
            raise serializers.ValidationError("Insufficient loyalty points.")
        
        total_amount = total_amount - points_discount
        
        # Create booking
        booking = Booking.objects.create(
            customer=customer,
            showtime=showtime,
            number_of_seats=number_of_seats,
            total_amount=total_amount,
            base_price_per_seat=base_price,
            discount_amount=points_discount,
            loyalty_points_used=loyalty_points_used,
            seat_numbers=validated_data.get('seat_numbers', []),
            special_requests=validated_data.get('special_requests', '')
        )
        
        # Confirm seat reservations if provided
        if selected_seats:
            for reservation in selected_seats:
                reservation.booking = booking
                reservation.confirm_reservation()
        
        # Deduct loyalty points if used
        if loyalty_points_used > 0:
            customer.loyalty_points -= loyalty_points_used
            customer.save()
        
        return booking


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for booking details.
    
    Provides comprehensive booking information for display.
    """
    customer = CustomerSerializer(read_only=True)
    showtime = ShowtimeSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'showtime', 'number_of_seats', 'total_amount',
            'status', 'booking_reference', 'seat_numbers', 'base_price_per_seat',
            'discount_amount', 'loyalty_points_used', 'is_active', 'can_cancel',
            'special_requests', 'created_at', 'confirmed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'booking_reference', 'total_amount', 'base_price_per_seat',
            'discount_amount', 'is_active', 'can_cancel', 'created_at', 
            'confirmed_at', 'cancelled_at'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for booking lists.
    
    Shows essential booking information without full related object details.
    """
    movie_title = serializers.CharField(source='showtime.movie.title', read_only=True)
    movie_poster = serializers.URLField(source='showtime.movie.poster_image', read_only=True)
    showtime_datetime = serializers.DateTimeField(source='showtime.datetime', read_only=True)
    theater_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'movie_title', 'movie_poster',
            'showtime_datetime', 'theater_info', 'number_of_seats',
            'total_amount', 'status', 'is_active', 'can_cancel', 'created_at'
        ]
    
    def get_theater_info(self, obj):
        """Get formatted theater information."""
        return f"{obj.showtime.theater_name} - Screen {obj.showtime.screen_number}"


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payment information.
    """
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_reference', 'amount', 'payment_method',
            'status', 'transaction_id', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'booking_reference', 'status', 'transaction_id',
            'created_at', 'processed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating payments.
    """
    class Meta:
        model = Payment
        fields = ['booking', 'payment_method']

    def create(self, validated_data):
        """Create payment with booking amount."""
        booking = validated_data['booking']
        
        # Validate booking belongs to current user
        request = self.context.get('request')
        if booking.customer.user != request.user:
            raise serializers.ValidationError("You can only pay for your own bookings.")
        
        # Validate booking is in pending status
        if booking.status != 'pending':
            raise serializers.ValidationError("This booking cannot be paid for.")
        
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            payment_method=validated_data['payment_method']
        )
        
        return payment


class BookingCancellationSerializer(serializers.Serializer):
    """
    Serializer for booking cancellation requests.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Optional reason for cancellation"
    )
    
    def validate(self, data):
        """Validate cancellation is allowed."""
        booking = self.context['booking']
        
        if not booking.can_cancel:
            raise serializers.ValidationError(
                "This booking cannot be cancelled. Cancellations are only allowed "
                "for confirmed bookings more than 2 hours before showtime."
            )
        
        return data