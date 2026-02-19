"""Fragment library module for lucy-ng.

Provides the storage foundation and search engine for the v5.0 Fragment Library:

- :class:`SSCRecord` — Pydantic model for a substructure-subspectrum correlation
- :class:`SSCMatch` — Pydantic model for a fragment search result
- :class:`FragmentDatabaseManager` — SQLite manager for ``lucy-ng-fragments.db``
- :class:`FragmentSearcher` — Two-phase search engine (pre-screening + fine matching)
- :func:`shifts_to_fingerprint` — Encode 13C shifts as a 256-bit fingerprint

Example usage::

    from lucy_ng.fragments import FragmentDatabaseManager, SSCRecord, shifts_to_fingerprint

    with FragmentDatabaseManager("data/reference/lucy-ng-fragments.db") as db:
        db.create_tables()
        count = db.get_ssc_count()

    fp = shifts_to_fingerprint([30.5, 130.2, 199.1])  # 32-byte fingerprint

    from lucy_ng.fragments import FragmentSearcher

    with FragmentSearcher("data/reference/lucy-ng-fragments.db") as searcher:
        matches = searcher.search([128.0, 130.5, 199.1])
"""

from __future__ import annotations

from lucy_ng.fragments.db import FragmentDatabaseManager
from lucy_ng.fragments.fingerprint import shifts_to_fingerprint
from lucy_ng.fragments.models import SSCMatch, SSCRecord
from lucy_ng.fragments.searcher import FragmentSearcher

__all__ = [
    "FragmentDatabaseManager",
    "FragmentSearcher",
    "SSCMatch",
    "SSCRecord",
    "shifts_to_fingerprint",
]
