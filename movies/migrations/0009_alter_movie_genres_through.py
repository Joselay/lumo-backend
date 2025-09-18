# Step 3: Update Movie.genres field to use through model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0008_migrate_movie_genres_data'),
    ]

    operations = [
        # Remove the old M2M field and create a new one with through model
        migrations.RemoveField(
            model_name='movie',
            name='genres',
        ),
        migrations.AddField(
            model_name='movie',
            name='genres',
            field=models.ManyToManyField(
                related_name='movies',
                through='movies.MovieGenre',
                to='movies.genre'
            ),
        ),
    ]