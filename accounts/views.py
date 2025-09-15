from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User
from .models import UserProfile, Customer
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    CustomerSerializer, CustomerUpdateSerializer, UserProfileSerializer
)
from .permissions import IsAdminUser
from movies.models import Movie
from bookings.models import Booking


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    Creates a new user account with associated customer profile.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register new user",
        operation_description="""
        Register a new user account with customer profile.
        
        **Features:**
        - Creates both User and Customer profile
        - Returns JWT access and refresh tokens
        - Validates email uniqueness
        - Requires password confirmation
        
        **Response:**
        Returns user information with JWT access and refresh tokens for immediate login.
        """,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe"
                        },
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "customer_profile": {
                            "id": "uuid-here",
                            "phone_number": "+1234567890",
                            "loyalty_points": 0
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Registration failed - validation errors",
                examples={
                    "application/json": {
                        "password": ["Passwords don't match."],
                        "email": ["A user with this email already exists."]
                    }
                }
            )
        },
        tags=['Authentication']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Return user data with tokens
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'customer_profile': CustomerSerializer(user.customer_profile).data
        }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_summary="User login",
    operation_description="""
    Authenticate user and return JWT tokens.
    
    **Features:**
    - Login with email and password only
    - Returns JWT access and refresh tokens
    - Includes customer profile information
    
    **Authentication:**
    Login requires email address and password.
    """,
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Response(
            description="Login successful",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe"
                    },
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "customer_profile": {
                        "id": "uuid-here",
                        "phone_number": "+1234567890",
                        "loyalty_points": 150
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Login failed - invalid credentials",
            examples={
                "application/json": {
                    "non_field_errors": ["Invalid credentials."]
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    API endpoint for user login.
    
    Authenticates user and returns token with profile information including role.
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        user = validated_data['user']
        
        # Ensure user profile exists
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Ensure customer profile exists for non-admin users
        if user.role == 'customer':
            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults={'phone_number': ''}
            )
            customer_data = CustomerSerializer(customer).data
        else:
            customer_data = None
        
        return Response({
            'user': validated_data['user_info'],
            'access_token': validated_data['tokens']['access'],
            'refresh_token': validated_data['tokens']['refresh'],
            'customer_profile': customer_data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="User logout",
    operation_description="""
    Logout current user by blacklisting their refresh token.
    
    **Authentication Required**
    """,
    responses={
        200: openapi.Response(
            description="Logout successful",
            examples={
                "application/json": {
                    "message": "Successfully logged out."
                }
            }
        ),
        401: openapi.Response(description="Authentication required")
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    API endpoint for user logout.
    
    Blacklists the user's refresh token to invalidate the JWT.
    """
    try:
        # Get the refresh token from the request
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out.'})
    except Exception:
        return Response({'message': 'Successfully logged out.'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating user profile.
    
    Allows users to view and update their profile information.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="""
        Retrieve current user's profile information including customer details.
        
        **Authentication Required**
        """,
        responses={
            200: openapi.Response(
                description="Profile retrieved successfully",
                schema=UserProfileSerializer()
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for managing customer-specific profile information.
    
    Allows customers to update their contact and preference information.
    """
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        customer, created = Customer.objects.get_or_create(
            user=self.request.user,
            defaults={'phone_number': ''}
        )
        return customer
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomerUpdateSerializer
        return CustomerSerializer
    
    @swagger_auto_schema(
        operation_summary="Get customer profile",
        operation_description="""
        Retrieve customer-specific profile information.
        
        **Authentication Required**
        """,
        responses={
            200: openapi.Response(
                description="Customer profile retrieved successfully",
                schema=CustomerSerializer()
            ),
            401: openapi.Response(description="Authentication required")
        },
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update customer profile",
        operation_description="""
        Update customer profile information including contact details and preferences.
        
        **Authentication Required**
        """,
        request_body=CustomerUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=CustomerSerializer()
            ),
            400: openapi.Response(description="Validation errors"),
            401: openapi.Response(description="Authentication required")
        },
        tags=['User Profile']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


# Admin Dashboard Views

class AdminDashboardView(APIView):
    """
    Admin dashboard API endpoint providing system statistics and overview.
    
    Returns summary statistics for administrators.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get admin dashboard statistics",
        operation_description="""
        Get overview statistics for admin dashboard.
        
        **Admin Access Required**
        Only users with admin role can access this endpoint.
        """,
        responses={
            200: openapi.Response(
                description="Dashboard statistics retrieved successfully",
                examples={
                    "application/json": {
                        "total_users": 150,
                        "total_customers": 140,
                        "total_admins": 10,
                        "total_movies": 25,
                        "active_movies": 20,
                        "total_bookings": 450,
                        "recent_registrations": 12
                    }
                }
            ),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        },
        tags=['Admin Dashboard']
    )
    def get(self, request):
        """Get dashboard statistics for admin users."""
        try:
            # User statistics
            total_users = User.objects.count()
            
            # Count users by role using UserProfile
            customer_profiles = UserProfile.objects.filter(role='customer').count()
            admin_profiles = UserProfile.objects.filter(role='admin').count()
            
            # Movie statistics  
            total_movies = Movie.objects.count()
            active_movies = Movie.objects.filter(is_active=True).count()
            
            # Booking statistics
            try:
                total_bookings = Booking.objects.count()
            except:
                total_bookings = 0
            
            # Recent registrations (last 7 days)
            from django.utils import timezone
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            recent_registrations = User.objects.filter(date_joined__gte=week_ago).count()
            
            return Response({
                'total_users': total_users,
                'total_customers': customer_profiles,
                'total_admins': admin_profiles,
                'total_movies': total_movies,
                'active_movies': active_movies,
                'total_bookings': total_bookings,
                'recent_registrations': recent_registrations
            })
        except Exception as e:
            import traceback
            print(f"Dashboard error: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': f'Failed to retrieve dashboard statistics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminUsersListView(generics.ListAPIView):
    """
    Admin endpoint to list all users with filtering and search capabilities.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Get all users with optional filtering."""
        queryset = User.objects.all().select_related().prefetch_related('customer_profile')
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Search by username, email, or name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')
    
    @swagger_auto_schema(
        operation_summary="List all users (Admin only)",
        operation_description="""
        Get paginated list of all users in the system.
        
        **Admin Access Required**
        
        **Query Parameters:**
        - `role`: Filter by user role (customer, admin)
        - `search`: Search by username, email, or name
        """,
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by role", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search users", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(description="Users list retrieved successfully"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        },
        tags=['Admin Dashboard']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin endpoint to manage individual user accounts.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().select_related().prefetch_related('customer_profile')
    
    @swagger_auto_schema(
        operation_summary="Get user details (Admin only)",
        operation_description="Retrieve detailed information for a specific user.",
        responses={
            200: openapi.Response(description="User details retrieved successfully"),
            404: openapi.Response(description="User not found"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        },
        tags=['Admin Dashboard']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update user (Admin only)",
        operation_description="Update user information (admin can modify any user).",
        responses={
            200: openapi.Response(description="User updated successfully"),
            400: openapi.Response(description="Validation errors"),
            404: openapi.Response(description="User not found"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        },
        tags=['Admin Dashboard']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete user (Admin only)",
        operation_description="Delete a user account (use with caution).",
        responses={
            204: openapi.Response(description="User deleted successfully"),
            404: openapi.Response(description="User not found"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        },
        tags=['Admin Dashboard']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
