"""Validation service for checking annexure and LAQ references."""

import json
import re
from typing import Dict, List, Optional, Tuple

from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class ValidationService:
    """Service for validating annexure and LAQ references."""

    def __init__(self, config: Config):
        """Initialize the validation service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.db = LAQDatabase(config)

    def validate_laq_annexure_references(self, laq_number: str, pdf_name: str) -> Dict:
        """Validate that annexures referenced in LAQ answers exist in the database.

        Args:
            laq_number: LAQ number to validate
            pdf_name: PDF name to validate (can be "unknown" if not set)

        Returns:
            Validation report dictionary
        """
        try:
            # Get LAQ documents for this number
            # If pdf_name is "unknown", get all LAQs with this number regardless of pdf
            if pdf_name == "unknown":
                where_clause = {
                    "$and": [
                        {"laq_num": str(laq_number)},
                        {"type": {"$ne": "annexure"}},
                    ]
                }
            else:
                where_clause = {
                    "$and": [
                        {"laq_num": str(laq_number)},
                        {"pdf": pdf_name},
                        {"type": {"$ne": "annexure"}},
                    ]
                }

            laq_results = self.db.collection.get(
                where=where_clause,
                include=["metadatas", "documents"],
            )

            # Get available annexures for this LAQ
            annexure_results = self.db.get_annexures_for_laq(laq_number)

            # Extract referenced annexures from LAQ answers
            referenced_annexures = set()
            for metadata in laq_results.get("metadatas", []):
                refs = metadata.get("referenced_annexures", "[]")
                try:
                    refs_list = json.loads(refs)
                    for ref in refs_list:
                        referenced_annexures.add(self._normalize_annexure_label(ref))

                except (json.JSONDecodeError, TypeError):
                    pass

            # Extract available annexure labels
            available_annexures = set()
            for metadata in annexure_results.get("metadatas", []):
                label = metadata.get("annexure_label", "")
                if label:
                    available_annexures.add(self._normalize_annexure_label(label))

            # Check for missing annexures
            missing_annexures = referenced_annexures - available_annexures

            # Check for unreferenced annexures
            unreferenced_annexures = available_annexures - referenced_annexures

            
            return {
                "laq_number": laq_number,
                "pdf_name": pdf_name,
                "total_laq_documents": len(laq_results.get("metadatas", [])),
                "total_annexures": len(annexure_results.get("metadatas", [])),
                "total_uploaded_annexures": len(available_annexures),
                "referenced_annexures": sorted(list(referenced_annexures)),
                "available_annexures": sorted(list(available_annexures)),
                "missing_annexures": sorted(list(missing_annexures)),
                "unreferenced_annexures": sorted(list(unreferenced_annexures)),
                "validation_status": (
                    "valid"
                    if not missing_annexures and not unreferenced_annexures
                    else "invalid"
                ),
                "issues": [
                    issue
                    for issue in [
                        (
                            f"Missing annexure(s): {', '.join(sorted(missing_annexures))}"
                            if missing_annexures
                            else None
                        ),
                        (
                            f"Uploaded but not mentioned in answer: {', '.join(sorted(unreferenced_annexures))}"
                            if unreferenced_annexures
                            else None
                        ),
                    ]
                    if issue is not None
                ],
            }

        except DatabaseError as e:
            raise ValidationError(f"Database error during validation: {e}")
        except Exception as e:
            raise ValidationError(f"Unexpected error during validation: {e}")

    def check_annexure_referenced_in_laq(self, laq_number: str, annexure_label: str) -> Tuple[bool, Optional[str]]:
        """Check if an annexure is referenced in a LAQ's answer.
        
        Args:
            laq_number: LAQ number to check
            annexure_label: Annexure label to search for (e.g., "I", "II", "III")
            
        Returns:
            Tuple of (is_referenced: bool, laq_document_ids: Optional[List[str]])
            Returns True and list of document IDs if referenced, False and None otherwise
        """
        try:
            # Normalize the input annexure label
            normalized_input = self._normalize_annexure_label(annexure_label)
            print(f"🔍 Checking if annexure '{annexure_label}' (normalized: '{normalized_input}') is referenced in LAQ {laq_number}")
            
            # Get all LAQ documents for this number (excluding annexures)
            laq_results = self.db.collection.get(
                where={
                    "$and": [
                        {"laq_num": str(laq_number)},
                        {"type": {"$ne": "annexure"}},
                    ]
                },
                include=["metadatas"],
            )
            
            # Check if this annexure is referenced in any of the LAQ answers
            referenced_document_ids = []
            all_refs_found = []
            
            for metadata in laq_results.get("metadatas", []):
                refs = metadata.get("referenced_annexures", "[]")
                try:
                    refs_list = json.loads(refs)
                    print(f"  Found referenced_annexures in LAQ: {refs_list}")
                    for ref in refs_list:
                        normalized_ref = self._normalize_annexure_label(ref)
                        all_refs_found.append(normalized_ref)
                        print(f"    Comparing '{ref}' (normalized: '{normalized_ref}') with target '{normalized_input}'")
                        if normalized_ref == normalized_input:
                            referenced_document_ids.append(metadata.get("id"))
                            print(f"    ✓ MATCH FOUND!")
                            break
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"  Error parsing referenced_annexures: {e}")
            
            print(f"  All references found in LAQ: {all_refs_found}")
            print(f"  Match result: {bool(referenced_document_ids)}")
            
            if referenced_document_ids:
                return True, referenced_document_ids
            else:
                return False, None
                
        except DatabaseError as e:
            raise ValidationError(f"Database error checking annexure reference: {e}")
        except Exception as e:
            import traceback
            print(f"❌ Error in check_annexure_referenced_in_laq: {e}\n{traceback.format_exc()}")
            raise ValidationError(f"Unexpected error checking annexure reference: {e}")

    def _normalize_annexure_label(self, label: str) -> str:
        """
        Normalize annexure labels to Roman numeral only.
        Examples:
        - "Annexure-I" → "I"
        - "annexure ii" → "II"
        - "III" → "III"
        - "I" → "I"
        - "ANEXURES I" → "I"
        - "Annex I" → "I"
        """
        if not label:
            return ""

        original = label
        label = label.upper().strip()
        
        # Try pattern 1: ANNEXURE (with variations) followed by separator and Roman numeral
        # Handles: "Annexure I", "ANNEXURE-I", "Anexures II", etc.
        match = re.search(r"ANNEX(?:URE)?S?[-\s]+([IVivXLCDM]+)", label)
        if match:
            return match.group(1).upper()
        
        # Try pattern 2: ANEXURES (common typo) followed by separator
        match = re.search(r"ANEXURES?[-\s]+([IVivXLCDM]+)", label)
        if match:
            return match.group(1).upper()
        
        # Try pattern 3: Just extract any Roman numerals from the label
        match = re.search(r"([IVivXLCDM]+)", label)
        if match:
            return match.group(1).upper()
        
        # Fallback: return the original label if no pattern matched
        return label

    def validate_all_laqs(self) -> Dict:
        """Validate annexure references for all LAQs in the database.

        Returns:
            Summary validation report
        """
        try:
            # Get all LAQ documents (excluding annexures)
            all_results = self.db.collection.get(
                where={"type": {"$ne": "annexure"}}, include=["metadatas"]
            )

            # Group by LAQ number (pdf is optional)
            laq_groups = {}
            for metadata in all_results.get("metadatas", []):
                laq_num = metadata.get("laq_num")
                pdf = metadata.get("pdf") or "unknown"  # Default to "unknown" if not present
                if laq_num:
                    key = f"{laq_num}_{pdf}"
                    if key not in laq_groups:
                        laq_groups[key] = {"laq_number": laq_num, "pdf_name": pdf}

            # Validate each group
            validation_reports = []
            total_issues = 0

            for group in laq_groups.values():
                report = self.validate_laq_annexure_references(
                    group["laq_number"], group["pdf_name"]
                )
                validation_reports.append(report)
                if report["validation_status"] == "invalid":
                    total_issues += 1

            return {
                "total_laqs_validated": len(validation_reports),
                "total_with_issues": total_issues,
                "validation_reports": validation_reports,
                "summary": {
                    "valid_laqs": len(validation_reports) - total_issues,
                    "invalid_laqs": total_issues,
                    "overall_status": "valid" if total_issues == 0 else "invalid",
                },
            }

        except Exception as e:
            raise ValidationError(f"Error during bulk validation: {e}")

    def get_annexure_usage_stats(self) -> Dict:
        """Get statistics about annexure usage across all LAQs.

        Returns:
            Usage statistics
        """
        try:
            # Get all LAQ documents
            laq_results = self.db.collection.get(
                where={"type": {"$ne": "annexure"}}, include=["metadatas"]
            )

            # Count annexure references
            annexure_usage = {}
            total_references = 0

            for metadata in laq_results.get("metadatas", []):
                refs = metadata.get("referenced_annexures", "[]")
                try:
                    refs_list = json.loads(refs)
                    for ref in refs_list:
                        annexure_usage[ref] = annexure_usage.get(ref, 0) + 1
                        total_references += 1
                except (json.JSONDecodeError, TypeError):
                    pass

            # Get available annexures
            annexure_results = self.db.collection.get(
                where={"type": "annexure"}, include=["metadatas"]
            )

            available_annexures = set()
            for metadata in annexure_results.get("metadatas", []):
                label = metadata.get("annexure_label", "")
                if label:
                    available_annexures.add(self._normalize_annexure_label(label))

            return {
                "total_annexure_documents": len(annexure_results.get("metadatas", [])),
                "unique_annexure_labels": len(available_annexures),
                "total_references_in_laqs": total_references,
                "unique_referenced_annexures": len(annexure_usage),
                "annexure_usage_breakdown": dict(sorted(annexure_usage.items())),
                "unreferenced_annexures": sorted(
                    list(available_annexures - set(annexure_usage.keys()))
                ),
                "referenced_but_missing": sorted(
                    list(set(annexure_usage.keys()) - available_annexures)
                ),
            }

        except DatabaseError as e:
            raise ValidationError(f"Database error getting usage stats: {e}")
        except Exception as e:
            raise ValidationError(f"Unexpected error getting usage stats: {e}")
