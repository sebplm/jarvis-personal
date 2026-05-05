"""Multi-account Google Calendar connector.

Wraps :class:`GCalendarConnector` to aggregate events from several Google
accounts into a single stream.  Each account is identified by a ``label``
and a path to its OAuth credentials file.

Configuration in ``config.toml``::

    [connectors.gcalendar_multi]
    enabled  = true
    accounts = [
      { label = "perso",      credentials = "~/.openjarvis/connectors/gcalendar_perso.json" },
      { label = "mentorshow", credentials = "~/.openjarvis/connectors/gcalendar_mentorshow.json" },
    ]
    sync_days_ahead = 14
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from openjarvis.connectors._stubs import BaseConnector, Document, SyncStatus
from openjarvis.connectors.gcalendar import GCalendarConnector
from openjarvis.core.registry import ConnectorRegistry
from openjarvis.tools._stubs import ToolSpec


@ConnectorRegistry.register("gcalendar_multi")
class GCalendarMultiConnector(BaseConnector):
    """Aggregate events from multiple Google Calendar accounts."""

    connector_id = "gcalendar_multi"
    display_name = "Google Calendar (multi-comptes)"
    auth_type = "oauth"

    def __init__(self, accounts: Optional[List[Dict[str, str]]] = None, sync_days_ahead: int = 14) -> None:
        self._accounts: List[Dict[str, str]] = accounts or []
        self._sync_days_ahead = sync_days_ahead
        self._connectors: List[tuple[str, GCalendarConnector]] = [
            (
                acc.get("label", f"account_{i}"),
                GCalendarConnector(credentials_path=str(Path(acc["credentials"]).expanduser())),
            )
            for i, acc in enumerate(self._accounts)
            if acc.get("credentials")
        ]
        self._items_synced = 0
        self._last_sync: Optional[datetime] = None

    def is_connected(self) -> bool:
        return any(conn.is_connected() for _, conn in self._connectors)

    def disconnect(self) -> None:
        for _, conn in self._connectors:
            conn.disconnect()

    def auth_url(self) -> str:
        for _, conn in self._connectors:
            if not conn.is_connected():
                return conn.auth_url()
        return "https://console.cloud.google.com/apis/credentials"

    def handle_callback(self, code: str) -> None:
        for _, conn in self._connectors:
            if not conn.is_connected():
                conn.handle_callback(code)
                return

    def sync(
        self,
        *,
        since: Optional[datetime] = None,
        cursor: Optional[str] = None,
    ) -> Iterator[Document]:
        if since is None:
            since = datetime.now() - timedelta(days=1)

        total = 0
        for label, conn in self._connectors:
            if not conn.is_connected():
                continue
            for doc in conn.sync(since=since, cursor=cursor):
                # Prefix doc_id with account label to avoid collisions
                doc = Document(
                    doc_id=f"{label}:{doc.doc_id}",
                    source=f"gcalendar:{label}",
                    doc_type=doc.doc_type,
                    content=f"[Agenda : {label}]\n{doc.content}",
                    title=doc.title,
                    author=doc.author,
                    participants=doc.participants,
                    timestamp=doc.timestamp,
                    url=doc.url,
                    metadata={**(doc.metadata or {}), "account_label": label},
                )
                total += 1
                yield doc

        self._items_synced = total
        self._last_sync = datetime.now()

    def sync_status(self) -> SyncStatus:
        return SyncStatus(
            state="idle",
            items_synced=self._items_synced,
            last_sync=self._last_sync,
            cursor=None,
        )

    def mcp_tools(self) -> List[ToolSpec]:
        return [
            ToolSpec(
                name="calendar_multi_get_events_today",
                description=(
                    "Récupère tous les événements du jour sur l'ensemble des agendas Google "
                    "(tous les comptes configurés). Retourne titre, horaire, lieu et participants."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "account_label": {
                            "type": "string",
                            "description": "Filtrer par compte (ex: 'perso', 'mentorshow'). Vide = tous les comptes.",
                        },
                    },
                    "required": [],
                },
                category="productivity",
            ),
            ToolSpec(
                name="calendar_multi_search_events",
                description=(
                    "Recherche des événements par mot-clé dans tous les agendas Google configurés."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Terme de recherche",
                        },
                        "account_label": {
                            "type": "string",
                            "description": "Filtrer par compte. Vide = tous les comptes.",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Nombre maximum de résultats",
                            "default": 20,
                        },
                    },
                    "required": ["query"],
                },
                category="productivity",
            ),
            ToolSpec(
                name="calendar_multi_next_meeting",
                description="Trouve le prochain rendez-vous sur tous les agendas configurés.",
                parameters={
                    "type": "object",
                    "properties": {
                        "account_label": {
                            "type": "string",
                            "description": "Filtrer par compte. Vide = tous les comptes.",
                        },
                    },
                    "required": [],
                },
                category="productivity",
            ),
            ToolSpec(
                name="calendar_list_accounts",
                description="Liste les comptes Google Calendar configurés et leur statut de connexion.",
                parameters={"type": "object", "properties": {}, "required": []},
                category="productivity",
            ),
        ]
