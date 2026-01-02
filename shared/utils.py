"""
Utility functions for the Multi-Agent AI Research Assistant
"""
from typing import Any, Dict, List
import json
from datetime import datetime


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable formats.
    Handles NumPy, Pandas, Enums, datetimes, and stringifies dict keys.
    """
    import numpy as np
    try:
        import pandas as pd
    except ImportError:
        pd = None
    from enum import Enum
    import uuid

    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    elif obj is None:
        return None
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, (int,)):
        return obj
    elif isinstance(obj, float):
        # Handle NaN and Infinity which are invalid in JSON
        import math
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, (np.integer, np.floating, np.bool_)):
        val = obj.item() if hasattr(obj, 'item') else (int(obj) if isinstance(obj, np.integer) else float(obj))
        # Also check numpy floats for NaN/Inf
        import math
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return val
    elif pd is not None and hasattr(obj, 'to_dict') and isinstance(obj, (pd.DataFrame, pd.Series)):
        return sanitize_for_json(obj.to_dict())
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, (datetime, uuid.UUID)):
        return obj.isoformat() if isinstance(obj, datetime) else str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    
    # Fallback to string representation for anything else
    try:
        return str(obj)
    except Exception:
        return "unserializable_object"


def to_json(data: Any) -> str:
    """Convert data to JSON string with robust sanitization"""
    return json.dumps(sanitize_for_json(data), indent=2)


def from_json(json_str: str) -> Any:
    """Parse JSON string to Python object"""
    if not json_str:
        return None
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
