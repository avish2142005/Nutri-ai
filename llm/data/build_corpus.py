"""
Generates the agricultural pretraining corpus and instruction fine-tuning dataset
from KrishiNetra knowledge base, agronomic rules, and IPM standards.
"""
import json
import os
from typing import List, Dict

def generate_agricultural_datasets():
    os.makedirs("llm/data", exist_ok=True)
    
    # 1. Load diseases.json
    kb_path = "farmai/backend/knowledge_base/diseases.json"
    with open(kb_path, "r", encoding="utf-8") as f:
        diseases = json.load(f)

    # 2. Load chunks.json
    chunks_path = "farmai/backend/knowledge_base/chunks.json"
    chunks = []
    if os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

    corpus_paragraphs = []
    sft_pairs = []

    # Process all disease profiles
    for disease_id, d in diseases.items():
        name = d.get("name", disease_id)
        sc_name = d.get("scientific_name", "")
        ctype = d.get("condition_type", "fungal")
        crops = ", ".join(d.get("affected_crops", []))
        symptoms = d.get("symptoms", "")
        favorable = d.get("favourable_conditions", {})
        temp = favorable.get("temperature", "")
        humidity = favorable.get("humidity", "")
        leaf_wet = favorable.get("leaf_wetness_hours", "")
        rain = favorable.get("rainfall", "")

        ipm = d.get("ipm_recommendations", {})
        cultural = ipm.get("cultural", [])
        biological = ipm.get("biological", [])
        chemical = ipm.get("chemical", [])
        prevention = ipm.get("prevention", [])

        # Build detailed knowledge paragraph
        para = f"""Disease Profile: {name} ({sc_name}).
Type: {ctype.capitalize()} pathogen affecting crops including {crops}.
Symptoms: {symptoms}
Environmental Triggers: Optimal temperature range is {temp}, relative humidity above {humidity}, requiring {leaf_wet} hours of leaf wetness and {rain}.
Integrated Pest Management (IPM) Strategy:
1. Cultural Controls: {'; '.join(cultural) if cultural else 'Maintain field hygiene and crop rotation.'}
2. Biological Controls: {'; '.join(biological) if biological else 'Apply Trichoderma viride or neem formulation.'}
3. Chemical Controls: {'; '.join(chemical) if chemical else 'Consult local agricultural extension.'}
4. Prevention: {'; '.join(prevention) if prevention else 'Use certified disease-resistant seeds.'}
"""
        corpus_paragraphs.append(para)

        # Build SFT Instruction Pairs
        sft_pairs.append({
            "prompt": f"What are the symptoms and causes of {name}?",
            "response": f"{name} ({sc_name}) is a {ctype} disease affecting {crops}. Symptoms include: {symptoms}. It thrives when temperatures are {temp} and humidity exceeds {humidity}."
        })
        sft_pairs.append({
            "prompt": f"How do I manage and treat {name} using IPM methods?",
            "response": f"For {name}, follow this Integrated Pest Management (IPM) plan:\n- Cultural: {'; '.join(cultural[:2])}\n- Biological: {'; '.join(biological[:2]) if biological else 'Use Trichoderma or neem formulations'}\n- Chemical: {'; '.join(chemical[:2]) if chemical else 'Apply copper-based fungicides with proper PPE'}\nAlways verify chemical dosage with your local Krishi Vigyan Kendra (KVK)."
        })
        sft_pairs.append({
            "prompt": f"What weather conditions trigger {name} outbreaks?",
            "response": f"{name} outbreaks are favored by temperatures between {temp}, relative humidity above {humidity}, and leaf wetness exceeding {leaf_wet} hours."
        })

    # Add agronomic domain text from chunks
    for chunk in chunks:
        if isinstance(chunk, dict):
            text = chunk.get("text", "").strip()
        else:
            text = str(chunk).strip()
        if text and len(text) > 40:
            corpus_paragraphs.append(text)

    # Add foundational agricultural science principles
    foundations = [
        "Nitrogen (N) Deficiency: Characterized by general yellowing (chlorosis) of older lower leaves first, stunted vegetative growth, and thin stems. Remediation: Apply urea top-dressing (25-30 kg/ha) or neem-coated urea, supplemented with organic compost.",
        "Phosphorus (P) Deficiency: Manifests as dark green to purplish anthocyanin pigmentation along leaf veins and petioles, delayed maturity, and poor root development. Remediation: Band application of Single Superphosphate (SSP) or Diammonium Phosphate (DAP) at root zone.",
        "Calcium (Ca) Deficiency: Causes apical blossom-end rot in tomatoes, tip-burn in leafy greens, and distorted growing shoot tips due to poor cell wall pectate synthesis. Remediation: Foliar spray of calcium nitrate (0.5%) and maintaining uniform soil moisture.",
        "Soil Moisture and Smart Irrigation: Sandy loam soils require frequent light irrigations (40-60% field capacity), while clay soils need deeper, less frequent watering to prevent root hypoxia. Drip irrigation saves 40-50% water and minimizes leaf wetness that triggers fungal pathogens.",
        "Satellite NDVI Vegetation Monitoring: Normalized Difference Vegetation Index (NDVI) is computed as (NIR - Red) / (NIR + Red). Values between 0.6 and 0.8 indicate vigorous green biomass. Drops below 0.35 signify severe drought stress, waterlogging, or pest infestation.",
        "Integrated Pest Management (IPM) Principles: IPM combines cultural sanitation, physical barriers, biological antagonists (Trichoderma, Bacillus subtilis, Chrysoperla), economic threshold scouting, and judicious chemical application as a last resort to minimize environmental toxicity.",
        "Weather and Plant Epidemiology: High relative humidity (>80%) combined with temperatures between 20-28°C accelerates conidial germination and zoospore mobility in blights. Wind gusts above 15 km/h disperse fungal spores across neighboring plots.",
    ]
    corpus_paragraphs.extend(foundations)

    for item in foundations:
        title, details = item.split(":", 1)
        sft_pairs.append({
            "prompt": f"Explain {title.strip()} and its management.",
            "response": details.strip()
        })

    # 3. Write raw_corpus.txt
    raw_corpus_path = "llm/data/raw_corpus.txt"
    with open(raw_corpus_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(corpus_paragraphs))

    # 4. Write sft_data.jsonl
    sft_data_path = "llm/data/sft_data.jsonl"
    with open(sft_data_path, "w", encoding="utf-8") as f:
        for pair in sft_pairs:
            # Format using standard chat template
            formatted = {
                "text": f"<|im_start|>user\n{pair['prompt']}<|im_end|>\n<|im_start|>assistant\n{pair['response']}<|im_end|>"
            }
            f.write(json.dumps(formatted) + "\n")

    print(f"Generated pretraining corpus: {len(corpus_paragraphs)} sections -> {raw_corpus_path}")
    print(f"Generated SFT dataset: {len(sft_pairs)} instruction pairs -> {sft_data_path}")

if __name__ == "__main__":
    generate_agricultural_datasets()
