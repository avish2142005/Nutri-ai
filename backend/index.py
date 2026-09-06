"""
AI-Powered Nutrition Analyzer - Backend API
============================================
FastAPI backend with:
- Gemini LLM integration via Google AI SDK
- Nutrition RAG pipeline (knowledge-base lookup + LLM reasoning)
- Streaming chat endpoint
- Meal logging & carbon footprint
- CORS for frontend on localhost:3000/3001
"""

import os
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

# ── Try Gemini SDK ──────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    HAS_GEMINI = bool(GEMINI_API_KEY)
except ImportError:
    HAS_GEMINI = False

# ── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NutriAI — AI Nutrition Analyzer API",
    description="AI-Powered Nutrition Analyzer with LLM chat, RAG, and meal tracking",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://192.168.56.1:3000",
        "http://192.168.56.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Nutrition Knowledge Base ────────────────────────────────────────────────
NUTRITION_DB = {
    "apple": {"calories": 95, "carbs": "25g", "protein": "0.5g", "fat": "0.3g", "fiber": "4.4g", "vitamin_c": "8.4mg"},
    "banana": {"calories": 105, "carbs": "27g", "protein": "1.3g", "fat": "0.4g", "fiber": "3.1g", "potassium": "422mg"},
    "chicken breast": {"calories": 165, "carbs": "0g", "protein": "31g", "fat": "3.6g", "fiber": "0g", "iron": "1mg"},
    "salmon": {"calories": 280, "carbs": "0g", "protein": "25g", "fat": "18g", "fiber": "0g", "omega3": "2.2g"},
    "egg": {"calories": 78, "carbs": "1g", "protein": "6g", "fat": "5g", "fiber": "0g", "choline": "147mg"},
    "milk": {"calories": 150, "carbs": "12g", "protein": "8g", "fat": "8g", "fiber": "0g", "calcium": "276mg"},
    "brown rice": {"calories": 216, "carbs": "45g", "protein": "5g", "fat": "1.8g", "fiber": "3.5g", "magnesium": "84mg"},
    "oatmeal": {"calories": 150, "carbs": "27g", "protein": "5g", "fat": "3g", "fiber": "4g", "iron": "2mg"},
    "almonds": {"calories": 164, "carbs": "6g", "protein": "6g", "fat": "14g", "fiber": "3.5g", "vitamin_e": "7.3mg"},
    "spinach": {"calories": 7, "carbs": "1g", "protein": "1g", "fat": "0.1g", "fiber": "0.7g", "iron": "0.8mg"},
    "broccoli": {"calories": 55, "carbs": "11g", "protein": "3.7g", "fat": "0.6g", "fiber": "5.1g", "vitamin_c": "135mg"},
    "avocado": {"calories": 234, "carbs": "12g", "protein": "2.9g", "fat": "21g", "fiber": "10g", "potassium": "708mg"},
    "quinoa": {"calories": 222, "carbs": "39g", "protein": "8g", "fat": "3.5g", "fiber": "5g", "iron": "2.8mg"},
    "sweet potato": {"calories": 130, "carbs": "31g", "protein": "3g", "fat": "0.1g", "fiber": "4g", "vitamin_a": "1096mcg"},
    "greek yogurt": {"calories": 100, "carbs": "6g", "protein": "17g", "fat": "0.7g", "fiber": "0g", "calcium": "200mg"},
    "lentils": {"calories": 230, "carbs": "40g", "protein": "18g", "fat": "0.8g", "fiber": "16g", "iron": "6.6mg"},
    "blueberries": {"calories": 84, "carbs": "21g", "protein": "1.1g", "fat": "0.5g", "fiber": "3.6g", "vitamin_c": "14mg"},
    "tofu": {"calories": 144, "carbs": "2.5g", "protein": "15g", "fat": "9g", "fiber": "0.3g", "calcium": "350mg"},
    "tuna": {"calories": 154, "carbs": "0g", "protein": "34g", "fat": "1.3g", "fiber": "0g", "selenium": "96mcg"},
    "whole wheat bread": {"calories": 81, "carbs": "15g", "protein": "4g", "fat": "1.1g", "fiber": "1.9g", "iron": "0.9mg"},
}

# CO2 emissions per 100g food (kg CO2 equivalent)
CO2_DB = {
    "beef": 27.0, "lamb": 25.0, "cheese": 13.5, "pork": 12.1, "chicken breast": 6.9,
    "salmon": 6.0, "tuna": 3.8, "egg": 4.5, "milk": 3.2, "tofu": 2.0,
    "rice": 4.0, "brown rice": 4.0, "lentils": 0.9, "beans": 0.8,
    "apple": 0.4, "banana": 0.7, "spinach": 0.5, "broccoli": 0.4,
    "almonds": 3.5, "quinoa": 1.4, "oatmeal": 1.6, "avocado": 2.5,
    "potato": 0.3, "sweet potato": 0.3, "tomato": 1.1,
}

SYSTEM_PROMPT = """You are NutriAI, an expert AI nutrition analyst and wellness coach for the AI-Powered Nutrition Analyzer app. 

Your expertise includes:
- Detailed nutritional analysis of foods and meals
- Personalized dietary recommendations based on health goals (weight loss, muscle gain, energy, longevity)
- Carbon footprint of different foods and eco-friendly eating
- Meal planning and recipe suggestions
- Identifying nutritional deficiencies and how to address them
- Science-backed advice on macros, micros, hydration, and supplementation

Guidelines:
- Always provide specific, actionable nutrition advice
- Include calorie counts, macros (protein/carbs/fat), and key micronutrients when discussing foods
- Mention environmental impact when relevant
- Be warm, encouraging, and science-backed — not preachy
- If discussing a specific food the user mentions, provide its exact nutrition data
- Format responses clearly with bullet points or sections when needed
- Keep responses concise but complete (2-4 paragraphs max unless asked for detail)
- End with a practical tip or follow-up suggestion

Nutrition context from knowledge base:
{nutrition_context}"""


def find_nutrition_context(text: str) -> str:
    """Extract relevant nutrition data from the knowledge base."""
    text_lower = text.lower()
    matched = []
    for food, nutrients in NUTRITION_DB.items():
        if food in text_lower:
            nu_str = ", ".join(f"{k}: {v}" for k, v in nutrients.items())
            matched.append(f"- {food.title()}: {nu_str}")
    if matched:
        return "\n".join(matched)
    return "No specific foods detected. Provide general evidence-based nutrition advice."


def find_co2_context(text: str) -> Optional[dict]:
    """Extract CO2 footprint data."""
    text_lower = text.lower()
    for food, co2 in CO2_DB.items():
        if food in text_lower:
            return {"food": food, "co2_per_100g_kg": co2}
    return None


def extract_food_data(text: str) -> Optional[dict]:
    """Return nutrition data for detected food."""
    text_lower = text.lower()
    for food, data in NUTRITION_DB.items():
        if food in text_lower:
            return {"food": food.title(), **data}
    return None


# ── Request / Response Models ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    model: str = "gemini"
    effort: str = "Medium"
    history: list = []


class ChatResponse(BaseModel):
    response: str
    model: str
    nutrition_info: Optional[dict] = None
    co2_info: Optional[dict] = None
    suggestions: list[str] = []


class NutritionQuery(BaseModel):
    question: str


class MealLogRequest(BaseModel):
    food: str
    portion_grams: float = 100.0
    meal_type: str = "Lunch"


class CarbonRequest(BaseModel):
    food: str
    portion_grams: float = 100.0


# ── Health Check ────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "NutriAI — AI Nutrition Analyzer API",
        "status": "healthy",
        "llm": "gemini" if HAS_GEMINI else "rule-based",
        "version": "1.0.0",
        "endpoints": ["/api/chat", "/api/nutrition/query", "/api/meals/log", "/api/carbon", "/api/user/profile"],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "gemini_enabled": HAS_GEMINI}


# ── Main Chat Endpoint ──────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main NutriAI chat with Gemini LLM or smart rule-based fallback."""
    nutrition_context = find_nutrition_context(request.message)
    nutrition_info = extract_food_data(request.message)
    co2_info = find_co2_context(request.message)

    # Generate follow-up suggestions
    suggestions = _generate_suggestions(request.message, nutrition_info)

    if HAS_GEMINI:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            system = SYSTEM_PROMPT.format(nutrition_context=nutrition_context)

            # Build conversation history
            history = []
            for msg in request.history[-6:]:  # last 3 turns
                if msg.get("role") == "user":
                    history.append({"role": "user", "parts": [msg["content"]]})
                elif msg.get("role") == "assistant":
                    history.append({"role": "model", "parts": [msg["content"]]})

            chat = model.start_chat(history=history)
            resp = chat.send_message(
                f"{system}\n\nUser question: {request.message}"
            )
            response_text = resp.text
        except Exception as e:
            response_text = _rule_based_response(request.message, nutrition_info, co2_info)
            response_text += f"\n\n_Note: AI enhanced mode temporarily unavailable. ({str(e)[:80]})_"
    else:
        response_text = _rule_based_response(request.message, nutrition_info, co2_info)

    return ChatResponse(
        response=response_text,
        model="gemini-2.0-flash" if HAS_GEMINI else "NutriAI Smart",
        nutrition_info=nutrition_info,
        co2_info=co2_info,
        suggestions=suggestions,
    )


def _rule_based_response(message: str, nutrition_info: Optional[dict], co2_info: Optional[dict]) -> str:
    """Smart fallback response when Gemini is not available."""
    msg_lower = message.lower()

    if nutrition_info:
        food = nutrition_info["food"]
        cal = nutrition_info["calories"]
        protein = nutrition_info.get("protein", "N/A")
        carbs = nutrition_info.get("carbs", "N/A")
        fat = nutrition_info.get("fat", "N/A")
        fiber = nutrition_info.get("fiber", "N/A")

        response = f"**{food} — Nutritional Profile**\n\n"
        response += f"Per standard serving: **{cal} calories** | Protein: {protein} | Carbs: {carbs} | Fat: {fat} | Fiber: {fiber}\n\n"

        # Context-aware additions
        if "lose weight" in msg_lower or "diet" in msg_lower:
            response += f"💡 **Weight management tip:** {food} is {'low-calorie and a great choice' if cal < 100 else 'moderate in calories — watch your portion size'}. Pair with high-fiber vegetables to stay satisfied.\n\n"
        elif "muscle" in msg_lower or "protein" in msg_lower:
            protein_g = float(re.sub(r'[^\d.]', '', protein) or '0')
            response += f"💪 **Muscle building:** {'Excellent protein source' if protein_g >= 15 else 'Moderate protein'} — combine with strength training and aim for 1.6-2.2g protein per kg bodyweight daily.\n\n"
        elif "energy" in msg_lower or "tired" in msg_lower:
            response += f"⚡ **Energy tip:** For sustained energy, combine {food} with complex carbs and healthy fats to avoid blood sugar spikes.\n\n"

        if co2_info:
            co2_val = co2_info["co2_per_100g_kg"]
            eco_label = "🟢 Eco-friendly" if co2_val < 2 else "🟡 Moderate impact" if co2_val < 6 else "🔴 High impact"
            response += f"🌍 **Carbon footprint:** {co2_val} kg CO₂ per 100g — {eco_label}\n\n"

        response += f"💬 Want a meal plan featuring {food}, or details on a specific nutrient?"

    elif "carbon" in msg_lower or "co2" in msg_lower or "environment" in msg_lower:
        response = """🌍 **Carbon Footprint of Your Diet**

The food system accounts for ~26% of global greenhouse gas emissions. Here's a quick guide:

| Food Category | CO₂ per 100g |
|---|---|
| 🔴 Beef | 27 kg |
| 🔴 Lamb | 25 kg |
| 🟡 Chicken | 6.9 kg |
| 🟡 Salmon | 6 kg |
| 🟢 Lentils | 0.9 kg |
| 🟢 Vegetables | 0.3–0.7 kg |

**Biggest wins:** Reduce beef, increase legumes (lentils/beans), choose local seasonal produce.

💡 Ask me to calculate the footprint of any specific meal!"""

    elif "calorie" in msg_lower or "calori" in msg_lower:
        response = """📊 **Calorie Guidance**

Daily calorie needs depend on your age, weight, height, and activity level:
- **Sedentary (desk job):** ~2,000–2,200 kcal
- **Moderately active:** ~2,200–2,600 kcal  
- **Very active / athlete:** ~2,600–3,200+ kcal

For **weight loss**, aim for a 300–500 kcal deficit. For **muscle gain**, a 200–300 kcal surplus with high protein.

Ask me about calories for a specific food, or let me help plan your daily meals!"""

    elif "protein" in msg_lower:
        response = """💪 **Protein Fundamentals**

Protein is essential for muscle repair, immune function, and satiety.

**Top high-protein foods per 100g:**
- Tuna: 34g protein
- Chicken breast: 31g protein  
- Greek yogurt: 17g protein
- Lentils: 18g protein
- Tofu: 15g protein
- Eggs: 13g protein

**Daily target:** 1.6–2.2g per kg bodyweight for muscle building, 0.8–1.2g for general health.

Which high-protein foods would you like more info on?"""

    elif "meal plan" in msg_lower or "plan" in msg_lower:
        response = """🗓️ **Sample Balanced Day (2,000 kcal)**

**Breakfast (~400 kcal)**
- Greek yogurt (150g) + blueberries + 30g almonds
- Protein: 20g | Carbs: 25g | Fat: 16g

**Lunch (~550 kcal)**  
- Grilled chicken breast (150g) + brown rice (100g) + steamed broccoli
- Protein: 48g | Carbs: 50g | Fat: 5g

**Snack (~200 kcal)**
- Apple + 20g almond butter
- Protein: 5g | Carbs: 28g | Fat: 10g

**Dinner (~600 kcal)**
- Salmon (150g) + quinoa (80g) + spinach salad with avocado
- Protein: 42g | Carbs: 40g | Fat: 25g

This plan provides ~2,000 kcal, 115g protein, 143g carbs, 56g fat.

Want me to customize this for your specific goals?"""

    else:
        response = """👋 **Welcome to NutriAI!**

I'm your personal AI nutrition analyst. I can help you with:

🥗 **Nutrition Analysis** — calories, macros, micros for any food
🌍 **Carbon Footprint** — environmental impact of your meals  
💪 **Goal Planning** — weight loss, muscle gain, energy optimization
🗓️ **Meal Planning** — personalized daily meal plans
🔬 **Science-backed advice** — evidence-based dietary guidance

**Try asking:**
- "How many calories in grilled chicken breast?"
- "What's the protein content of Greek yogurt?"
- "Create a high-protein meal plan for muscle gain"
- "What's the carbon footprint of my beef dinner?"
- "Am I eating enough fiber?"

What would you like to know about your nutrition today?"""

    return response


def _generate_suggestions(message: str, nutrition_info: Optional[dict]) -> list[str]:
    """Generate contextual follow-up suggestions."""
    msg_lower = message.lower()

    if nutrition_info:
        food = nutrition_info["food"]
        return [
            f"Best way to cook {food}?",
            f"Meal plan featuring {food}",
            f"Carbon footprint of {food}",
            f"Alternatives to {food}",
        ]
    elif "calorie" in msg_lower:
        return ["How to count calories?", "Low calorie meal ideas", "Calorie deficit for weight loss"]
    elif "protein" in msg_lower:
        return ["High protein breakfast ideas", "Best plant-based proteins", "How much protein do I need?"]
    elif "carbon" in msg_lower or "co2" in msg_lower:
        return ["Most eco-friendly foods", "Plant-based meal plan", "How to reduce diet carbon footprint"]
    else:
        return [
            "What are macros?",
            "Create a meal plan for me",
            "Best foods for weight loss",
            "High protein meal ideas",
        ]


# ── Nutrition Query Endpoint ─────────────────────────────────────────────────
@app.post("/api/nutrition/query")
async def nutrition_query(query: NutritionQuery):
    """Nutrition-specific query endpoint."""
    nutrition_info = extract_food_data(query.question)
    co2_info = find_co2_context(query.question)

    if nutrition_info:
        food = nutrition_info["food"]
        details = {k: v for k, v in nutrition_info.items() if k != "food"}
        response = f"**{food}** nutrition breakdown:\n"
        for key, val in details.items():
            response += f"- {key.replace('_', ' ').title()}: {val}\n"
    else:
        response = "I don't have specific data for that food. Try: apple, banana, chicken breast, salmon, egg, brown rice, almonds, spinach, broccoli, avocado, quinoa, Greek yogurt, lentils, tofu, tuna."

    return {
        "response": response,
        "nutrition_info": nutrition_info,
        "co2_info": co2_info,
    }


# ── Meal Log Endpoint ───────────────────────────────────────────────────────
@app.post("/api/meals/log")
async def log_meal(meal: MealLogRequest):
    """Log a meal and get nutritional summary."""
    food_key = meal.food.lower()
    nutrition = NUTRITION_DB.get(food_key)
    scaling = meal.portion_grams / 100.0

    if nutrition:
        scaled = {
            "food": meal.food.title(),
            "portion_grams": meal.portion_grams,
            "meal_type": meal.meal_type,
            "calories": round(nutrition["calories"] * scaling, 1),
            "protein": f"{round(float(re.sub(r'[^\d.]', '', nutrition['protein'])) * scaling, 1)}g",
            "carbs": f"{round(float(re.sub(r'[^\d.]', '', nutrition['carbs'])) * scaling, 1)}g",
            "fat": f"{round(float(re.sub(r'[^\d.]', '', nutrition['fat'])) * scaling, 1)}g",
        }
        co2 = CO2_DB.get(food_key, 1.0) * scaling
        return {
            "status": "logged",
            "meal_id": f"meal_{hash(meal.food + str(meal.portion_grams)) % 100000}",
            "summary": scaled,
            "co2_kg": round(co2 / 1000, 4),
        }

    return {
        "status": "logged",
        "meal_id": "meal_unknown",
        "summary": {"food": meal.food, "portion_grams": meal.portion_grams, "meal_type": meal.meal_type},
        "message": f"Food '{meal.food}' not in database. Logged without nutrition details.",
    }


# ── Carbon Footprint Endpoint ───────────────────────────────────────────────
@app.post("/api/carbon")
async def carbon_footprint(req: CarbonRequest):
    """Calculate carbon footprint of a food item."""
    food_key = req.food.lower()
    co2_per_100g = CO2_DB.get(food_key)

    if co2_per_100g is None:
        # Try partial match
        for key in CO2_DB:
            if key in food_key or food_key in key:
                co2_per_100g = CO2_DB[key]
                food_key = key
                break

    if co2_per_100g is not None:
        total_co2 = co2_per_100g * (req.portion_grams / 100)
        eco_rating = "excellent" if co2_per_100g < 1 else "good" if co2_per_100g < 3 else "moderate" if co2_per_100g < 8 else "high"
        return {
            "food": req.food,
            "portion_grams": req.portion_grams,
            "co2_kg": round(total_co2, 4),
            "eco_rating": eco_rating,
            "tip": _eco_tip(co2_per_100g, req.food),
        }

    return {
        "food": req.food,
        "portion_grams": req.portion_grams,
        "co2_kg": None,
        "eco_rating": "unknown",
        "tip": "Try plant-based options like lentils, beans, or vegetables for the lowest carbon footprint.",
    }


def _eco_tip(co2: float, food: str) -> str:
    if co2 < 1:
        return f"{food.title()} is one of the most planet-friendly foods you can eat. Great choice! 🌿"
    elif co2 < 3:
        return f"{food.title()} has a moderate footprint. Pair with vegetables to balance it out."
    elif co2 < 8:
        return f"Consider reducing {food.lower()} frequency. Swapping one serving per week for lentils saves ~1.5 kg CO₂."
    else:
        return f"High environmental impact. Consider plant-based alternatives — beans, lentils, or tofu have 10–30x lower emissions."


# ── User Profile Endpoint ───────────────────────────────────────────────────
@app.get("/api/user/profile")
async def get_user_profile():
    return {
        "user": "demo_user",
        "name": "Alex",
        "goals": {
            "calories": 2000,
            "protein": "120g",
            "carbs": "220g",
            "fat": "65g",
            "water_ml": 2500,
        },
        "stats": {
            "meals_logged": 42,
            "streak_days": 7,
            "co2_saved_kg": 12.4,
            "avg_daily_calories": 1890,
        },
        "plan": "Balanced Wellness",
    }


if __name__ == "__main__":
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)