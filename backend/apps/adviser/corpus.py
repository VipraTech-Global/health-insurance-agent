from django.db import connection

CORPUS_PUBLICATION_LOCK = 4_295_117_903


def lock_corpus_publication() -> None:
    """Serialize current-corpus transitions with final answer publication."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CORPUS_PUBLICATION_LOCK])
