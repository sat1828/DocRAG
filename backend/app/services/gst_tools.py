"""
GST and Indian legal compliance tools.
"""
import re
from typing import List, Dict, Any, Optional
from app.utils.validators import validate_gstin_format
import structlog

logger = structlog.get_logger()


class GSTTools:
    """Tools for GST validation, extraction, and calculations."""

    @staticmethod
    def validate_gstin(gstin: str) -> Dict[str, Any]:
        is_valid_format = validate_gstin_format(gstin)
        return {
            "gstin": gstin,
            "valid_format": is_valid_format,
            "state_code": gstin[:2] if is_valid_format and len(gstin) >= 2 else None,
            "pan": gstin[2:12] if is_valid_format and len(gstin) == 15 else None,
        }

    @staticmethod
    def extract_gstins(text: str) -> List[str]:
        gstin_pattern = re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[\dA-Z]{1}\b')
        matches = gstin_pattern.findall(text)
        valid_gstins = [g for g in matches if validate_gstin_format(g)]
        logger.info("Extracted GSTINs from text", count=len(valid_gstins))
        return valid_gstins

    @staticmethod
    def extract_hsn_codes(text: str) -> List[str]:
        hsn_pattern = re.compile(r'(?:HSN\s*(?:Code)?:?\s*)(\d{4,8})', re.IGNORECASE)
        matches = hsn_pattern.findall(text)
        if len(matches) < 3:
            standalone_pattern = re.compile(r'(?:^|\s)(\d{4}(?:\d{2}(?:\d{2})?))(?:\s|$)')
            matches.extend(standalone_pattern.findall(text))
        unique_hsns = list(set(matches))
        logger.info("Extracted HSN codes", count=len(unique_hsns))
        return unique_hsns

    @staticmethod
    def calculate_gst(amount: float, rate: float, gst_type: str = "both") -> Dict[str, float]:
        total_gst = amount * (rate / 100.0)
        if gst_type == "igst":
            return {
                "base_amount": amount,
                "igst": round(total_gst, 2),
                "cgst": 0.0,
                "sgst": 0.0,
                "total_gst": round(total_gst, 2),
                "total_amount": round(amount + total_gst, 2)
            }
        else:
            half_gst = total_gst / 2.0
            return {
                "base_amount": amount,
                "igst": 0.0,
                "cgst": round(half_gst, 2),
                "sgst": round(half_gst, 2),
                "total_gst": round(total_gst, 2),
                "total_amount": round(amount + total_gst, 2)
            }

    @staticmethod
    def verify_tax_totals(base_amount: float, cgst: float, sgst: float, igst: float, total_amount: float) -> Dict[str, Any]:
        calculated_total = base_amount + cgst + sgst + igst
        discrepancy = abs(calculated_total - total_amount)
        is_valid = discrepancy < 1.0
        return {
            "valid": is_valid,
            "base_amount": base_amount,
            "total_tax": cgst + sgst + igst,
            "calculated_total": round(calculated_total, 2),
            "reported_total": total_amount,
            "discrepancy": round(discrepancy, 2),
            "flags": [] if is_valid else ["Tax total mismatch detected"]
        }

    @staticmethod
    def flag_legal_risks(text: str) -> List[Dict[str, Any]]:
        risks = []
        if re.search(r'force\s*majeure|act\s*of\s*god|unforeseen\s*events', text, re.IGNORECASE):
            risks.append({"category": "Force Majeure", "severity": "medium", "description": "Force Majeure clause detected", "section": "Extract"})
        if re.search(r'penalty|liquidated\s*damages|compensation\s*for\s*breach', text, re.IGNORECASE):
            risks.append({"category": "Penalty Clause", "severity": "high", "description": "Penalty clause found", "section": "Extract"})
        if re.search(r'termination|terminate\s*agreement|notice\s*period', text, re.IGNORECASE):
            risks.append({"category": "Termination", "severity": "medium", "description": "Termination clause detected", "section": "Extract"})
        if re.search(r'jurisdiction|arbitration|dispute\s*resolution', text, re.IGNORECASE):
            risks.append({"category": "Dispute Resolution", "severity": "medium", "description": "Jurisdiction clause found", "section": "Extract"})
        if re.search(r'gst|goods\s*and\s*services\s*tax', text, re.IGNORECASE):
            if not GSTTools.extract_gstins(text):
                risks.append({"category": "GST Compliance", "severity": "high", "description": "GST mentioned but no valid GSTIN", "section": "N/A"})
        if re.search(r'indemnif|hold\s*harmless', text, re.IGNORECASE):
            risks.append({"category": "Indemnity", "severity": "high", "description": "Indemnity clause detected", "section": "Extract"})
        logger.info("Legal risk analysis completed", risks_found=len(risks))
        return risks


gst_tools = GSTTools()
