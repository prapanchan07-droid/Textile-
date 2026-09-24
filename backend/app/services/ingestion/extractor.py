import os
import re
import csv
import io
import datetime
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from openpyxl import load_workbook
from pypdf import PdfReader
from PIL import Image
from app.services.ingestion.normalizer import Normalizer
from app.core.logging import logger

KNOWN_SECTIONS = [
    "CARDING", "CARD", "DRAW FRAME", "DRAWING", "DRAWFRAME",
    "SIMPLEX", "SPEED FRAME", "RING FRAME", "SPINNING",
    "AIRJET", "VORTEX", "WEAVING", "BLOWROOM", "COMBING",
    "LINKCONER", "WINDING", "PREPARATORY", "LOOMS", "FINISHER"
]

def detect_section_header(text: str) -> Optional[str]:
    """Detect if a text string represents a section or department title."""
    clean = str(text).strip().upper()
    if not clean or len(clean) > 40:
        return None
    for kw in KNOWN_SECTIONS:
        if kw in clean or clean == kw:
            return kw.title()
    return None

class Extractor:
    @staticmethod
    def extract_from_file(file_path: str, filename: str) -> Tuple[List[Dict[str, Any]], List[str], Optional[str], Optional[str]]:
        """
        Extract tabular records, sheet names, report date, and report unit from any supported file format:
        XLSX, XLS, CSV, PDF, PNG, JPG, JPEG.
        """
        ext = os.path.splitext(filename)[1].lower()
        sheet_names: List[str] = []
        records: List[Dict[str, Any]] = []
        report_date: Optional[str] = None
        report_unit: Optional[str] = None

        if ext in ['.xlsx', '.xls']:
            records, sheet_names, report_date, report_unit = Extractor._extract_excel(file_path)
        elif ext == '.csv':
            records, report_date, report_unit = Extractor._extract_csv(file_path)
            sheet_names = ["CSV Data"]
        elif ext == '.pdf':
            records, report_date, report_unit = Extractor._extract_pdf(file_path)
            sheet_names = ["PDF Data"]
        elif ext in ['.jpg', '.jpeg', '.png']:
            records, report_date, report_unit = Extractor._extract_image(file_path)
            sheet_names = ["Scanned Image Data"]
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Try to extract date & unit from filename if not found inside content
        if not report_date:
            report_date = Extractor._extract_date_from_text(filename)
        if not report_date:
            report_date = datetime.date.today().strftime("%Y-%m-%d")

        if not report_unit:
            report_unit = Extractor._extract_unit_from_text(filename)

        return records, sheet_names, report_date, report_unit

    @staticmethod
    def _extract_excel(file_path: str) -> Tuple[List[Dict[str, Any]], List[str], Optional[str], Optional[str]]:
        sheet_names: List[str] = []
        records: List[Dict[str, Any]] = []
        report_date: Optional[str] = None
        report_unit: Optional[str] = None

        try:
            wb = load_workbook(file_path, data_only=True)
            sheet_names = wb.sheetnames
        except Exception as e:
            logger.warning(f"Could not load openpyxl workbook: {e}")
            sheet_names = ["Sheet1"]

        xls = pd.ExcelFile(file_path)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            if df.empty:
                continue

            text_block = f"{sheet} {df.to_string()}"
            if not report_date:
                report_date = Extractor._extract_date_from_text(text_block)
            if not report_unit:
                report_unit = Extractor._extract_unit_from_text(text_block)

            # Clean headers
            normalized_columns = [Normalizer.normalize_header(col) for col in df.columns]
            df.columns = normalized_columns

            current_section: Optional[str] = None

            for row_idx, row in df.iterrows():
                # Check for section header row
                row_str_values = [str(v).strip() for v in row.values if pd.notna(v)]
                if len(row_str_values) == 1 or (len(row_str_values) > 0 and row_str_values[0].upper() in KNOWN_SECTIONS):
                    sec = detect_section_header(row_str_values[0])
                    if sec:
                        current_section = sec

                rec = {k: row[k] for k in df.columns if pd.notna(row[k])}
                if rec:
                    if current_section and "department" not in rec:
                        rec["department"] = current_section
                    rec["_source_sheet"] = sheet
                    rec["_source_row"] = int(row_idx) + 2  # 1-indexed row with header
                    rec["_source_column"] = "Multiple"
                    records.append(rec)

        return records, sheet_names, report_date, report_unit

    @staticmethod
    def _extract_csv(file_path: str) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
        records: List[Dict[str, Any]] = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        text_block = "".join(lines)
        report_date = Extractor._extract_date_from_text(text_block)
        report_unit = Extractor._extract_unit_from_text(text_block)

        try:
            df = pd.read_csv(file_path)
            normalized_columns = [Normalizer.normalize_header(col) for col in df.columns]
            df.columns = normalized_columns

            current_section: Optional[str] = None

            for row_idx, row in df.iterrows():
                row_str_values = [str(v).strip() for v in row.values if pd.notna(v)]
                if len(row_str_values) == 1 or (len(row_str_values) > 0 and row_str_values[0].upper() in KNOWN_SECTIONS):
                    sec = detect_section_header(row_str_values[0])
                    if sec:
                        current_section = sec

                rec = {k: row[k] for k in df.columns if pd.notna(row[k])}
                if rec:
                    if current_section and "department" not in rec:
                        rec["department"] = current_section
                    rec["_source_sheet"] = "CSV"
                    rec["_source_row"] = int(row_idx) + 2
                    rec["_source_column"] = "CSV Row"
                    records.append(rec)
        except Exception:
            records = Extractor._parse_text_lines_to_records(text_block)

        return records, report_date, report_unit

    @staticmethod
    def _extract_pdf(file_path: str) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"

        report_date = Extractor._extract_date_from_text(full_text)
        report_unit = Extractor._extract_unit_from_text(full_text)
        records = Extractor._parse_text_lines_to_records(full_text)
        return records, report_date, report_unit

    @staticmethod
    def _extract_image(file_path: str) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
        text = ""
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False)
            result = reader.readtext(file_path, detail=0)
            text = "\n".join(result)
        except Exception as e:
            logger.warning(f"EasyOCR fallback to pytesseract: {e}")
            try:
                import pytesseract
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
            except Exception as ex:
                logger.error(f"OCR extraction failed: {ex}")

        report_date = Extractor._extract_date_from_text(text)
        report_unit = Extractor._extract_unit_from_text(text)
        records = Extractor._parse_text_lines_to_records(text)
        return records, report_date, report_unit

    @staticmethod
    def _extract_unit_from_text(text: str) -> Optional[str]:
        """Detect unit designation (e.g. Unit I, Unit II, Mill 1, Plant 2) from text block or filename."""
        if not text:
            return None
        match = re.search(r'\b(UNIT\s*(?:I{1,3}|IV|V|[0-9]+|A|B))\b', text, re.IGNORECASE)
        if match:
            raw_u = match.group(1).upper()
            if "1" in raw_u or "UNIT I" in raw_u or raw_u == "UNIT 1" or raw_u == "UNIT A":
                return "Unit I"
            if "2" in raw_u or "UNIT II" in raw_u or raw_u == "UNIT 2" or raw_u == "UNIT B":
                return "Unit II"
            return raw_u.title()
        return None

    @staticmethod
    def _extract_date_from_text(text: str) -> Optional[str]:
        """Regex scanner for various date formats (e.g. 14/08/2026, 2026-08-14, Aug 14 2026)."""
        patterns = [
            r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})',
            r'(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                raw_dt = match.group(1)
                try:
                    dt = pd.to_datetime(raw_dt)
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return raw_dt
        return None

    @staticmethod
    def _parse_text_lines_to_records(text: str) -> List[Dict[str, Any]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        records = []
        headers = []
        current_section: Optional[str] = None

        for idx, line in enumerate(lines):
            # Check section header
            sec = detect_section_header(line)
            if sec:
                current_section = sec
                continue

            parts = re.split(r'\s{2,}|\t|,|\|', line)
            parts = [p.strip() for p in parts if p.strip()]

            if not headers and len(parts) >= 2 and any(k in line.upper() for k in ["TARGET", "ACTUAL", "PROD", "SHIFT", "LOSS"]):
                headers = [Normalizer.normalize_header(p) for p in parts]
            elif headers and len(parts) == len(headers):
                rec = {headers[i]: parts[i] for i in range(len(headers))}
                if current_section and "department" not in rec:
                    rec["department"] = current_section
                rec["_source_sheet"] = "Text/PDF/Image"
                rec["_source_row"] = idx + 1
                rec["_source_column"] = "Line"
                records.append(rec)
            elif len(parts) >= 3:
                rec = {}
                for p_idx, val in enumerate(parts):
                    rec[f"col_{p_idx}"] = val
                if current_section and "department" not in rec:
                    rec["department"] = current_section
                rec["_source_sheet"] = "Text/PDF/Image"
                rec["_source_row"] = idx + 1
                rec["_source_column"] = "Line"
                records.append(rec)

        return records

