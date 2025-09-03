from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Customer
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    CustomerSerializer, CustomerUpdateSerializer, UserProfileSerializer
)


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
        - Returns authentication token
        - Validates email uniqueness
        - Requires password confirmation
        
        **Response:**
        Returns user information and authentication token for immediate login.
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
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
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
        
        # Create authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        # Return user data with token
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key,
            'customer_profile': CustomerSerializer(user.customer_profile).data
        }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_summary="User login",
    operation_description="""
    Authenticate user and return access token.
    
    **Features:**
    - Login with username or email
    - Returns authentication token
    - Includes customer profile information
    
    **Authentication:**
    Supports login with either username or email address.
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
                    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
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
    
    Authenticates user and returns token with profile information.
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Get or create authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        # Ensure customer profile exists
        customer, created = Customer.objects.get_or_create(
            user=user,
            defaults={'phone_number': ''}
        )
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key,
            'customer_profile': CustomerSerializer(customer).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="User logout",
    operation_description="""
    Logout current user by deleting their authentication token.
    
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
    
    Deletes the user's authentication token.
    """
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out.'})
    except:
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
