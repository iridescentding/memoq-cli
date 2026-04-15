# -*- coding: utf-8 -*-
"""
memoQ CLI - TB (Terminology Base) Manager

Supported RSAPI endpoints:
  GET    v1/tbs?lang[0]=&lang[1]=          List TBs (with optional language filters)
  GET    v1/tbs?tbGuid=                    Get TB by GUID
  GET    v1/tbs/{tbGuid}                   Get TB by GUID
  GET    v1/tbs/{tbGuid}/metadefinitions   Get meta definitions
  POST   v1/tbs/{tbGuid}/search            Search terms
  POST   v1/tbs/{tbGuid}/lookupterms       Lookup terms
  GET    v1/tbs/{tbGuid}/entries/{entryId}              Get entry
  POST   v1/tbs/{tbGuid}/entries/create                 Create entry
  POST   v1/tbs/{tbGuid}/entries/{entryId}/update       Update entry
  POST   v1/tbs/{tbGuid}/entries/{entryId}/delete       Delete entry
  GET/POST  v1/tbs/{tbGuid}/entries/{entryId}/entrymetas/{metaname}
  GET/POST  v1/tbs/{tbGuid}/entries/{entryId}/languagemetas/{metaname}
  GET/POST  v1/tbs/{tbGuid}/entries/{entryId}/languagemetas/{language}/{metaname}
  GET/POST  v1/tbs/{tbGuid}/entries/{entryId}/termmetas/{metaname}
  GET/POST  v1/tbs/{tbGuid}/entries/{entryId}/termmetas/{termId}/{metaname}

NOTE: RSAPI does NOT support TB create, delete, import, or export.
      Those operations require WSAPI (SOAP).
"""

from typing import List, Dict, Any, Optional

from .client import RSAPIClient
from ..utils import get_logger


class TBManager(RSAPIClient):
    """memoQ Terminology Base Manager (RSAPI)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("rsapi.tb")

    def list_tbs(
        self,
        filter_text: Optional[str] = None,
        lang0: Optional[str] = None,
        lang1: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all TBs, optionally filtered.

        Args:
            filter_text: Filter by name (client-side)
            lang0: First language filter (server-side via lang[0] param)
            lang1: Second language filter (server-side via lang[1] param)
        """
        params = {}
        if lang0:
            params["lang[0]"] = lang0
        if lang1:
            params["lang[1]"] = lang1

        tbs = self.get("tbs", params=params if params else None)

        if filter_text:
            filter_text = filter_text.lower()
            tbs = [
                tb for tb in tbs
                if filter_text in tb.get("FriendlyName", "").lower()
                or filter_text in tb.get("TBGuid", "").lower()
            ]

        return tbs

    def get_tb_info(self, tb_guid: str) -> Dict[str, Any]:
        """Get TB details by GUID."""
        return self.get(f"tbs/{tb_guid}")

    def get_meta_definitions(self, tb_guid: str) -> Any:
        """Get TB metadata definitions."""
        return self.get(f"tbs/{tb_guid}/metadefinitions")

    def search_tb(
        self,
        tb_guid: str,
        search_text: str,
        target_lang: str,
        condition: int = 1,
        limit: Optional[int] = None,
    ) -> Any:
        """
        Search terms in a TB.

        Args:
            tb_guid: TB GUID
            search_text: Search expression
            target_lang: Target language code
            condition: Match condition (0=BeginsWith, 1=Contains, 2=EndsWith, 3=ExactMatch)
            limit: Max results (default 120)
        """
        payload = {
            "SearchExpression": search_text,
            "TargetLanguage": target_lang,
            "Condition": condition,
        }
        if limit is not None:
            payload["Limit"] = limit
        return self.post(f"tbs/{tb_guid}/search", json_data=payload)

    def lookup_terms(
        self,
        tb_guid: str,
        segments: List[str],
        source_lang: str,
        target_lang: Optional[str] = None,
    ) -> Any:
        """
        Lookup terms in a TB.

        Args:
            tb_guid: TB GUID
            segments: List of segments (memoQ seg XML format)
            source_lang: Source language code
            target_lang: Target language code (optional)
        """
        payload = {
            "SourceLanguage": source_lang,
            "Segments": segments,
        }
        if target_lang:
            payload["TargetLanguage"] = target_lang
        return self.post(f"tbs/{tb_guid}/lookupterms", json_data=payload)

    def get_entry(self, tb_guid: str, entry_id: int) -> Dict[str, Any]:
        """Get a specific TB entry."""
        return self.get(f"tbs/{tb_guid}/entries/{entry_id}")

    def create_entry(
        self,
        tb_guid: str,
        terms: Dict[str, str],
        definition: str = "",
        domain: str = "",
        return_new_entry: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a TB entry.

        Args:
            tb_guid: TB GUID
            terms: Dict of {lang_code: term_text}
            definition: Term definition
            domain: Domain/subject
            return_new_entry: Whether to return the created entry
        """
        payload = {
            "Terms": [
                {"LangCode": lang, "Term": term}
                for lang, term in terms.items()
            ],
        }
        if definition:
            payload["Definition"] = definition
        if domain:
            payload["Domain"] = domain

        params = {}
        if return_new_entry:
            params["returnNewEntry"] = "true"

        endpoint = f"tbs/{tb_guid}/entries/create"
        return self.post(endpoint, json_data=payload, params=params)

    def update_entry(
        self,
        tb_guid: str,
        entry_id: int,
        terms: Dict[str, str],
        definition: str = "",
        domain: str = "",
    ) -> Any:
        """
        Update a TB entry.

        Fetches the current entry first, then merges in the new terms
        and sends the full entry object (required by the API).
        """
        # Fetch current entry (needed for Creator, Modified, etc.)
        current = self.get_entry(tb_guid, entry_id)

        # Build Languages list from terms
        languages = []
        for lang, term_text in terms.items():
            languages.append({
                "Language": lang,
                "TermItems": [{"Text": term_text}],
                "Definition": "",
            })

        current["Languages"] = languages
        if definition:
            current["Definition"] = definition
        if domain:
            current["Domain"] = domain

        return self.post(f"tbs/{tb_guid}/entries/{entry_id}/update", json_data=current)

    def delete_entry(self, tb_guid: str, entry_id: int) -> Any:
        """Delete a TB entry."""
        return self.post(f"tbs/{tb_guid}/entries/{entry_id}/delete")

    # --- Metadata operations ---

    def get_entry_meta(self, tb_guid: str, entry_id: int, meta_name: str) -> Any:
        """Get entry-level metadata."""
        return self.get(f"tbs/{tb_guid}/entries/{entry_id}/entrymetas/{meta_name}")

    def set_entry_meta(self, tb_guid: str, entry_id: int, meta_name: str, value: Any) -> Any:
        """Set entry-level metadata."""
        return self.post(f"tbs/{tb_guid}/entries/{entry_id}/entrymetas/{meta_name}", json_data=value)

    def get_language_meta(
        self, tb_guid: str, entry_id: int, meta_name: str,
        language: Optional[str] = None,
    ) -> Any:
        """Get language-level metadata."""
        if language:
            return self.get(f"tbs/{tb_guid}/entries/{entry_id}/languagemetas/{language}/{meta_name}")
        return self.get(f"tbs/{tb_guid}/entries/{entry_id}/languagemetas/{meta_name}")

    def set_language_meta(
        self, tb_guid: str, entry_id: int, meta_name: str, value: Any,
        language: Optional[str] = None,
    ) -> Any:
        """Set language-level metadata."""
        if language:
            return self.post(f"tbs/{tb_guid}/entries/{entry_id}/languagemetas/{language}/{meta_name}", json_data=value)
        return self.post(f"tbs/{tb_guid}/entries/{entry_id}/languagemetas/{meta_name}", json_data=value)

    def get_term_meta(
        self, tb_guid: str, entry_id: int, meta_name: str,
        term_id: Optional[str] = None,
    ) -> Any:
        """Get term-level metadata."""
        if term_id:
            return self.get(f"tbs/{tb_guid}/entries/{entry_id}/termmetas/{term_id}/{meta_name}")
        return self.get(f"tbs/{tb_guid}/entries/{entry_id}/termmetas/{meta_name}")

    def set_term_meta(
        self, tb_guid: str, entry_id: int, meta_name: str, value: Any,
        term_id: Optional[str] = None,
    ) -> Any:
        """Set term-level metadata."""
        if term_id:
            return self.post(f"tbs/{tb_guid}/entries/{entry_id}/termmetas/{term_id}/{meta_name}", json_data=value)
        return self.post(f"tbs/{tb_guid}/entries/{entry_id}/termmetas/{meta_name}", json_data=value)
