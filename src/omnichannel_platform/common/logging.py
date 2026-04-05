"""Zentrales Logging-Setup fuer die gesamte Plattform.

Alle Module verwenden get_logger(__name__) fuer konsistentes Log-Format:
  2026-04-05 08:01:00 | INFO | omnichannel_platform.batch.commerce_batch_ingestion | ...
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Erstellt einen Logger mit einheitlichem Format (Zeitstempel | Level | Modul | Nachricht)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)
