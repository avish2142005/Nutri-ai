"""KrishiNetra Multilingual Farmer Assistance Service.

Generates localized, farmer-friendly diagnostic advisories in 8 major regional farming languages:
- English (en)
- Kannada (kn) [ಕನ್ನಡ]
- Tulu (tcy) [ತುಳು (ಕನ್ನಡ ಲಿಪಿ)]
- Hindi (hi) [हिन्दी]
- Punjabi (pa) [ਪੰਜਾਬੀ]
- Telugu (te) [తెలుగు]
- Tamil (ta) [தமிழ்]
- Marathi (mr) [मराठी]
"""

from typing import Dict, Any


def get_multilingual_diagnosis(
    crop: str,
    disease_label: str,
    severity_level: str,
    risk_level: str,
    affected_percentage: float,
    is_healthy: bool
) -> Dict[str, str]:
    """Generate localized diagnostic summaries for farmers."""
    if is_healthy:
        return {
            "en": f"Great news! Your {crop} crop appears healthy with vigorous foliage and negligible disease risk.",
            "kn": f"ಶುಭ ಸುದ್ದಿ! ನಿಮ್ಮ {crop} ಬೆಳೆ ಸಂಪೂರ್ಣ ಆರೋಗ್ಯಕರವಾಗಿದ್ದು, ಉತ್ತಮ ಎಲೆಗಳ ಬೆಳವಣಿಗೆ ಹೊಂದಿದ್ದು ಯಾವುದೇ ರೋಗದ ಲಕ್ಷಣಗಳಿಲ್ಲ.",
            "tcy": f"ಎಡ್ಡೆ ಸುದ್ದಿ! ಈರೆನ {crop} ಬುಳೆ ಬಾರಿ ಎಡ್ಡ ಉಂಡು, ಎಲೆಕುಲು ಸಗ್ಗಿ ತೋಜೊಂದುಂಡು, ದಾಲ ರೋಗದ ಬೇನೆ ಇಜ್ಜಿ.",
            "hi": f"खुशखबरी! आपकी {crop} की फसल पूरी तरह स्वस्थ दिखाई दे रही है। रोग का कोई गंभीर खतरा नहीं है।",
            "pa": f"ਵੱਡੀ ਖੁਸ਼ਖਬਰੀ! ਤੁਹਾਡੀ {crop} ਦੀ ਫ਼ਸਲ ਬਿਲਕੁਲ ਤੰਦਰੁਸਤ ਹੈ ਅਤੇ ਬਿਮਾਰੀ ਦਾ ਕੋਈ ਖ਼ਤਰਾ ਨਹੀਂ ਹੈ।",
            "te": f"శుభవార్త! మీ {crop} పంట ఆరోగ్యకరంగా ఉంది. ఎటువంటి తెగుళ్ల ముప్పు లేదు.",
            "ta": f"நற்செய்தி! உங்கள் {crop} பயிர் ஆரோக்கியமாக உள்ளது. நோய் ஆபத்து இல்லை.",
            "mr": f"आनंदाची बातमी! तुमचे {crop} पीक पूर्णपणे निरोगी दिसत आहे. कोणताही धोका नाही."
        }

    # Diseased / Nutrient Deficient
    return {
        "en": f"Diagnostic Alert: {disease_label} identified on {crop} with {severity_level} severity ({affected_percentage}% leaf area affected). Weather-adjusted risk is {risk_level}.",
        "kn": f"ರೋಗ ಪತ್ತೆ ಎಚ್ಚರಿಕೆ: {crop} ಬೆಳೆಯಲ್ಲಿ {disease_label} ರೋಗ ಕಂಡುಬಂದಿದೆ. ತೀವ್ರತೆ: {severity_level} ({affected_percentage}% ಎಲೆಯ ಭಾಗ ಬಾಧಿತವಾಗಿದೆ). ಹವಾಮಾನ ಆಧಾರಿತ ಅಪಾಯ: {risk_level}.",
        "tcy": f"ರೋಗ ಪತ್ತೆ ಎಚ್ಚರಿಕೆ: {crop} ಬುಳೆಟ್ {disease_label} ರೋಗ ತೋಜಿದ್ ಬೈದ್ಂಡ್. ತೀವ್ರತೆ: {severity_level} ({affected_percentage}% ಇರೆಗ್ ಬೇನೆ ತಾಗ್ ದ್ಂಡ್). ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ಅಪಾಯ: {risk_level}.",
        "hi": f"निदान चेतावनी: {crop} में {disease_label} की पहचान हुई है। गंभीरता: {severity_level} ({affected_percentage}% पत्ती प्रभावित)। मौसम जोखिम स्तर: {risk_level}।",
        "pa": f"ਜਾਂਚ ਚੇਤਾਵਨੀ: {crop} ਵਿੱਚ {disease_label} ਦਾ ਪਤਾ ਲੱਗਾ ਹੈ। ਗੰਭੀਰਤਾ: {severity_level} ({affected_percentage}% ਪੱਤਾ ਪ੍ਰਭਾਵਿਤ)। ਮੌਸਮੀ ਖ਼ਤਰਾ: {risk_level}।",
        "te": f"రోగ నిర్ధారణ హెచ్చరిక: {crop} పంటలో {disease_label} గుర్తించబడింది. తీవ్రత: {severity_level} ({affected_percentage}% ఆకు దెబ్బతిన్నది). వాతావరణ ముప్పు: {risk_level}.",
        "ta": f"கண்டறிதல் எச்சரிக்கை: {crop} பயிரில் {disease_label} கண்டறியப்பட்டுள்ளது. தீவிரம்: {severity_level} ({affected_percentage}% இலை பாதிக்கப்பட்டுள்ளது). வானிலை ஆபத்து: {risk_level}.",
        "mr": f"रोग निदान सूचना: {crop} पिकावर {disease_label} आढळले आहे. तीव्रता: {severity_level} ({affected_percentage}% पान बाधित). हवामान जोखीम: {risk_level}."
    }
