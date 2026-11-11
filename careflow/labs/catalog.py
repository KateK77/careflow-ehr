import json
import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

SPECIMEN_TYPES = [("mock_serum", "Mock serum"), ("mock_blood", "Mock whole blood"), ("mock_swab", "Mock swab")]
DEMO_COMPONENTS = [{"code": "SYN-A", "label": "Demo analyte A", "type": "numeric", "required": True,
                    "unit": "demo-U", "precision": 4, "minimum": "0", "maximum": "9999"}]


def validate_components(value):
    """Validate immutable synthetic definitions, never expressions or clinical ranges."""
    message = "Use 1–10 unique SYN- components with valid typed demonstration definitions."
    try:
        if len(json.dumps(value, allow_nan=False).encode()) > 16384:
            raise ValueError
        if not isinstance(value, list) or not 1 <= len(value) <= 10:
            raise ValueError
        seen = set()
        for item in value:
            if not isinstance(item, dict):
                raise ValueError
            common = {"code", "label", "type", "required"}
            kind = item.get("type")
            extra = {"unit", "precision", "minimum", "maximum"} if kind == "numeric" else {"allowed_codes"}
            if kind not in {"numeric", "coded"} or set(item) != common | extra:
                raise ValueError
            if not isinstance(item["code"], str) or not re.fullmatch(r"SYN-[A-Z0-9-]{1,32}", item["code"]) or item["code"] in seen:
                raise ValueError
            seen.add(item["code"])
            if not isinstance(item["label"], str) or not 1 <= len(item["label"].strip()) <= 160 or type(item["required"]) is not bool:
                raise ValueError
            if kind == "numeric":
                if type(item["precision"]) is not int or not 0 <= item["precision"] <= 4:
                    raise ValueError
                if not isinstance(item["unit"], str) or not re.fullmatch(r"demo-[A-Za-z0-9/-]{1,32}", item["unit"]):
                    raise ValueError
                for key in ["minimum", "maximum"]:
                    if not isinstance(item[key], str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]{0,7})(?:\.[0-9]{1,4})?", item[key]):
                        raise ValueError
                if Decimal(item["minimum"]) > Decimal(item["maximum"]):
                    raise ValueError
            else:
                codes = item["allowed_codes"]
                if not isinstance(codes, list) or not 1 <= len(codes) <= 20 or any(not isinstance(c, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", c) for c in codes) or len(set(codes)) != len(codes):
                    raise ValueError
    except (ValueError, TypeError, KeyError, InvalidOperation, OverflowError):
        raise ValidationError(message) from None
