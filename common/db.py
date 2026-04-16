# Raw-SQL data layer. This project does not use the Django ORM.
from contextlib import contextmanager

import psycopg2
from django.conf import settings


def get_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
    )


@contextmanager
def db_cursor(commit=False):
    """Yield a psycopg2 cursor; close the connection on exit.

    Pass commit=True for services that mutate state. Selectors (reads) omit it.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            yield cur
            if commit:
                conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
