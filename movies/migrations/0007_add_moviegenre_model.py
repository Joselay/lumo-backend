# Step 1: Create MovieGenre through model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0006_alter_showtime_ticket_price_seatlayout_seat_and_more'),
    ]

    operations = [
        # Create the new through model first
        migrations.CreateModel(
            name='MovieGenre',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movies.genre')),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='movies.movie')),
            ],
            options={
                'ordering': ['movie__title', 'genre__name'],
                'unique_together': {('movie', 'genre')},
            },
        ),
    ]