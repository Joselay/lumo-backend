import logging
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Sync movies from TMDB with enhanced logging for cron jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=10,
            help='Number of pages to fetch from TMDB (default: 10)'
        )
        parser.add_argument(
            '--log-file',
            type=str,
            default='tmdb_sync.log',
            help='Log file name (default: tmdb_sync.log)'
        )

    def handle(self, *args, **options):
        # Setup logging
        log_file = os.path.join(settings.BASE_DIR, 'logs', options['log_file'])
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)

        start_time = datetime.now()
        logger.info(f"Starting TMDB movie sync at {start_time}")

        try:
            # Call the main sync command
            call_command(
                'sync_tmdb_movies',
                pages=options['pages'],
                update_existing=True,
                verbosity=1
            )

            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"TMDB movie sync completed successfully in {duration}")

        except Exception as e:
            logger.error(f"TMDB movie sync failed: {str(e)}")
            end_time = datetime.now()
            duration = end_time - start_time
            logger.error(f"Failed sync duration: {duration}")
            raise