"""LLM-free Chat Service — grounded answers directly from the RAG knowledge base.

No external API key required.  Every answer is synthesised from retrieved
knowledge-base chunks, formatted clearly, and always includes the KVK notice
when chemical controls are mentioned.  IPM hierarchy is strictly respected:
cultural → biological → monitoring → chemical (last resort).
"""
import logging
import re
import sys
import os

# Ensure root directory is on sys.path for llm package imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from llm.llm_service import KrishiNetraLLMService
    _llm_service = KrishiNetraLLMService.get_instance()
except Exception as _e:
    _llm_service = None

from services.rag_service import retrieve

logger = logging.getLogger(__name__)

KVK_NOTICE = (
    "\n\n> ⚠️ **KVK Notice:** Confirm with your local agriculture officer / "
    "Krishi Vigyan Kendra (KVK) before applying any chemical treatment."
)

# ── Topic keywords used to score chunks ──────────────────────────────────────
_TOPIC_SEEDS = {
    "early_blight":    ["early blight", "alternaria", "concentric", "target-board"],
    "late_blight":     ["late blight", "phytophthora", "water-soaked", "greasy"],
    "leaf_mold":       ["leaf mold", "fulvia", "olive-green", "velvety"],
    "tylcv":           ["yellow leaf curl", "tylcv", "begomovirus", "whitefly", "virus"],
    "bacterial_spot":  ["bacterial spot", "xanthomonas", "water-soaked spots", "scab"],
    "powdery_mildew":  ["powdery mildew", "white powdery", "erysiphe", "leveillula"],
    "ipm":             ["ipm", "integrated pest", "scouting", "threshold"],
    "irrigation":      ["irrigat", "water", "drip", "moisture", "soil moisture"],
    "organic":         ["organic", "neem", "trichoderma", "bacillus", "biological"],
    "rotation":        ["crop rotation", "rotation", "nitrogen"],
}

_CHEMICAL_KEYWORDS = {
    "chemical", "fungicide", "pesticide", "spray", "apply", "dose",
    "mancozeb", "azoxystrobin", "copper", "imidacloprid", "metalaxyl",
    "chlorothalonil", "triadimefon", "hexaconazole",
}


def _score_line(line: str, query_words: set[str]) -> int:
    """Score a line by how many query words it contains."""
    low = line.lower()
    return sum(1 for w in query_words if w in low)


def _clean_line(line: str) -> str:
    """Remove markdown heading markers and excess whitespace."""
    line = re.sub(r"^#{1,4}\s+", "", line)
    return line.strip()


def _has_chemical_mention(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _CHEMICAL_KEYWORDS)


def _extract_section(chunks: list[str], query: str) -> list[str]:
    """
    Intelligently extract the most relevant lines from the retrieved chunks.
    Groups IPM steps (Cultural / Biological / Monitoring / Chemical) and
    returns them in the correct priority order.
    """
    query_words = set(re.findall(r"\w+", query.lower()))

    # Collect all lines from chunks, skip blank and heading-only lines
    all_lines: list[tuple[int, str]] = []  # (score, line)
    for chunk in chunks[:4]:
        for raw in chunk.split("\n"):
            cleaned = _clean_line(raw)
            if len(cleaned) < 12:
                continue
            score = _score_line(cleaned, query_words)
            all_lines.append((score, cleaned))

    # Separate IPM-step lines to reorder them correctly
    cultural:    list[str] = []
    biological:  list[str] = []
    monitoring:  list[str] = []
    chemical:    list[str] = []
    other_high:  list[str] = []

    for score, line in all_lines:
        low = line.lower()
        if re.search(r"\*?\*?cultural", low):
            cultural.append(line)
        elif re.search(r"\*?\*?biological", low):
            biological.append(line)
        elif re.search(r"\*?\*?monitoring", low):
            monitoring.append(line)
        elif re.search(r"\*?\*?(chemical|last resort)", low):
            chemical.append(line)
        elif score >= 2:
            other_high.append(line)

    # Build ordered answer lines
    ordered: list[str] = []
    for group, label in [
        (cultural,   "🌿 **Cultural controls (first line):**"),
        (biological, "🧫 **Biological controls:**"),
        (monitoring, "🔍 **Monitoring:**"),
        (chemical,   "⚗️ **Chemical advisory (last resort):**"),
    ]:
        if group:
            ordered.append(label)
            for l in group[:3]:  # max 3 per group
                ordered.append(f"- {l}")

    # Add high-relevance other lines if section was sparse
    if len(ordered) < 4 and other_high:
        ordered.extend(other_high[:6])

    # Absolute fallback: best-scored lines
    if not ordered:
        top = sorted(all_lines, key=lambda x: -x[0])[:8]
        ordered = [l for _, l in top if l]

    return ordered


def _build_intro(chunks: list[str], analysis_context: str) -> str:
    """Generate a 1-sentence intro from the analysis context or detected disease."""
    if analysis_context:
        return f"Based on your farm analysis ({analysis_context}), here are the recommended IPM steps:"
    # Try to detect disease name from chunks
    for chunk in chunks[:2]:
        m = re.search(r"##\s+(.+?)\s*\(", chunk)
        if m:
            return f"For **{m.group(1).strip()}**, here are the IPM-based recommendations:"
    return "Based on the FarmAI knowledge base, here are the recommended steps:"


async def chat(
    message: str,
    analysis_context: str = "",
    language: str = "en",
) -> tuple[str, list[str], bool]:
    """
    Returns (answer_text, source_files, grounded_flag).

    Fully local — no external API required.
    Retrieves KB chunks via RAG (semantic FAISS or keyword fallback),
    then synthesises a structured, IPM-ordered answer.
    """
    source_files = [
        "knowledge_base/docs/ipm_crop_diseases.md",
        "knowledge_base/docs/sustainable_agriculture.md",
    ]

    # Nothing to answer
    if not message.strip():
        return (
            "Please ask me a farming or disease management question. "
            "For example: *'What organic spray works for early blight?'*",
            source_files,
            True,
        )

    # 1. Retrieve relevant chunks
    search_query = f"{message} {analysis_context}".strip()
    chunks = retrieve(search_query, top_k=5)

    if not chunks:
        return (
            "I don't have specific information on that in my knowledge base. "
            "Please consult your local **Krishi Vigyan Kendra (KVK)** for tailored advice.",
            source_files,
            False,
        )

    # 2. Build structured answer using custom KrishiNetra LLM if available
    intro = _build_intro(chunks, analysis_context)
    if _llm_service and _llm_service.is_available():
        llm_reply = _llm_service.answer_query(message, context=analysis_context)
        answer = f"{intro}\n\n**KrishiNetra Agronomist LLM:**\n{llm_reply}"
    else:
        lines = _extract_section(chunks, message)
        body = "\n".join(lines) if lines else "\n".join(
            _clean_line(l) for chunk in chunks[:2]
            for l in chunk.split("\n") if len(l.strip()) > 12
        )[:1200]
        answer = f"{intro}\n\n{body}"

    # 3. Add KVK notice if any chemical mention
    if _has_chemical_mention(answer):
        answer += KVK_NOTICE

    # 4. Language note (if non-English requested)
    if language == "kn":
        answer += (
            "\n\n*ಗಮನಿಸಿ: ಈ ಸಲಹೆ FarmAI ಜ್ಞಾನ ಆಧಾರದ ಮೇಲಿದೆ. "
            "ಯಾವುದೇ ರಾಸಾಯನಿಕ ಚಿಕಿತ್ಸೆ ಅನ್ವಯಿಸುವ ಮೊದಲು "
            "ನಿಮ್ಮ ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿ / KVK ಅನ್ನು ಸಂಪರ್ಕಿಸಿ.*"
        )
    elif language == "hi":
        answer += (
            "\n\n*नोट: यह सलाह FarmAI ज्ञान आधार पर आधारित है। "
            "कोई भी रासायनिक उपचार लागू करने से पहले "
            "अपने स्थानीय कृषि अधिकारी / KVK से संपर्क करें।*"
        )

    return answer, source_files, True
