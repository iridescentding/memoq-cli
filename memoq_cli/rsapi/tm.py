# -*- coding: utf-8 -*-
"""
memoQ CLI - TM (Translation Memory) Manager

Supported RSAPI endpoints:
  GET    v1/tms?srcLang=&targetLang=       List TMs (with optional filters)
  GET    v1/tms?tmGuid=                    Get TM by GUID
  GET    v1/tms/{tmGuid}                   Get TM by GUID
  GET    v1/tms/{tmGuid}/custommetascheme  Get custom meta scheme
  POST   v1/tms/{tmGuid}/concordance       Concordance search
  POST   v1/tms/{tmGuid}/lookupsegments    Lookup segments
  GET    v1/tms/{tmGuid}/entries/{entryId}           Get entry
  POST   v1/tms/{tmGuid}/entries/create              Create entry
  POST   v1/tms/{tmGuid}/entries/{entryId}/update    Update entry
  POST   v1/tms/{tmGuid}/entries/{entryId}/delete    Delete entry

NOTE: RSAPI does NOT support TM create, delete, import, export, or search.
      Those operations require WSAPI (SOAP).
"""

from typing import List, Dict, Any, Optional

from .client import RSAPIClient
from ..utils import get_logger


class TMManager(RSAPIClient):
    """memoQ Translation Memory Manager (RSAPI)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("rsapi.tm")

    def list_tms(
        self,
        filter_text: Optional[str] = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all TMs, optionally filtered.

        Args:
            filter_text: Filter by name (client-side, API doesn't support name filter)
            source_lang: Filter by source language (server-side via srcLang param)
            target_lang: Filter by target language (server-side via targetLang param)
        """
        params = {}
        if source_lang:
            params["srcLang"] = source_lang
        if target_lang:
            params["targetLang"] = target_lang

        tms = self.get("tms", params=params if params else None)

        # Client-side name filter (API doesn't support it)
        if filter_text:
            filter_text = filter_text.lower()
            tms = [
                tm for tm in tms
                if filter_text in tm.get("FriendlyName", "").lower()
                or filter_text in tm.get("TMGuid", "").lower()
            ]

        return tms

    def get_tm_info(self, tm_guid: str) -> Dict[str, Any]:
        """Get TM details by GUID."""
        return self.get(f"tms/{tm_guid}")

    def get_custom_meta_scheme(self, tm_guid: str) -> Dict[str, Any]:
        """Get TM custom metadata scheme."""
        return self.get(f"tms/{tm_guid}/custommetascheme")

    def concordance(
        self,
        tm_guid: str,
        expressions: list,
        options: dict = None,
    ) -> Any:
        """
        Concordance search in a TM.

        Args:
            tm_guid: TM GUID
            expressions: List of search expression strings
            options: Optional dict with keys like ResultsLimit, CaseSensitive, etc.
        """
        payload = {"SearchExpression": expressions}
        if options:
            payload["Options"] = options
        return self.post(f"tms/{tm_guid}/concordance", json_data=payload)

    def lookup_segments(
        self,
        tm_guid: str,
        segments: List[str],
    ) -> Any:
        """
        Lookup segments in a TM.

        Args:
            tm_guid: TM GUID
            segments: List of segments in memoQ seg XML format
        """
        payload = {
            "Segments": [{"Segment": s} for s in segments]
        }
        return self.post(f"tms/{tm_guid}/lookupsegments", json_data=payload)

    def get_entry(self, tm_guid: str, entry_id: int) -> Dict[str, Any]:
        """Get a specific TM entry."""
        return self.get(f"tms/{tm_guid}/entries/{entry_id}")

    def create_entry(
        self,
        tm_guid: str,
        source_segment: str,
        target_segment: str,
        modifier: str = "",
    ) -> Dict[str, Any]:
        """
        Create a TM entry.

        Args:
            tm_guid: TM GUID
            source_segment: Source segment (memoQ seg XML, e.g. <seg>text</seg>)
            target_segment: Target segment
            modifier: Modifier username
        """
        payload = {
            "SourceSegment": source_segment,
            "TargetSegment": target_segment,
        }
        if modifier:
            payload["Modifier"] = modifier
        return self.post(f"tms/{tm_guid}/entries/create", json_data=payload)

    def update_entry(
        self,
        tm_guid: str,
        entry_id: int,
        source_segment: str,
        target_segment: str,
        modifier: str = "",
    ) -> Any:
        """
        Update a TM entry.

        Fetches the current entry first to get the full object
        (including Modified timestamp for concurrency control),
        then merges in the new values.
        """
        current = self.get_entry(tm_guid, entry_id)
        current["SourceSegment"] = source_segment
        current["TargetSegment"] = target_segment
        if modifier:
            current["Modifier"] = modifier
        return self.post(f"tms/{tm_guid}/entries/{entry_id}/update", json_data=current)

    def delete_entry(self, tm_guid: str, entry_id: int) -> Any:
        """Delete a TM entry."""
        return self.post(f"tms/{tm_guid}/entries/{entry_id}/delete")
