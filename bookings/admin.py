from django.contrib import admin
from django.utils.html import format_html
from .models import Booking, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model."""
    list_display = (
        'booking_reference', 'customer_name', 'movie_title', 'showtime_info',
        'number_of_seats', 'total_amount', 'status_badge', 'created_at'
    )
    list_filter = ('status', 'created_at', 'showtime__movie__title', 'showtime__theater__name')
    search_fields = (
        'booking_reference', 'customer__user__username', 'customer__user__email',
        'showtime__movie__title', 'customer__user__first_name', 'customer__user__last_name'
    )
    readonly_fields = (
        'id', 'booking_reference', 'is_active', 'can_cancel',
        'created_at', 'updated_at', 'confirmed_at', 'cancelled_at'
    )
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'customer', 'showtime', 'status')
        }),
        ('Seat Details', {
            'fields': ('number_of_seats', 'seat_numbers', 'special_requests')
        }),
        ('Pricing', {
            'fields': ('base_price_per_seat', 'discount_amount', 'loyalty_points_used', 'total_amount')
        }),
        ('Status Information', {
            'fields': ('is_active', 'can_cancel')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer__user', 'showtime__movie', 'showtime__theater'
        )
    
    def customer_name(self, obj):
        """Display customer's full name."""
        return obj.customer.full_name
    customer_name.short_description = 'Customer'
    
    def movie_title(self, obj):
        """Display movie title."""
        return obj.showtime.movie.title
    movie_title.short_description = 'Movie'
    
    def showtime_info(self, obj):
        """Display formatted showtime information."""
        return f"{obj.showtime.datetime.strftime('%Y-%m-%d %H:%M')} - {obj.showtime.theater.name}"
    showtime_info.short_description = 'Showtime'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'cancelled': 'red',
            'refunded': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


class PaymentInline(admin.StackedInline):
    """Inline payment in booking admin."""
    model = Payment
    extra = 0
    readonly_fields = ('id', 'created_at', 'processed_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    list_display = (
        'id', 'booking_reference', 'customer_name', 'amount',
        'payment_method', 'status_badge', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'booking__booking_reference', 'transaction_id',
        'booking__customer__user__username', 'booking__customer__user__email'
    )
    readonly_fields = ('id', 'created_at', 'processed_at', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'amount', 'payment_method', 'status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'processor_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'booking__customer__user'
        )
    
    def booking_reference(self, obj):
        """Display booking reference."""
        return obj.booking.booking_reference
    booking_reference.short_description = 'Booking Reference'
    
    def customer_name(self, obj):
        """Display customer's name."""
        return obj.booking.customer.full_name
    customer_name.short_description = 'Customer'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'purple'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# Add payment inline to booking admin
BookingAdmin.inlines = [PaymentInline]
