import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Booking, Payment
from .serializers import (
    BookingCreateSerializer, BookingSerializer, BookingListSerializer,
    PaymentSerializer, PaymentCreateSerializer, BookingCancellationSerializer
)
from accounts.models import Customer
from movies.models import Movie, Genre, Showtime, Theater, SeatLayout, Seat, SeatReservation

User = get_user_model()


class BookingModelTest(TestCase):
    """Test cases for the Booking model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number='+1-555-0123',
            date_of_birth=date(1990, 1, 1),
            address='123 Test Street',
            city='Test City',
            state='TS',
            zip_code='12345',
            loyalty_points=100
        )
        
        self.theater = Theater.objects.create(
            name="Test Theater",
            address="123 Theater Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0456"
        )
        
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="A test movie.",
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
            total_seats=100,
            available_seats=95,
            ticket_price=Decimal('15.99')
        )
        
        self.booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=2,
            total_amount=Decimal('31.98'),
            base_price_per_seat=Decimal('15.99'),
            discount_amount=Decimal('0.00'),
            loyalty_points_used=0,
            status='pending'
        )
    
    def test_booking_creation(self):
        """Test basic booking creation."""
        self.assertEqual(self.booking.customer, self.customer)
        self.assertEqual(self.booking.showtime, self.showtime)
        self.assertEqual(self.booking.number_of_seats, 2)
        self.assertEqual(self.booking.total_amount, Decimal('31.98'))
        self.assertEqual(self.booking.status, 'pending')
        self.assertIsNotNone(self.booking.booking_reference)
        self.assertIsInstance(self.booking.id, uuid.UUID)
    
    def test_booking_str_method(self):
        """Test the string representation of Booking."""
        expected = f"Booking {self.booking.booking_reference} - Test User - Test Movie"
        self.assertEqual(str(self.booking), expected)
    
    def test_booking_reference_generation(self):
        """Test that booking reference is automatically generated."""
        self.assertTrue(self.booking.booking_reference.startswith('BK'))
        self.assertEqual(len(self.booking.booking_reference), 12)
    
    def test_is_active_property(self):
        """Test the is_active property logic."""
        # Pending booking should be active
        self.booking.status = 'pending'
        self.assertTrue(self.booking.is_active)
        
        # Confirmed booking should be active
        self.booking.status = 'confirmed'
        self.assertTrue(self.booking.is_active)
        
        # Cancelled booking should not be active
        self.booking.status = 'cancelled'
        self.assertFalse(self.booking.is_active)
        
        # Refunded booking should not be active
        self.booking.status = 'refunded'
        self.assertFalse(self.booking.is_active)
    
    def test_can_cancel_property(self):
        """Test the can_cancel property logic."""
        # Confirmed booking more than 2 hours before showtime should be cancellable
        self.booking.status = 'confirmed'
        self.booking.confirmed_at = timezone.now()
        self.assertTrue(self.booking.can_cancel)
        
        # Pending booking should not be cancellable
        self.booking.status = 'pending'
        self.assertFalse(self.booking.can_cancel)
        
        # Already cancelled booking should not be cancellable
        self.booking.status = 'cancelled'
        self.assertFalse(self.booking.can_cancel)
        
        # Booking too close to showtime should not be cancellable
        near_future = timezone.now() + timedelta(minutes=30)
        self.showtime.datetime = near_future
        self.showtime.save()
        self.booking.status = 'confirmed'
        self.assertFalse(self.booking.can_cancel)
    
    def test_confirm_booking_method(self):
        """Test the confirm_booking method."""
        self.booking.confirm_booking()
        
        self.assertEqual(self.booking.status, 'confirmed')
        self.assertIsNotNone(self.booking.confirmed_at)
    
    def test_cancel_booking_method(self):
        """Test the cancel_booking method."""
        # First confirm the booking
        self.booking.confirm_booking()
        
        # Then cancel it
        reason = "Test cancellation"
        self.booking.cancel_booking(reason)
        
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertIsNotNone(self.booking.cancelled_at)


class PaymentModelTest(TestCase):
    """Test cases for the Payment model."""
    
    def setUp(self):
        # Set up user and customer
        self.user = User.objects.create_user(
            username='paymentuser',
            email='payment@example.com',
            password='testpassword123'
        )
        
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number='+1-555-0789'
        )
        
        # Set up movie/showtime/booking
        self.theater = Theater.objects.create(
            name="Payment Test Theater",
            address="456 Payment Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0789"
        )
        
        self.movie = Movie.objects.create(
            title="Payment Test Movie",
            description="A test movie for payments.",
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
            total_seats=50,
            available_seats=48,
            ticket_price=Decimal('12.50')
        )
        
        self.booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=2,
            total_amount=Decimal('25.00'),
            base_price_per_seat=Decimal('12.50')
        )
        
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('25.00'),
            payment_method='credit_card'
        )
    
    def test_payment_creation(self):
        """Test basic payment creation."""
        self.assertEqual(self.payment.booking, self.booking)
        self.assertEqual(self.payment.amount, Decimal('25.00'))
        self.assertEqual(self.payment.payment_method, 'credit_card')
        self.assertEqual(self.payment.status, 'pending')
        self.assertIsNotNone(self.payment.transaction_id)
        self.assertIsInstance(self.payment.id, uuid.UUID)
    
    def test_payment_str_method(self):
        """Test the string representation of Payment."""
        expected = f"Payment {self.payment.transaction_id} - $25.00 - Pending"
        self.assertEqual(str(self.payment), expected)
    
    def test_transaction_id_generation(self):
        """Test that transaction ID is automatically generated."""
        self.assertTrue(self.payment.transaction_id.startswith('TXN'))
        self.assertEqual(len(self.payment.transaction_id), 15)
    
    def test_process_payment_method(self):
        """Test the process_payment method."""
        result = self.payment.process_payment()
        
        self.assertTrue(result)
        self.assertEqual(self.payment.status, 'completed')
        self.assertIsNotNone(self.payment.processed_at)
    
    def test_fail_payment_method(self):
        """Test the fail_payment method."""
        self.payment.fail_payment()
        
        self.assertEqual(self.payment.status, 'failed')


class BookingSeatIntegrationTest(TestCase):
    """Test cases for booking integration with seat selection."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='seatuser',
            email='seat@example.com',
            password='testpassword123'
        )
        
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number='+1-555-0333',
            loyalty_points=50
        )
        
        self.theater = Theater.objects.create(
            name="Seat Integration Theater",
            address="789 Seat Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0333"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="Test Layout",
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
            title="Seat Integration Movie",
            description="Test movie for seat integration.",
            duration=110,
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
            ticket_price=Decimal('10.00'),
            seat_layout=self.seat_layout
        )
        
        # Create some seat reservations
        self.reservations = []
        for i in range(3):  # Reserve A1, A2, A3
            reservation = SeatReservation.objects.create(
                showtime=self.showtime,
                seat=self.seats[i],
                status='reserved',
                expires_at=timezone.now() + timedelta(minutes=15)
            )
            self.reservations.append(reservation)
    
    def test_booking_with_seat_reservations(self):
        """Test creating booking with specific seat reservations."""
        # Create booking with seat reservations
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=3,
            total_amount=Decimal('45.00'),  # 3 premium seats at $15 each (10 * 1.5)
            base_price_per_seat=Decimal('15.00'),
            seat_numbers=['A1', 'A2', 'A3']
        )
        
        # Link reservations to booking
        for reservation in self.reservations:
            reservation.booking = booking
            reservation.confirm_reservation()
        
        # Verify booking creation
        self.assertEqual(booking.number_of_seats, 3)
        self.assertEqual(booking.seat_numbers, ['A1', 'A2', 'A3'])
        
        # Verify reservations are confirmed
        for reservation in self.reservations:
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, 'confirmed')
            self.assertEqual(reservation.booking, booking)
    
    def test_booking_price_calculation_with_seats(self):
        """Test price calculation with mixed seat types."""
        # Create reservations for mixed seats (1 premium A seat, 1 standard B seat)
        # Using different seats than those created in setUp
        mixed_reservations = [
            SeatReservation.objects.create(
                showtime=self.showtime,
                seat=self.seats[3],  # A4 - premium (avoiding A1-A3 from setUp)
                status='reserved',
                expires_at=timezone.now() + timedelta(minutes=15)
            ),
            SeatReservation.objects.create(
                showtime=self.showtime,
                seat=self.seats[6],  # B1 - standard
                status='reserved',
                expires_at=timezone.now() + timedelta(minutes=15)
            )
        ]
        
        # Calculate expected total: (10 * 1.5) + (10 * 1.0) = 15 + 10 = 25
        expected_total = Decimal('25.00')
        expected_average = expected_total / 2  # 12.50
        
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=2,
            total_amount=expected_total,
            base_price_per_seat=expected_average,
            seat_numbers=['A4', 'B1']
        )
        
        # Link reservations to booking
        for reservation in mixed_reservations:
            reservation.booking = booking
            reservation.confirm_reservation()
        
        self.assertEqual(booking.total_amount, expected_total)
        self.assertEqual(booking.base_price_per_seat, expected_average)


class BookingSerializerTest(TestCase):
    """Test cases for Booking serializers."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='serializeruser',
            email='serializer@example.com',
            password='testpassword123',
            first_name='Serializer',
            last_name='User'
        )
        
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number='+1-555-0111',
            loyalty_points=25
        )
        
        self.theater = Theater.objects.create(
            name="Serializer Test Theater",
            address="111 Serializer Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0111"
        )
        
        self.movie = Movie.objects.create(
            title="Serializer Test Movie",
            description="Test movie for serializers.",
            duration=95,
            release_date=date.today(),
            is_active=True
        )
        
        future_time = timezone.now() + timedelta(days=1)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time,
            screen_number=1,
            total_seats=75,
            available_seats=73,
            ticket_price=Decimal('14.00')
        )
    
    def test_booking_serialization(self):
        """Test BookingSerializer output."""
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=2,
            total_amount=Decimal('28.00'),
            base_price_per_seat=Decimal('14.00'),
            status='confirmed'
        )
        booking.confirm_booking()
        
        serializer = BookingSerializer(booking)
        data = serializer.data
        
        self.assertEqual(data['number_of_seats'], 2)
        self.assertEqual(data['total_amount'], '28.00')
        self.assertEqual(data['status'], 'confirmed')
        self.assertTrue(data['is_active'])
        self.assertTrue(data['can_cancel'])
        self.assertIn('customer', data)
        self.assertIn('showtime', data)
        self.assertEqual(data['customer']['user']['first_name'], 'Serializer')
    
    def test_booking_list_serialization(self):
        """Test BookingListSerializer output."""
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=1,
            total_amount=Decimal('14.00'),
            base_price_per_seat=Decimal('14.00')
        )
        
        serializer = BookingListSerializer(booking)
        data = serializer.data
        
        self.assertEqual(data['movie_title'], 'Serializer Test Movie')
        self.assertEqual(data['theater_info'], 'Serializer Test Theater - Screen 1')
        self.assertEqual(data['number_of_seats'], 1)
        self.assertEqual(data['total_amount'], '14.00')
        self.assertIn('booking_reference', data)
        self.assertIn('showtime_datetime', data)


class BookingAPITest(APITestCase):
    """Test cases for Booking API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpassword123',
            first_name='API',
            last_name='User'
        )
        
        self.customer = Customer.objects.create(
            user=self.user,
            phone_number='+1-555-0999',
            loyalty_points=75
        )
        
        # Create token for authentication
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.theater = Theater.objects.create(
            name="API Test Theater",
            address="999 API Street",
            city="Test City",
            state="TS",
            zip_code="12345",
            phone_number="+1-555-0999"
        )
        
        self.seat_layout = SeatLayout.objects.create(
            theater=self.theater,
            screen_number=1,
            name="API Layout",
            total_rows=2,
            total_seats=12,
            row_configuration={"A": 6, "B": 6}
        )
        
        # Create seats
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
            duration=105,
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
            ticket_price=Decimal('11.00'),
            seat_layout=self.seat_layout
        )
    
    def test_booking_creation_without_seats(self):
        """Test creating booking without specific seat selection."""
        url = reverse('bookings:booking-create')
        data = {
            'showtime': str(self.showtime.id),
            'number_of_seats': 2,
            'special_requests': 'Aisle seats preferred',
            'loyalty_points_used': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        
        booking = Booking.objects.first()
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.number_of_seats, 2)
        self.assertEqual(booking.loyalty_points_used, 10)
        self.assertEqual(booking.status, 'pending')
        
        # Check loyalty points were deducted
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.loyalty_points, 65)  # 75 - 10
    
    def test_booking_creation_with_seats(self):
        """Test creating booking with specific seat reservations."""
        # First create seat reservations
        reservations = []
        for i in range(2):  # A1, A2
            reservation = SeatReservation.objects.create(
                showtime=self.showtime,
                seat=self.seats[i],
                status='reserved',
                expires_at=timezone.now() + timedelta(minutes=15)
            )
            reservations.append(reservation)
        
        url = reverse('bookings:booking-create')
        data = {
            'showtime': str(self.showtime.id),
            'number_of_seats': 2,
            'seat_reservation_ids': [str(r.id) for r in reservations],
            'loyalty_points_used': 0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        
        booking = Booking.objects.first()
        self.assertEqual(booking.number_of_seats, 2)
        self.assertEqual(booking.seat_numbers, ['A1', 'A2'])
        
        # Check reservations were confirmed
        for reservation in reservations:
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, 'confirmed')
            self.assertEqual(reservation.booking, booking)
    
    def test_booking_creation_validation_errors(self):
        """Test booking creation validation errors."""
        url = reverse('bookings:booking-create')
        
        # Test with too many seats
        data = {
            'showtime': str(self.showtime.id),
            'number_of_seats': 15  # Too many
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with insufficient loyalty points
        data = {
            'showtime': str(self.showtime.id),
            'number_of_seats': 2,
            'loyalty_points_used': 100  # More than customer has (75)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with expired seat reservation
        expired_reservation = SeatReservation.objects.create(
            showtime=self.showtime,
            seat=self.seats[0],
            status='reserved',
            expires_at=timezone.now() - timedelta(minutes=5)  # Expired
        )
        
        data = {
            'showtime': str(self.showtime.id),
            'number_of_seats': 1,
            'seat_reservation_ids': [str(expired_reservation.id)]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_booking_list_endpoint(self):
        """Test the booking list API endpoint."""
        # Create a couple of bookings
        booking1 = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=1,
            total_amount=Decimal('11.00'),
            base_price_per_seat=Decimal('11.00')
        )
        
        # Create another showtime and booking
        future_time2 = timezone.now() + timedelta(days=2)
        showtime2 = Showtime.objects.create(
            movie=self.movie,
            theater=self.theater,
            datetime=future_time2,
            screen_number=2,
            total_seats=20,
            available_seats=20,
            ticket_price=Decimal('13.00')
        )
        
        booking2 = Booking.objects.create(
            customer=self.customer,
            showtime=showtime2,
            number_of_seats=2,
            total_amount=Decimal('26.00'),
            base_price_per_seat=Decimal('13.00')
        )
        
        url = reverse('bookings:booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        results = response.data['results']
        self.assertEqual(len(results), 2)
        
        # Should be ordered by creation date (newest first)
        self.assertEqual(results[0]['id'], str(booking2.id))
        self.assertEqual(results[1]['id'], str(booking1.id))
    
    def test_booking_detail_endpoint(self):
        """Test the booking detail API endpoint."""
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=3,
            total_amount=Decimal('33.00'),
            base_price_per_seat=Decimal('11.00'),
            status='confirmed'
        )
        booking.confirm_booking()
        
        url = reverse('bookings:booking-detail', kwargs={'pk': str(booking.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(booking.id))
        self.assertEqual(response.data['number_of_seats'], 3)
        self.assertEqual(response.data['status'], 'confirmed')
        self.assertIn('customer', response.data)
        self.assertIn('showtime', response.data)
    
    def test_booking_cancellation_endpoint(self):
        """Test the booking cancellation API endpoint."""
        booking = Booking.objects.create(
            customer=self.customer,
            showtime=self.showtime,
            number_of_seats=2,
            total_amount=Decimal('22.00'),
            base_price_per_seat=Decimal('11.00'),
            status='confirmed'
        )
        booking.confirm_booking()
        
        url = reverse('bookings:booking-cancel', kwargs={'booking_id': str(booking.id)})
        data = {
            'reason': 'Plans changed'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('bookings:booking-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        url = reverse('bookings:booking-create')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)