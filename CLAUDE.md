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
- `chat/` - AI chat functionality using OpenRouter with DeepSeek AI model

### API Design
- **Base URL**: `/api/v1/`
- **Documentation**: Swagger UI at `/api/v1/docs/` and ReDoc at `/api/v1/redoc/`
- **Authentication**: JWT-only authentication with refresh tokens via DRF Simple JWT
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
- `POST /api/v1/auth/register/` - Register new user account (returns JWT tokens)
- `POST /api/v1/auth/login/` - User login (returns JWT access and refresh tokens)
- `POST /api/v1/auth/logout/` - User logout (blacklists refresh token)
- `POST /api/v1/auth/token/refresh/` - Refresh JWT access token
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

**AI Chat:**
- `POST /api/v1/chat/ai-chat/` - Send message to AI assistant and get response (requires authentication)

### Key Features
- **Movie Management**: Filtering, searching, and ordering of movies and showtimes
- **User Authentication**: JWT-based authentication with access and refresh tokens
- **Customer Profiles**: Extended user profiles with contact info and loyalty points
- **Booking System**: Complete ticket booking with seat availability tracking
- **Payment Processing**: Mock payment system with transaction tracking
- **Real-time Availability**: Seat availability updates in real-time
- **Booking Cancellation**: Time-based cancellation rules (2+ hours before showtime)
- **Loyalty Program**: Points earned on purchases and redeemable for discounts
- **AI Chat Assistant**: OpenRouter-powered AI assistant using DeepSeek model for movie recommendations and cinema queries
- **Comprehensive API Documentation**: Extensive Swagger/OpenAPI documentation with examples
- **Admin Interface**: Full Django admin integration for all models

### Environment Setup
The project uses environment variables for sensitive configuration. Copy `.env.example` to `.env` and configure:

**Required Environment Variables:**
- `OPENROUTER_API_KEY` - Your OpenRouter API key for AI chat functionality
- `OPENROUTER_BASE_URL` - OpenRouter API base URL (default: https://openrouter.ai/api/v1)
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DATABASE_NAME` - PostgreSQL database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password
- `DATABASE_HOST` - Database host
- `DATABASE_PORT` - Database port

**Setup Steps:**
1. `cp .env.example .env`
2. Edit `.env` with your configuration values
3. Ensure `.env` is in `.gitignore` (already configured)

### Dependencies
- Django 4.2.23
- Django REST Framework 3.16.1
- Django REST Framework Simple JWT 5.3.0
- PostgreSQL (psycopg2-binary)
- django-filter for advanced filtering
- drf-yasg for API documentation
- python-decouple for environment variables
- openai for OpenRouter AI integration

### Settings Notes
- Database: PostgreSQL with hardcoded connection settings
- DEBUG=True (development mode)
- REST Framework configured with JWT-only auth and pagination
- JWT tokens: 60-minute access token, 7-day refresh token with rotation
- Comprehensive Swagger and ReDoc documentation settings with Bearer token auth