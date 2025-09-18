#!/bin/bash

# Database reset and sync script for Lumo Cinema
# This script will:
# 1. Drop and recreate the lumo database
# 2. Run Django migrations
# 3. Sync movie data from TMDB

set -e  # Exit on any error

echo "🎬 Starting Lumo Cinema database reset and sync..."

# Database configuration
DB_NAME="lumo"
DB_USER="postgres"
DB_PASSWORD="jose"
DB_HOST="localhost"
DB_PORT="5432"

echo "📊 Terminating active connections to database '$DB_NAME'..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

echo "📊 Dropping existing database '$DB_NAME'..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "📊 Creating new database '$DB_NAME'..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

echo "🔄 Running Django migrations..."
python manage.py migrate

echo "🎭 Syncing movie data from TMDB (10 movies)..."
python manage.py sync_tmdb_movies --pages 1

echo "✅ Database reset and sync completed successfully!"
echo "🚀 You can now start the server with: python manage.py runserver"