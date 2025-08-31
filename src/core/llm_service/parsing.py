import json
import re
from typing import Optional, Dict, Any, Tuple


def extract_json_from_response_text(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Attempt to extract and parse a JSON object from a model response that
    may include prose or markdown fences.
    """
    if not text:
        return None, "Empty response"

    fence_pattern = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)
    m = fence_pattern.search(text)
    candidate: Optional[str] = None
    if m:
        candidate = m.group(1).strip()
    else:
        start = text.find('{')
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        break

    if not candidate:
        return None, "No JSON candidate found in response"

    try:
        return json.loads(candidate), None
    except Exception:
        cleaned = (
            candidate.replace('“', '"')
            .replace('”', '"')
            .replace('’', "'")
            .replace('`', '')
        )
        try:
            return json.loads(cleaned), None
        except Exception as e2:
            return None, f"JSON parse failed: {e2} | Original candidate: {candidate[:2000]}"

