"""Excel annexure processing for LAQ RAG system."""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


class ExcelProcessingError(Exception):
    """Raised when Excel processing fails."""

    pass


class AnnexureData:
    """Container for parsed annexure content."""

    def __init__(self, file_name: str, sheets: List[Dict[str, Any]]):
        self.file_name = file_name
        self.sheets = sheets

    def to_text(self, max_chars: int | None = 4000) -> str:
        """Render annexure content to a readable text block.

        If max_chars is None, return the full content.
        """
        parts: List[str] = []
        parts.append(f"Annexure File: {self.file_name}")
        for sheet in self.sheets:
            parts.append(f"\nSheet: {sheet['name']}")
            parts.append(sheet["markdown"])
        text = "\n\n".join(parts)
        if max_chars is None:
            return text
        return text[:max_chars]


class ExcelProcessor:
    """Parses .xls/.xlsx annexure files into structured text."""

    def __init__(self):
        pass

    def validate_excel_file(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise ExcelProcessingError(f"File not found: {file_path}")
        if path.suffix.lower() not in (".xls", ".xlsx"):
            raise ExcelProcessingError(
                f"Unsupported file type: {path.suffix} (expected .xls or .xlsx)"
            )
        return path

    def _sheet_to_markdown(
        self, df: pd.DataFrame, max_rows: int = 50, max_cols: int = 50
    ) -> str:
        # Trim oversized sheets
        df = df.iloc[:max_rows, :max_cols]
        # Replace NaNs for readability
        df = df.fillna("")
        # Build a simple Markdown table
        headers = " | ".join(map(str, df.columns.tolist()))
        separator = " | ".join(["---"] * len(df.columns))
        rows = [" | ".join(map(lambda x: str(x), row)) for row in df.values.tolist()]
        md = [headers, separator, *rows]
        return "\n".join(md)

    def process_excel(self, file_path: str) -> AnnexureData:
        """Read Excel and convert sheets to markdown-like tables."""
        path = self.validate_excel_file(file_path)

        try:
            sheets: List[Dict[str, Any]] = []

            # IMPORTANT: context manager closes file handle on Windows
            with pd.ExcelFile(path) as xls:
                for sheet_name in xls.sheet_names:
                    df = xls.parse(sheet_name)
                    markdown = self._sheet_to_markdown(df)
                    sheets.append({"name": sheet_name, "markdown": markdown})

            return AnnexureData(file_name=path.name, sheets=sheets)

        except Exception as e:
            raise ExcelProcessingError(f"Failed to parse Excel: {e}") from e
