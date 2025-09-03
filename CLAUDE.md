# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Django Management Commands
- `python manage.py runserver` - Start the development server
- `python manage.py makemigrations` - Create new database migrations
- `python manage.py migrate` - Apply database migrations
- `python manage.py collectstatic` - Collect static files for production
- `python manage.py createsuperuser` - Create admin user
- `python manage.py populate_sample_data` - Populate database with sample movies and genres
- `python manage.py populate_sample_data --clear` - Clear existing data and populate with samples

### Database Setup
- Ensure PostgreSQL is running locally
- Database name: `lumo`
- Default user: `postgres` with no password
- Port: `5432`

### Testing
- `python manage.py test` - Run all tests
- `python manage.py test movies` - Run tests for movies app only

## Architecture Overview

### Project Structure
This is a Django REST API for a cinema ticket booking system called "Lumo Cinema". The project follows Django's standard app-based architecture.

**Main Components:**
- `lumo_api/` - Main Django project configuration
- `movies/` - Django app handling movie and genre management
- `accounts/` - User management and authentication
- `bookings/` - Booking and payment management

### API Design
- **Base URL**: `/api/v1/`
- **Documentation**: Swagger UI at `/api/v1/docs/` and ReDoc at `/api/v1/redoc/`
- **Authentication**: Token-based and Session authentication via DRF
- **Pagination**: 20 items per page for list endpoints

### Key Models
- `Movie` - Core movie entity with fields: title, description, duration, release_date, rating, poster_image, trailer_url, genres (M2M), is_active
- `Genre` - Movie genres with simple name field
- `Showtime` - Movie screenings with scheduling, theater info, and seat availability
- `Customer` - Extended user profiles with contact info and loyalty points
- `Booking` - Ticket reservations linking customers to showtimes
- `Payment` - Payment processing and transaction tracking

### API Endpoints

**Movies & Showtimes:**
- `GET /api/v1/movies/genres/` - List all genres
- `GET /api/v1/movies/` - List active movies with filtering, searching, and ordering
- `GET /api/v1/movies/{id}/` - Get detailed movie information
- `GET /api/v1/movies/showtimes/` - List all showtimes
- `GET /api/v1/movies/showtimes/{id}/` - Get detailed showtime information
- `GET /api/v1/movies/{id}/showtimes/` - Get showtimes for a specific movie

**Authentication:**
- `POST /api/v1/auth/register/` - Register new user account
- `POST /api/v1/auth/login/` - User login (returns token)
- `POST /api/v1/auth/logout/` - User logout (invalidates token)
- `GET /api/v1/auth/profile/` - Get user profile
- `PUT/PATCH /api/v1/auth/customer-profile/` - Update customer profile

**Bookings:**
- `GET /api/v1/bookings/` - List customer's bookings
- `POST /api/v1/bookings/create/` - Create new booking
- `GET /api/v1/bookings/{id}/` - Get booking details
- `POST /api/v1/bookings/{id}/cancel/` - Cancel booking

**Payments:**
- `GET /api/v1/bookings/payments/` - List customer's payments
- `POST /api/v1/bookings/payments/create/` - Process payment for booking

### Key Features
- **Movie Management**: Filtering, searching, and ordering of movies and showtimes
- **User Authentication**: Token-based authentication with user registration/login
- **Customer Profiles**: Extended user profiles with contact info and loyalty points
- **Booking System**: Complete ticket booking with seat availability tracking
- **Payment Processing**: Mock payment system with transaction tracking
- **Real-time Availability**: Seat availability updates in real-time
- **Booking Cancellation**: Time-based cancellation rules (2+ hours before showtime)
- **Loyalty Program**: Points earned on purchases and redeemable for discounts
- **Comprehensive API Documentation**: Extensive Swagger/OpenAPI documentation with examples
- **Admin Interface**: Full Django admin integration for all models

### Dependencies
- Django 4.2.23
- Django REST Framework 3.16.1
- PostgreSQL (psycopg2-binary)
- django-filter for advanced filtering
- drf-yasg for API documentation
- python-decouple for environment variables (not currently used)

### Settings Notes
- Database: PostgreSQL with hardcoded connection settings
- DEBUG=True (development mode)
- REST Framework configured with Token + Session auth and pagination
- Comprehensive Swagger and ReDoc documentation settings