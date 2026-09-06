import re

# Read the file
with open(r'd:\AI-Powered Nutrition Analyzer\backend\index.py', 'r') as f:
    content = f.read()

# Find the position after extract_food_data function
# Look for the def _rule_based_response line
idx = content.find('def _rule_based_response')
if idx > 0:
    # Define the feature engineering function
    features_func = """

def extract_query_features(message: str) -> dict:
    \"\"\"Extract features from user query for enhanced responses.\"\"\"
    features = {
        "food": None,
        "portion_factor": 1.0,
        "target_nutrients": [],
        "co2_request": False,
        "goal": "general",
    }

    msg = message.lower()

    # Extract food from database
    food_data = extract_food_data(message)
    if food_data:
        features["food"] = food_data.get("food")

    # Extract portion factor (e.g., "200g" -> 2.0)
    m = re.search(r'(\d+(?:\.\d+)?)\s*g', msg)
    if m:
        features["portion_factor"] = float(m.group(1)) / 100.0

    # Extract target nutrients
    for nutrient in ["calorie", "protein", "carbs", "fat", "fiber", "vitamin"]:
        if nutrient in msg:
            features["target_nutrients"].append(nutrient)

    # CO2 request flag
    if any(w in msg for w in ["carbon", "co2", "eco", "environment"]):
        features["co2_request"] = True

    # Goal detection
    if any(w in msg for w in ["weight loss", "diet", "lose"]):
        features["goal"] = "weight loss"
    elif any(w in msg for w in ["muscle", "protein", "gain"]):
        features["goal"] = "muscle gain"
    elif any(w in msg for w in ["energy", "tired", "boost"]):
        features["goal"] = "energy"

    return features
"""

    # Insert before def _rule_based_response
    new_content = content[:idx] + features_func + content[idx:]
    
    with open(r'd:\AI-Powered Nutrition Analyzer\backend\index.py', 'w') as f:
        f.write(new_content)
    
    print('Feature engineering function added successfully')
else:
    print('Could not find insertion point')