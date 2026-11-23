"""Knowledge base loader and query utilities.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
_KB_DATA: Optional[Dict[str, Any]] = None


def load_diseases_kb() -> Dict[str, Any]:
    """Load and cache diseases.json knowledge base."""
    global _KB_DATA
    if _KB_DATA is None:
        kb_path = Path(__file__).resolve().parent / "diseases.json"
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                _KB_DATA = json.load(f)
            logger.info(f"Loaded {len(_KB_DATA)} disease profiles from knowledge base.")
        except Exception as e:
            logger.error(f"Failed to load knowledge base from {kb_path}: {e}")
            _KB_DATA = {}
    return _KB_DATA


def get_disease_profile(kb_id: str) -> Dict[str, Any]:
    """Fetch disease profile by ID with fallback default."""
    kb = load_diseases_kb()
    if kb_id in kb:
        return kb[kb_id]
    for key, val in kb.items():
        if val.get("raw_class") == kb_id:
            return val
    # Fallback default
    logger.warning(f"Disease ID {kb_id} not found in KB; using generic fallback.")
    return {
        "id": kb_id,
        "crop": "Crop",
        "display_name": kb_id.replace("_", " ").title(),
        "is_healthy": "healthy" in kb_id.lower(),
        "severity_weight": 0.5,
        "favourable_temp_range": [20.0, 30.0],
        "favourable_humidity_min": 70.0,
        "symptoms": ["Visible foliar symptoms."],
        "cultural_controls": ["Prune and remove infected plant debris."],
        "biological_controls": ["Apply preventive Trichoderma or Neem extract sprays."],
        "monitoring": ["Inspect leaf surfaces regularly for lesion expansion."],
        "water_management": ["Avoid overhead irrigation and reduce canopy moisture."],
        "chemical_advisory": "Consult authorized extension agents before chemical intervention. Confirm with your local agriculture officer / Krishi Vigyan Kendra (KVK) before applying any chemical treatment.",
        "prevention": ["Use certified disease-free seeds and balanced fertilizers."],
        "source_note": "Standard ICAR/FAO Integrated Pest Management Guidelines."
    }
