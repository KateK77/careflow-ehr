"""Version-1 typed synthetic report snapshots; no clinical interpretation."""
import copy
import json
import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from .catalog import validate_components


def envelope(order,specimen,components):
    panel=order.catalog_snapshot
    return {"schema_version":1,"kind":"report","context":{"order_id":str(order.public_id),"specimen_id":str(specimen.accession)},
        "catalog":{"code":panel["code"],"revision":panel["revision"],"display_name":panel["display_name"],"specimen_type":panel["specimen_type"],"definitions":copy.deepcopy(panel["components"])},"components":components}


def validate_payload(order,specimen,payload,complete=False):
    try:
        if len(json.dumps(payload,allow_nan=False,ensure_ascii=False,separators=(",",":")).encode())>65536:
            raise ValueError
        expected=envelope(order,specimen,[])
        if not isinstance(payload,dict) or set(payload)!=set(expected) or type(payload["schema_version"]) is not int:
            raise ValueError
        if any(payload[k]!=expected[k] for k in ["schema_version","kind","context","catalog"]):
            raise ValueError
        definitions=expected["catalog"]["definitions"]; validate_components(definitions)
        definitions={d["code"]:d for d in definitions}; seen=set()
        if not isinstance(payload["components"],list) or len(payload["components"])>10: raise ValueError
        for item in payload["components"]:
            if not isinstance(item,dict): raise ValueError
            code=item.get("code"); kind=item.get("value_kind"); definition=definitions.get(code)
            if not definition or code in seen: raise ValueError
            seen.add(code)
            keys={"code","value_kind"}
            if "comment" in item:
                keys.add("comment")
                if not isinstance(item["comment"],str) or len(item["comment"])>400: raise ValueError
            if kind=="absent":
                keys|={"absence_reason","absence_explanation"}
                if item.get("absence_reason")!="not_performed" or not isinstance(item.get("absence_explanation"),str) or not 1<=len(item["absence_explanation"].strip())<=1000: raise ValueError
            elif kind==definition["type"]=="numeric":
                keys|={"value","unit"}; value=item.get("value")
                if not isinstance(value,str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]{0,7})(?:\.[0-9]{1,4})?",value): raise ValueError
                if len(value.split(".")[1])>definition["precision"] if "." in value else False: raise ValueError
                if item.get("unit")!=definition["unit"] or not Decimal(definition["minimum"])<=Decimal(value)<=Decimal(definition["maximum"]): raise ValueError
            elif kind==definition["type"]=="coded":
                keys.add("value")
                if item.get("value") not in definition["allowed_codes"]: raise ValueError
            else: raise ValueError
            if set(item)!=keys: raise ValueError
        if complete and any(d["required"] and c not in seen for c,d in definitions.items()): raise ValueError
    except (ValueError,TypeError,KeyError,AttributeError,ValidationError):
        raise ValidationError("Invalid report snapshot: use the frozen panel, unique typed components, exact demo units and bounded decimal strings; publication requires every required component or an explicit not-performed reason.") from None
    return payload


def withdrawal_payload(order, predecessor, code, reason):
    return {"schema_version":1,"kind":"withdrawal","context":{"order_id":str(order.public_id),"specimen_id":str(predecessor.specimen.accession)},"catalog":{"code":order.catalog_snapshot["code"],"revision":order.catalog_snapshot["revision"]},"target_revision":predecessor.revision,"reason_code":code,"reason":reason}


def validate_withdrawal(result):
    if result.schema_version!=1 or result.status!="withdrawn" or not result.supersedes_id or result.performed_at or result.reason_code not in {"report_error","context_error"} or not 1<=len(result.reason.strip())<=1000:
        raise ValidationError("Invalid withdrawal notice metadata.")
    expected=withdrawal_payload(result.order,result.supersedes,result.reason_code,result.reason)
    if result.payload!=expected or type(result.payload.get('schema_version')) is not int or type(result.payload.get('target_revision')) is not int:
        raise ValidationError("Withdrawal notices must preserve exact target context and cannot contain result values.")
