from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Customer


class UserProfileInline(admin.StackedInline):
    """Inline user profile in User admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Role Profile'

class CustomerInline(admin.StackedInline):
    """Inline customer profile in User admin."""
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer Profile'


class CustomUserAdmin(UserAdmin):
    """Extended User admin with user profile and customer profile."""
    inlines = (UserProfileInline, CustomerInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'get_loyalty_points')
    list_filter = UserAdmin.list_filter + ('customer_profile__preferred_language',)
    
    def get_role(self, obj):
        """Display user role in user list."""
        try:
            return obj.user_profile.role
        except UserProfile.DoesNotExist:
            return 'customer'
    get_role.short_description = 'Role'
    
    def get_loyalty_points(self, obj):
        """Display loyalty points in user list."""
        try:
            return obj.customer_profile.loyalty_points
        except Customer.DoesNotExist:
            return 0
    get_loyalty_points.short_description = 'Loyalty Points'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model."""
    list_display = ('full_name', 'email', 'phone_number', 'loyalty_points', 'preferred_language', 'created_at')
    list_filter = ('preferred_language', 'receive_marketing_emails', 'receive_booking_notifications', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'date_of_birth')
        }),
        ('Preferences', {
            'fields': ('preferred_language', 'receive_marketing_emails', 'receive_booking_notifications')
        }),
        ('Loyalty Program', {
            'fields': ('loyalty_points',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)


# Unregister the original User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
