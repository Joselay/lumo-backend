from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Booking, Payment
from .serializers import (
    BookingCreateSerializer, BookingSerializer, BookingListSerializer,
    PaymentSerializer, PaymentCreateSerializer, BookingCancellationSerializer
)


class BookingCreateView(generics.CreateAPIView):
    """
    API endpoint for creating new bookings.
    
    Creates a booking reservation for authenticated customers.
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create new booking",
        operation_description="""
        Create a new booking reservation for a showtime.
        
        **Features:**
        - Validates seat availability in real-time
        - Calculates total pricing with discounts
        - Applies loyalty points if specified
        - Generates unique booking reference
        
        **Booking Process:**
        1. Booking created in 'pending' status
        2. Customer has limited time to complete payment
        3. Payment confirms the booking
        
        **Authentication Required**
        """,
        responses={
            201: openapi.Response(
                description="Booking created successfully",
                schema=BookingSerializer(),
                examples={
                    "application/json": {
                        "id": "uuid-here",
                        "booking_reference": "BK789012ABCD",
                        "showtime": {"movie_title": "Avengers: Endgame", "datetime": "2024-12-25T19:00:00Z"},
                        "number_of_seats": 2,
                        "total_amount": "25.00",
                        "status": "pending",
                        "loyalty_points_used": 50
                    }
                }
            ),
            400: openapi.Response(
                description="Booking creation failed - validation errors",
                examples={
                    "application/json": {
                        "number_of_seats": ["Only 1 seats available for this showtime."],
                        "showtime": ["This showtime is no longer available."]
                    }
                }
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Bookings']
    )
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().create(request, *args, **kwargs)


class BookingListView(generics.ListAPIView):
    """
    API endpoint for listing customer's bookings.
    
    Shows all bookings for the authenticated customer.
    """
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(
            customer__user=self.request.user
        ).select_related('showtime__movie', 'customer')
    
    @swagger_auto_schema(
        operation_summary="List customer bookings",
        operation_description="""
        Retrieve all bookings for the authenticated customer.
        
        **Features:**
        - Shows booking history with movie and showtime details
        - Includes booking status and cancellation options
        - Ordered by creation date (newest first)
        
        **Authentication Required**
        """,
        responses={
            200: openapi.Response(
                description="Bookings retrieved successfully",
                schema=BookingListSerializer(many=True)
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Bookings']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BookingDetailView(generics.RetrieveAPIView):
    """
    API endpoint for viewing detailed booking information.
    
    Shows complete booking details for a specific booking.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(
            customer__user=self.request.user
        ).select_related('showtime__movie', 'customer')
    
    @swagger_auto_schema(
        operation_summary="Get booking details",
        operation_description="""
        Retrieve detailed information about a specific booking.
        
        **Features:**
        - Complete booking information
        - Showtime and movie details
        - Payment status and cancellation options
        
        **Authentication Required**
        """,
        responses={
            200: openapi.Response(
                description="Booking details retrieved successfully",
                schema=BookingSerializer()
            ),
            404: openapi.Response(description="Booking not found"),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Bookings']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_summary="Cancel booking",
    operation_description="""
    Cancel an existing booking reservation.
    
    **Cancellation Rules:**
    - Only confirmed bookings can be cancelled
    - Must be more than 2 hours before showtime
    - Refunds seats back to showtime availability
    
    **Authentication Required**
    """,
    request_body=BookingCancellationSerializer,
    responses={
        200: openapi.Response(
            description="Booking cancelled successfully",
            examples={
                "application/json": {
                    "message": "Booking cancelled successfully.",
                    "booking_reference": "BK789012ABCD",
                    "refund_amount": "25.00"
                }
            }
        ),
        400: openapi.Response(
            description="Cancellation not allowed",
            examples={
                "application/json": {
                    "error": "This booking cannot be cancelled. Cancellations are only allowed for confirmed bookings more than 2 hours before showtime."
                }
            }
        ),
        404: openapi.Response(description="Booking not found"),
        401: openapi.Response(description="Authentication required")
    },
    tags=['Bookings']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_booking(request, booking_id):
    """
    API endpoint for cancelling bookings.
    
    Allows customers to cancel their bookings within the allowed timeframe.
    """
    booking = get_object_or_404(
        Booking.objects.select_related('showtime', 'customer__user'),
        id=booking_id,
        customer__user=request.user
    )
    
    serializer = BookingCancellationSerializer(
        data=request.data,
        context={'booking': booking}
    )
    
    if serializer.is_valid():
        with transaction.atomic():
            if booking.cancel_booking():
                return Response({
                    'message': 'Booking cancelled successfully.',
                    'booking_reference': booking.booking_reference,
                    'refund_amount': str(booking.total_amount)
                })
            else:
                return Response(
                    {'error': 'Booking cancellation failed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentCreateView(generics.CreateAPIView):
    """
    API endpoint for creating payments for bookings.
    
    Processes payment for pending bookings.
    """
    serializer_class = PaymentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create payment for booking",
        operation_description="""
        Process payment for a pending booking.
        
        **Payment Process:**
        1. Creates payment record in 'pending' status
        2. In real implementation, would integrate with payment processor
        3. For now, immediately marks payment as completed
        4. Confirms the booking upon successful payment
        
        **Authentication Required**
        """,
        responses={
            201: openapi.Response(
                description="Payment created and processed successfully",
                schema=PaymentSerializer(),
                examples={
                    "application/json": {
                        "id": "payment-uuid",
                        "booking_reference": "BK789012ABCD",
                        "amount": "25.00",
                        "payment_method": "credit_card",
                        "status": "completed",
                        "transaction_id": "txn_123456789"
                    }
                }
            ),
            400: openapi.Response(
                description="Payment creation failed",
                examples={
                    "application/json": {
                        "booking": ["You can only pay for your own bookings."],
                        "non_field_errors": ["This booking cannot be paid for."]
                    }
                }
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Payments']
    )
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            payment = serializer.save()
            
            # For demo purposes, immediately process the payment
            # In production, this would integrate with actual payment processors
            import uuid
            transaction_id = f"txn_{str(uuid.uuid4())[:12]}"
            payment.mark_completed(transaction_id=transaction_id)
            
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )


class PaymentListView(generics.ListAPIView):
    """
    API endpoint for listing customer's payments.
    
    Shows payment history for the authenticated customer.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(
            booking__customer__user=self.request.user
        ).select_related('booking')
    
    @swagger_auto_schema(
        operation_summary="List customer payments",
        operation_description="""
        Retrieve payment history for the authenticated customer.
        
        **Features:**
        - Shows all payments with booking references
        - Includes payment status and transaction details
        - Ordered by creation date (newest first)
        
        **Authentication Required**
        """,
        responses={
            200: openapi.Response(
                description="Payments retrieved successfully",
                schema=PaymentSerializer(many=True)
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['Payments']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
