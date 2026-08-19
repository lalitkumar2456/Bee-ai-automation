from __future__ import annotations
import re
from datetime import datetime
from typing import Any

def clean(value: Any) -> str | None:
    value = None if value is None else str(value).strip()
    return None if not value or value.lower() in {'nan', 'none', 'null'} else value
def normalize_name(value: Any) -> str | None:
    value = clean(value)
    return re.sub(r'\s+', ' ', value.replace('.', ' ')).strip().title() if value else None
def name_key(value: Any) -> str:
    return re.sub(r'[^a-z]', '', (normalize_name(value) or '').lower())
def normalize_email(value: Any) -> str | None:
    value = clean(value)
    return value.lower() if value and '@' in value else None
def normalize_phone(value: Any) -> str | None:
    digits = re.sub(r'\D', '', clean(value) or '')
    return digits[-10:] if len(digits) >= 10 else None
def normalize_city(value: Any) -> str | None:
    value = clean(value)
    if not value: return None
    aliases = {'gurgaon':'Gurugram','gurugram':'Gurugram','bangalore':'Bengaluru','bengaluru':'Bengaluru','pune':'Pune','mumbai':'Mumbai','delhi':'Delhi','new delhi':'Delhi','delhi ncr':'Delhi NCR'}
    return aliases.get(value.lower(), value.title())
def normalize_date(value: Any) -> str | None:
    value = clean(value)
    if not value: return None
    for fmt in ('%Y-%m-%d','%d-%m-%Y','%d/%m/%Y','%m/%d/%Y','%d %b %Y','%d %B %Y'):
        try: return datetime.strptime(value, fmt).date().isoformat()
        except ValueError: pass
    return None
def normalize_ctc(value: Any) -> float | None:
    value = clean(value)
    try: amount = float(re.sub(r'[^0-9.]', '', value or ''))
    except ValueError: return None
    return amount * 100_000 if amount < 100 else amount
def normalize_skills(value: Any) -> list[str]:
    value = clean(value)
    return sorted({x.strip().lower() for x in re.split(r'[,;|/]', value or '') if x.strip()})
