# Step 2: Migrate data from old M2M table to new through model

from django.db import migrations


def migrate_movie_genre_data(apps, schema_editor):
    """Migrate existing movie-genre relationships to new through model."""
    Movie = apps.get_model('movies', 'Movie')
    Genre = apps.get_model('movies', 'Genre')
    MovieGenre = apps.get_model('movies', 'MovieGenre')
    db_alias = schema_editor.connection.alias

    # Copy all existing relationships to the new through model
    for movie in Movie.objects.using(db_alias).all():
        for genre in movie.genres.all():
            # Create the relationship in the new through model
            MovieGenre.objects.using(db_alias).create(
                movie=movie,
                genre=genre
            )


def reverse_migration(apps, schema_editor):
    """Remove all MovieGenre relationships."""
    MovieGenre = apps.get_model('movies', 'MovieGenre')
    db_alias = schema_editor.connection.alias
    MovieGenre.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0007_add_moviegenre_model'),
    ]

    operations = [
        migrations.RunPython(migrate_movie_genre_data, reverse_migration),
    ]