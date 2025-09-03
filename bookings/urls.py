from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking management endpoints
    path('', views.BookingListView.as_view(), name='booking-list'),
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),
    path('<uuid:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('<uuid:booking_id>/cancel/', views.cancel_booking, name='booking-cancel'),
    
    # Payment endpoints
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
]