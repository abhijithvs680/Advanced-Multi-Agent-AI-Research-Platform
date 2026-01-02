"""
Utility functions for the Multi-Agent AI Research Assistant
"""
from typing import Any, Dict, List
import json
from datetime import datetime


def serialize_datetime(obj: Any) -> str:
    """Serialize datetime objects to ISO format string"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def to_json(data: Any) -> str:
    """Convert data to JSON string with datetime handling"""
    return json.dumps(data, default=serialize_datetime, indent=2)


def from_json(json_str: str) -> Any:
    """Parse JSON string to Python object"""
    return json.loads(json_str)


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary"""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d
