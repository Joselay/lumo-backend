"""
URL configuration for lumo_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Lumo Cinema API",
        default_version='v1',
        description="""
        # Lumo Cinema Ticket Booking System API
        
        Welcome to the **Lumo Cinema API** - a comprehensive REST API for managing cinema operations, movie listings, and ticket bookings.
        
        ## Features
        
        ### 🎬 Movies
        - **Movie Listings**: Browse active movies with filtering and search
        - **Movie Details**: Get comprehensive movie information
        - **Genre Management**: Organize movies by genres
        
        ### 🔍 Search & Filter
        - **Smart Search**: Search movies by title and description
        - **Genre Filtering**: Filter movies by single or multiple genres
        - **Date Filtering**: Find movies by release date
        - **Sorting**: Sort by release date, rating, or title
        
        ### 📄 Pagination
        - All list endpoints support pagination (20 items per page)
        - Navigation links provided for easy browsing
        
        ## Getting Started
        
        1. **Browse Movies**: Start with `/api/v1/movies/` to get active movies
        2. **Filter by Genre**: Use `/api/v1/movies/?genres=1` to filter by genre
        3. **Search**: Use `/api/v1/movies/?search=action` to search movies
        4. **Get Details**: Use `/api/v1/movies/{id}/` for specific movie details
        
        ## Base URL
        - **Development**: `http://localhost:8000`
        - **Production**: TBD
        
        ## Response Format
        All responses are in JSON format with consistent structure:
        - **Success**: Returns requested data with HTTP 200
        - **Error**: Returns error details with appropriate HTTP status codes
        - **Pagination**: List endpoints include `count`, `next`, `previous`, and `results`
        
        ## Rate Limiting
        Currently no rate limiting is applied (development mode).
        
        ---
        
        **Version**: 1.0.0  
        **Last Updated**: September 2025
        """,
        terms_of_service="https://www.lumocinema.com/terms/",
        contact=openapi.Contact(
            name="Lumo Cinema API Support",
            email="api-support@lumocinema.com",
            url="https://www.lumocinema.com/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/movies/', include('movies.urls')),
    re_path(r'^api/v1/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/v1/docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/v1/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
