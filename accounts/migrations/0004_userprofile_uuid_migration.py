# Generated manually to convert UserProfile ID from BigInt to UUID

from django.db import migrations, models
import uuid


def migrate_to_uuid(apps, schema_editor):
    """Backup data, drop table, recreate with UUID, restore data with new UUIDs."""
    UserProfile = apps.get_model('accounts', 'UserProfile')
    db_alias = schema_editor.connection.alias

    # Backup existing data
    backup_data = []
    for profile in UserProfile.objects.using(db_alias).all():
        backup_data.append({
            'user_id': profile.user_id,
            'role': profile.role,
            'created_at': profile.created_at,
        })

    # Clear the table (this will be recreated with UUID field)
    UserProfile.objects.using(db_alias).all().delete()

    # Store backup for later restoration
    migrate_to_uuid.backup_data = backup_data


def restore_data(apps, schema_editor):
    """Restore data with new UUID primary keys."""
    UserProfile = apps.get_model('accounts', 'UserProfile')
    db_alias = schema_editor.connection.alias

    # Restore data with new UUIDs
    if hasattr(migrate_to_uuid, 'backup_data'):
        for data in migrate_to_uuid.backup_data:
            UserProfile.objects.using(db_alias).create(
                user_id=data['user_id'],
                role=data['role'],
                created_at=data['created_at'],
            )


def reverse_migration(apps, schema_editor):
    """This migration cannot be easily reversed."""
    raise RuntimeError("This migration cannot be automatically reversed.")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_delete_user'),
    ]

    operations = [
        # Step 1: Backup and clear data
        migrations.RunPython(migrate_to_uuid, reverse_migration),

        # Step 2: Delete and recreate the table with UUID
        migrations.DeleteModel(
            name='UserProfile',
        ),

        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('customer', 'Customer'), ('admin', 'Admin')], default='customer', help_text='User role for access control', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='user_profile', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Step 3: Restore data
        migrations.RunPython(restore_data, reverse_migration),
    ]