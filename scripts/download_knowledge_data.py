"""
Download free knowledge datasets to enrich Monica's knowledge base.
All sources are free, no API keys required.
"""
import json
import os
import sys
import urllib.request
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "data" / "Monica_Knowledge_Base"
DOWNLOADED_DIR = KB_DIR / "downloaded_datasets"
DOWNLOADED_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url, timeout=15):
    """Fetch JSON from a URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return None


def save_dataset(name, data, description=""):
    """Save a dataset to the downloaded_datasets folder."""
    path = DOWNLOADED_DIR / f"{name}.json"
    envelope = {
        "dataset": name,
        "description": description,
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "free public API",
        "data": data,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, indent=2, ensure_ascii=False)
    size_kb = path.stat().st_size / 1024
    print(f"  [OK] {name}: {size_kb:.0f} KB saved")
    return True


def download_all():
    print("=" * 60)
    print("DOWNLOADING FREE KNOWLEDGE DATASETS FOR MONICA")
    print("=" * 60)
    count = 0

    # 1. Nobel Prizes (complete history)
    print("\n1. Nobel Prizes...")
    data = fetch_json("https://api.nobelprize.org/2.1/nobelPrizes?limit=500")
    if data:
        prizes = data.get("nobelPrizes", [])
        save_dataset("nobel_prizes", prizes, "Complete Nobel Prize history")
        count += 1

    # 2. Countries of the world
    print("\n2. Countries of the world...")
    data = fetch_json("https://restcountries.com/v3.1/all?fields=name,capital,population,region,subregion,languages,currencies,timezones,flags,latlng,area")
    if data:
        save_dataset("countries_of_world", data, "All countries with capitals, population, languages, currencies")
        count += 1

    # 3. US Presidents
    print("\n3. US historical data...")
    # Use a simple known dataset
    presidents = [
        {"number": 1, "name": "George Washington", "years": "1789-1797", "party": "None"},
        {"number": 2, "name": "John Adams", "years": "1797-1801", "party": "Federalist"},
        {"number": 3, "name": "Thomas Jefferson", "years": "1801-1809", "party": "Democratic-Republican"},
        {"number": 16, "name": "Abraham Lincoln", "years": "1861-1865", "party": "Republican"},
        {"number": 26, "name": "Theodore Roosevelt", "years": "1901-1909", "party": "Republican"},
        {"number": 32, "name": "Franklin D. Roosevelt", "years": "1933-1945", "party": "Democratic"},
        {"number": 35, "name": "John F. Kennedy", "years": "1961-1963", "party": "Democratic"},
        {"number": 44, "name": "Barack Obama", "years": "2009-2017", "party": "Democratic"},
        {"number": 45, "name": "Donald Trump", "years": "2017-2021, 2025-", "party": "Republican"},
        {"number": 46, "name": "Joe Biden", "years": "2021-2025", "party": "Democratic"},
    ]
    save_dataset("us_presidents_key", presidents, "Key US Presidents")
    count += 1

    # 4. Periodic Table of Elements
    print("\n4. Periodic Table...")
    data = fetch_json("https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json")
    if data:
        save_dataset("periodic_table", data.get("elements", data), "Complete periodic table of elements")
        count += 1

    # 5. World universities
    print("\n5. Top universities...")
    data = fetch_json("http://universities.hipolabs.com/search?limit=200")
    if data:
        save_dataset("world_universities", data[:200], "Top 200 world universities")
        count += 1

    # 6. Programming languages
    print("\n6. Programming languages...")
    langs = [
        {"name": "Python", "paradigm": "Multi-paradigm", "year": 1991, "creator": "Guido van Rossum", "use": "AI, web, data science, automation"},
        {"name": "JavaScript", "paradigm": "Multi-paradigm", "year": 1995, "creator": "Brendan Eich", "use": "Web development, full-stack"},
        {"name": "Java", "paradigm": "Object-oriented", "year": 1995, "creator": "James Gosling", "use": "Enterprise, Android, backend"},
        {"name": "C++", "paradigm": "Multi-paradigm", "year": 1985, "creator": "Bjarne Stroustrup", "use": "Systems, games, performance"},
        {"name": "C#", "paradigm": "Object-oriented", "year": 2000, "creator": "Microsoft/Anders Hejlsberg", "use": "Unity, .NET, enterprise"},
        {"name": "TypeScript", "paradigm": "Multi-paradigm", "year": 2012, "creator": "Microsoft", "use": "Web development, large-scale JS"},
        {"name": "Rust", "paradigm": "Multi-paradigm", "year": 2015, "creator": "Graydon Hoare/Mozilla", "use": "Systems, WebAssembly, safety-critical"},
        {"name": "Go", "paradigm": "Concurrent", "year": 2009, "creator": "Google", "use": "Cloud, microservices, DevOps"},
        {"name": "Swift", "paradigm": "Multi-paradigm", "year": 2014, "creator": "Apple", "use": "iOS/macOS development"},
        {"name": "Kotlin", "paradigm": "Multi-paradigm", "year": 2011, "creator": "JetBrains", "use": "Android, backend"},
        {"name": "R", "paradigm": "Functional", "year": 1993, "creator": "Ross Ihaka, Robert Gentleman", "use": "Statistics, data analysis"},
        {"name": "SQL", "paradigm": "Declarative", "year": 1974, "creator": "IBM", "use": "Database querying"},
        {"name": "PHP", "paradigm": "Multi-paradigm", "year": 1995, "creator": "Rasmus Lerdorf", "use": "Web backend, WordPress"},
        {"name": "Ruby", "paradigm": "Object-oriented", "year": 1995, "creator": "Yukihiro Matsumoto", "use": "Web (Rails), scripting"},
    ]
    save_dataset("programming_languages", langs, "Major programming languages with details")
    count += 1

    # 7. Common medical conditions (educational, non-diagnostic)
    print("\n7. Medical knowledge (educational)...")
    medical = {
        "common_conditions": [
            {"name": "Hypertension", "also_known_as": "High blood pressure", "prevalence": "~1.3 billion worldwide", "risk_factors": ["obesity", "high sodium diet", "stress", "family history"], "when_to_see_doctor": "BP consistently above 130/80"},
            {"name": "Type 2 Diabetes", "prevalence": "~422 million worldwide", "risk_factors": ["obesity", "sedentary lifestyle", "family history", "age"], "symptoms": ["increased thirst", "frequent urination", "fatigue", "blurred vision"]},
            {"name": "Anxiety Disorders", "prevalence": "~301 million worldwide", "types": ["Generalized Anxiety", "Social Anxiety", "Panic Disorder", "PTSD"], "treatments": ["CBT", "medication", "mindfulness", "exercise"]},
            {"name": "Depression", "prevalence": "~280 million worldwide", "symptoms": ["persistent sadness", "loss of interest", "fatigue", "sleep changes", "appetite changes"], "treatments": ["therapy", "medication", "exercise", "social support"]},
            {"name": "Asthma", "prevalence": "~262 million worldwide", "triggers": ["allergens", "exercise", "cold air", "pollution"], "management": ["inhalers", "avoiding triggers", "action plan"]},
        ],
        "first_aid_basics": [
            {"situation": "Choking", "action": "Heimlich maneuver (abdominal thrusts), call 911 if unresponsive"},
            {"situation": "Bleeding", "action": "Apply direct pressure with clean cloth, elevate, call 911 for severe"},
            {"situation": "Burns", "action": "Cool under running water 10-20 min, do NOT use ice, cover loosely"},
            {"situation": "Heart Attack Signs", "action": "Call 911 immediately. Chest pain/pressure, shortness of breath, arm/jaw pain"},
            {"situation": "Stroke Signs (FAST)", "action": "Face drooping, Arm weakness, Speech difficulty, Time to call 911"},
        ],
        "disclaimer": "This information is for educational purposes only. Always consult a healthcare professional for medical advice."
    }
    save_dataset("medical_knowledge_basics", medical, "Common conditions and first aid basics (educational)")
    count += 1

    # 8. Major historical events
    print("\n8. Historical events...")
    history = [
        {"year": -3000, "event": "Ancient Egyptian civilization flourishes along the Nile"},
        {"year": -776, "event": "First Olympic Games held in Olympia, Greece"},
        {"year": -509, "event": "Roman Republic established"},
        {"year": -27, "event": "Roman Empire begins under Augustus"},
        {"year": 476, "event": "Fall of the Western Roman Empire"},
        {"year": 1066, "event": "Norman Conquest of England"},
        {"year": 1215, "event": "Magna Carta signed in England"},
        {"year": 1347, "event": "Black Death reaches Europe"},
        {"year": 1453, "event": "Fall of Constantinople to the Ottoman Empire"},
        {"year": 1492, "event": "Christopher Columbus reaches the Americas"},
        {"year": 1517, "event": "Martin Luther posts 95 Theses, Protestant Reformation begins"},
        {"year": 1776, "event": "United States Declaration of Independence"},
        {"year": 1789, "event": "French Revolution begins"},
        {"year": 1804, "event": "Napoleon crowned Emperor of France"},
        {"year": 1865, "event": "US Civil War ends, slavery abolished (13th Amendment)"},
        {"year": 1903, "event": "Wright Brothers achieve first powered flight"},
        {"year": 1914, "event": "World War I begins"},
        {"year": 1929, "event": "Stock market crash, Great Depression begins"},
        {"year": 1939, "event": "World War II begins"},
        {"year": 1945, "event": "WWII ends, United Nations founded, atomic bombs dropped"},
        {"year": 1947, "event": "India gains independence from Britain"},
        {"year": 1969, "event": "Apollo 11: First humans walk on the Moon"},
        {"year": 1989, "event": "Fall of the Berlin Wall"},
        {"year": 1991, "event": "Dissolution of the Soviet Union, World Wide Web launched"},
        {"year": 2001, "event": "September 11 attacks on the United States"},
        {"year": 2008, "event": "Global financial crisis, Barack Obama elected US President"},
        {"year": 2020, "event": "COVID-19 pandemic begins worldwide"},
        {"year": 2022, "event": "Russia invades Ukraine, ChatGPT released"},
        {"year": 2023, "event": "GPT-4 released, AI boom accelerates"},
        {"year": 2024, "event": "Paris Olympics, Trump wins US election, Claude 3.5 and GPT-4o released"},
        {"year": 2025, "event": "DeepSeek R1, Claude 3.5 Sonnet, Llama 3.3, continued AI advancement"},
    ]
    save_dataset("major_historical_events", history, "Key historical events from ancient times to 2025")
    count += 1

    # 9. AI/Tech knowledge 2024-2025
    print("\n9. AI/Tech current knowledge...")
    tech = {
        "ai_models_2024_2025": [
            {"name": "GPT-4o", "company": "OpenAI", "year": 2024, "type": "Multimodal LLM", "notes": "Omni model - text, vision, audio natively"},
            {"name": "GPT-4o mini", "company": "OpenAI", "year": 2024, "type": "Efficient LLM", "notes": "Cost-effective, replaces GPT-3.5"},
            {"name": "Claude 3.5 Sonnet", "company": "Anthropic", "year": 2024, "type": "LLM", "notes": "Strong coding and reasoning"},
            {"name": "Claude 3.5 Haiku", "company": "Anthropic", "year": 2024, "type": "Fast LLM"},
            {"name": "Gemini 2.0", "company": "Google", "year": 2024, "type": "Multimodal LLM"},
            {"name": "Llama 3.3 70B", "company": "Meta", "year": 2024, "type": "Open-source LLM"},
            {"name": "DeepSeek R1", "company": "DeepSeek", "year": 2025, "type": "Reasoning LLM", "notes": "Open-source reasoning model from China"},
            {"name": "Stable Diffusion 3.5", "company": "Stability AI", "year": 2024, "type": "Image generation"},
            {"name": "DALL-E 3", "company": "OpenAI", "year": 2024, "type": "Image generation"},
            {"name": "Sora", "company": "OpenAI", "year": 2024, "type": "Video generation"},
            {"name": "Whisper v3", "company": "OpenAI", "year": 2024, "type": "Speech recognition"},
        ],
        "tech_trends_2025": [
            "AI agents and autonomous systems",
            "Multimodal AI (text + vision + audio)",
            "Open-source AI models competing with proprietary",
            "AI in healthcare diagnostics",
            "Edge AI and on-device inference",
            "Quantum computing progress",
            "AR/VR spatial computing (Apple Vision Pro)",
            "Robotics advancement (humanoid robots)",
            "Electric vehicles and autonomous driving",
            "Brain-computer interfaces",
        ],
    }
    save_dataset("ai_tech_2024_2025", tech, "Current AI models and tech trends 2024-2025")
    count += 1

    # 10. Useful math formulas
    print("\n10. Math formulas...")
    math_data = {
        "algebra": [
            {"name": "Quadratic Formula", "formula": "x = (-b +/- sqrt(b^2 - 4ac)) / 2a", "use": "Solving ax^2 + bx + c = 0"},
            {"name": "Slope-Intercept", "formula": "y = mx + b", "use": "Linear equations"},
            {"name": "Point-Slope", "formula": "y - y1 = m(x - x1)", "use": "Line through a point"},
        ],
        "geometry": [
            {"name": "Circle Area", "formula": "A = pi * r^2"},
            {"name": "Circle Circumference", "formula": "C = 2 * pi * r"},
            {"name": "Triangle Area", "formula": "A = (1/2) * base * height"},
            {"name": "Pythagorean Theorem", "formula": "a^2 + b^2 = c^2"},
            {"name": "Sphere Volume", "formula": "V = (4/3) * pi * r^3"},
        ],
        "calculus": [
            {"name": "Power Rule", "formula": "d/dx [x^n] = n*x^(n-1)"},
            {"name": "Chain Rule", "formula": "d/dx [f(g(x))] = f'(g(x)) * g'(x)"},
            {"name": "Integration by Parts", "formula": "integral(u dv) = uv - integral(v du)"},
        ],
        "statistics": [
            {"name": "Mean", "formula": "sum(x_i) / n"},
            {"name": "Standard Deviation", "formula": "sqrt(sum((x_i - mean)^2) / n)"},
            {"name": "Normal Distribution", "formula": "f(x) = (1/(sigma*sqrt(2*pi))) * e^(-(x-mu)^2 / (2*sigma^2))"},
        ],
    }
    save_dataset("math_formulas", math_data, "Common math formulas by category")
    count += 1

    print(f"\n{'='*60}")
    print(f"Downloaded {count} knowledge datasets to:")
    print(f"  {DOWNLOADED_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    download_all()
