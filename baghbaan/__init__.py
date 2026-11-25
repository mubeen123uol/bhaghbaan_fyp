from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def enable_sqlite_wal(sender, connection, **kwargs):
    """
    Enable Write-Ahead Logging (WAL) and set concurrency pragmas for SQLite.
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA busy_timeout = 30000;')
