from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Customer


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Creates both User and Customer profile in a single request.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    phone_number = serializers.CharField(write_only=True, help_text="Customer's phone number")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'phone_number']

    def validate(self, data):
        """Validate password confirmation and email uniqueness."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return data

    def create(self, validated_data):
        """Create user and associated customer profile."""
        phone_number = validated_data.pop('phone_number')
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        
        # Create customer profile
        Customer.objects.create(
            user=user,
            phone_number=phone_number
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    
    Login with email and password only.
    """
    email = serializers.EmailField(help_text="Email address")
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """Authenticate user with email and password."""
        email = data['email']
        password = data['password']
        
        # Find user by email and authenticate with username
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        data['user'] = user
        return data


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile information.
    """
    full_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'username', 'full_name', 'email', 'phone_number',
            'date_of_birth', 'preferred_language', 'receive_marketing_emails',
            'receive_booking_notifications', 'loyalty_points', 'created_at'
        ]
        read_only_fields = ['id', 'loyalty_points', 'created_at']


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating customer profile.
    
    Allows updating both User and Customer fields.
    """
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'preferred_language', 'receive_marketing_emails',
            'receive_booking_notifications'
        ]

    def validate_email(self, value):
        """Ensure email uniqueness excluding current user."""
        user = self.instance.user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        """Update both User and Customer models."""
        # Extract user data
        user_data = validated_data.pop('user', {})
        
        # Update user fields
        for field, value in user_data.items():
            setattr(instance.user, field, value)
        instance.user.save()
        
        # Update customer fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Combined serializer for user profile including customer information.
    """
    customer_profile = CustomerSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'customer_profile']
        read_only_fields = ['id', 'username', 'date_joined']