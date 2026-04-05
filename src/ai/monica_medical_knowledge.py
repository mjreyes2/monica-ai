"""
Monica's Comprehensive Medical Knowledge Base
For informational purposes only - NOT a substitute for professional medical advice.

DISCLAIMER: This is for educational purposes only. Always consult a healthcare professional.
Monica will always recommend seeing appropriate medical professionals.
"""

import requests
from typing import Dict, List, Optional, Any, Tuple

# ============================================================================
# EMERGENCY SYMPTOMS - CALL 911 IMMEDIATELY
# ============================================================================

EMERGENCY_SYMPTOMS = {
    "heart_attack": {
        "symptoms": ["chest pain", "chest pressure", "crushing chest pain", "pain radiating to arm",
                    "pain radiating to jaw", "shortness of breath with chest pain", "cold sweat",
                    "nausea with chest pain", "lightheaded with chest pain"],
        "action": "CALL 911 IMMEDIATELY",
        "description": "Possible heart attack - every minute counts",
        "specialist": "Emergency Room / Cardiologist",
        "while_waiting": ["Chew aspirin if not allergic", "Sit or lie down", "Loosen tight clothing",
                         "Stay calm", "Don't drive yourself", "Don't eat or drink"]
    },
    "stroke": {
        "symptoms": ["sudden numbness one side", "face drooping", "arm weakness one side",
                    "speech difficulty sudden", "confusion sudden", "severe headache sudden",
                    "vision loss sudden", "trouble walking sudden", "dizziness severe"],
        "action": "CALL 911 IMMEDIATELY - Remember FAST: Face, Arms, Speech, Time",
        "description": "Stroke symptoms - brain damage increases every minute without treatment",
        "specialist": "Emergency Room / Neurologist",
        "while_waiting": ["Note time symptoms started", "Don't give food or water",
                         "Keep person comfortable", "Don't let them sleep"]
    },
    "severe_allergic_reaction": {
        "symptoms": ["throat swelling", "tongue swelling", "can't breathe", "hives all over",
                    "anaphylaxis", "face swelling", "difficulty swallowing"],
        "action": "CALL 911 IMMEDIATELY - Use EpiPen if available",
        "description": "Anaphylaxis - life-threatening allergic reaction",
        "specialist": "Emergency Room / Allergist",
        "while_waiting": ["Use EpiPen if available", "Lie down with legs elevated",
                         "Loosen tight clothing", "Don't give oral medications"]
    },
    "severe_bleeding": {
        "symptoms": ["uncontrolled bleeding", "blood won't stop", "deep wound",
                    "arterial bleeding", "blood spurting", "losing a lot of blood"],
        "action": "CALL 911 IMMEDIATELY",
        "description": "Severe blood loss can be life-threatening",
        "specialist": "Emergency Room / Trauma Surgeon",
        "while_waiting": ["Apply direct pressure", "Elevate wound above heart",
                         "Don't remove embedded objects", "Apply tourniquet if trained"]
    },
    "difficulty_breathing": {
        "symptoms": ["can't breathe", "gasping for air", "lips turning blue", "choking",
                    "severe asthma attack", "can't speak full sentences"],
        "action": "CALL 911 IMMEDIATELY",
        "description": "Respiratory emergency",
        "specialist": "Emergency Room / Pulmonologist",
        "while_waiting": ["Sit upright", "Use inhaler if available", "Loosen clothing",
                         "Open windows", "Stay calm"]
    },
    "seizure": {
        "symptoms": ["convulsions", "seizure", "uncontrollable shaking", "foaming at mouth",
                    "loss of consciousness with shaking", "epileptic episode"],
        "action": "CALL 911 if seizure lasts more than 5 minutes or person doesn't wake up",
        "description": "Seizure - protect from injury",
        "specialist": "Emergency Room / Neurologist",
        "while_waiting": ["Clear area of dangerous objects", "Don't restrain",
                         "Don't put anything in mouth", "Turn on side after seizure stops",
                         "Time the seizure"]
    },
    "suicidal": {
        "symptoms": ["want to kill myself", "suicidal thoughts", "want to die", "end my life",
                    "no reason to live", "better off dead", "planning suicide"],
        "action": "CALL 988 (Suicide Hotline) or 911 IMMEDIATELY",
        "description": "Mental health emergency - help is available",
        "specialist": "Emergency Room / Psychiatrist / Crisis Counselor",
        "while_waiting": ["Stay with the person", "Remove access to weapons/pills",
                         "Listen without judgment", "988 is available 24/7"]
    },
    "overdose": {
        "symptoms": ["overdose", "took too many pills", "drug overdose", "can't wake up",
                    "slow breathing", "blue lips", "unresponsive"],
        "action": "CALL 911 IMMEDIATELY - Administer Narcan if available",
        "description": "Drug overdose - time critical",
        "specialist": "Emergency Room / Toxicologist",
        "while_waiting": ["Give Narcan if available", "Turn on side", "Don't leave alone",
                         "Tell 911 what was taken"]
    }
}

# ============================================================================
# COMMON SYMPTOMS AND CONDITIONS
# ============================================================================

SYMPTOMS_DATABASE = {
    # HEAD & NEUROLOGICAL
    "headache": {
        "common_causes": ["tension headache", "migraine", "dehydration", "eye strain",
                         "sinus pressure", "stress", "lack of sleep", "caffeine withdrawal"],
        "serious_causes": ["meningitis", "brain tumor", "aneurysm", "stroke"],
        "questions": ["How long have you had it?", "Where is the pain located?",
                     "Is it throbbing or constant?", "Any vision changes?",
                     "Fever or stiff neck?", "Worst headache of your life?"],
        "red_flags": ["worst headache ever", "sudden severe onset", "fever with stiff neck",
                     "confusion", "vision changes", "weakness"],
        "home_care": ["Rest in dark quiet room", "Stay hydrated", "OTC pain relievers",
                     "Cold compress", "Reduce screen time"],
        "see_doctor_if": ["Persists more than 3 days", "Recurring frequently",
                         "Interferes with daily life", "OTC meds don't help"],
        "specialist": "Neurologist (for chronic/severe) or Primary Care"
    },
    "dizziness": {
        "common_causes": ["dehydration", "low blood sugar", "inner ear issues", "anxiety",
                         "medication side effect", "standing up too fast"],
        "serious_causes": ["stroke", "heart arrhythmia", "brain tumor"],
        "questions": ["Does the room spin or do you feel faint?", "When does it happen?",
                     "Any hearing changes?", "New medications?", "Chest pain?"],
        "red_flags": ["chest pain", "slurred speech", "weakness one side", "severe headache"],
        "home_care": ["Sit or lie down", "Stay hydrated", "Eat something", "Move slowly"],
        "see_doctor_if": ["Frequent episodes", "Falls", "Hearing loss", "Persists"],
        "specialist": "ENT (ear issues) / Neurologist / Cardiologist"
    },
    
    # RESPIRATORY
    "cough": {
        "common_causes": ["cold", "flu", "allergies", "post-nasal drip", "acid reflux",
                         "dry air", "asthma"],
        "serious_causes": ["pneumonia", "bronchitis", "COVID-19", "lung cancer", "TB"],
        "questions": ["How long?", "Productive or dry?", "Color of mucus?", "Fever?",
                     "Shortness of breath?", "Blood in mucus?", "Smoker?"],
        "red_flags": ["coughing blood", "high fever", "can't breathe", "chest pain",
                     "lasting more than 3 weeks"],
        "home_care": ["Honey and warm liquids", "Humidifier", "Rest", "Stay hydrated",
                     "OTC cough medicine"],
        "see_doctor_if": ["Lasts more than 2 weeks", "Fever over 101°F", "Blood in mucus",
                         "Difficulty breathing"],
        "specialist": "Pulmonologist (lung) / Primary Care"
    },
    "sore_throat": {
        "common_causes": ["viral infection", "cold", "flu", "allergies", "dry air",
                         "acid reflux", "strep throat"],
        "serious_causes": ["strep throat", "mono", "tonsillitis", "throat cancer"],
        "questions": ["Fever?", "Swollen glands?", "White patches on tonsils?",
                     "Difficulty swallowing?", "How long?", "Exposed to strep?"],
        "red_flags": ["can't swallow", "drooling", "difficulty breathing", "high fever"],
        "home_care": ["Salt water gargle", "Warm liquids", "Throat lozenges", "Rest",
                     "Honey", "Humidifier"],
        "see_doctor_if": ["Lasts more than a week", "Fever over 101°F", "Swollen glands",
                         "White patches on throat", "Recurring frequently"],
        "specialist": "ENT (Ear Nose Throat) / Primary Care"
    },
    
    # DIGESTIVE
    "stomach_pain": {
        "common_causes": ["indigestion", "gas", "constipation", "food poisoning",
                         "stomach flu", "acid reflux", "menstrual cramps"],
        "serious_causes": ["appendicitis", "gallstones", "ulcer", "pancreatitis",
                          "bowel obstruction", "ectopic pregnancy"],
        "questions": ["Where exactly is the pain?", "Sharp or dull?", "When did it start?",
                     "Nausea or vomiting?", "Fever?", "Last bowel movement?",
                     "Could you be pregnant?"],
        "red_flags": ["severe pain lower right", "blood in stool", "black stool",
                     "can't keep fluids down", "fever with severe pain", "rigid abdomen"],
        "home_care": ["BRAT diet", "Clear fluids", "Rest", "Heating pad",
                     "Avoid fatty/spicy foods"],
        "see_doctor_if": ["Severe pain", "Lasts more than 2 days", "Fever",
                         "Can't eat or drink", "Blood in stool"],
        "specialist": "Gastroenterologist / Primary Care / ER if severe"
    },
    "nausea": {
        "common_causes": ["food poisoning", "stomach flu", "motion sickness", "pregnancy",
                         "medication side effect", "anxiety", "migraine"],
        "serious_causes": ["appendicitis", "bowel obstruction", "concussion", "meningitis"],
        "questions": ["Vomiting?", "Fever?", "Diarrhea?", "Pregnant?", "Head injury?",
                     "What did you eat?", "New medications?"],
        "red_flags": ["blood in vomit", "severe headache", "stiff neck", "confusion"],
        "home_care": ["Small sips of clear fluids", "Ginger", "Crackers", "Rest",
                     "Avoid strong smells"],
        "see_doctor_if": ["Can't keep fluids down 24+ hours", "Signs of dehydration",
                         "Blood in vomit", "Severe abdominal pain"],
        "specialist": "Gastroenterologist / Primary Care"
    },
    
    # SKIN CONDITIONS
    "rash": {
        "common_causes": ["allergic reaction", "eczema", "contact dermatitis", "heat rash",
                         "hives", "dry skin", "insect bites"],
        "serious_causes": ["shingles", "cellulitis", "meningitis rash", "drug reaction"],
        "questions": ["Where is it?", "Itchy?", "New products or foods?", "Fever?",
                     "Spreading?", "Painful?", "Blistering?"],
        "red_flags": ["fever with rash", "spreading rapidly", "painful blisters",
                     "rash doesn't fade when pressed", "difficulty breathing"],
        "home_care": ["Hydrocortisone cream", "Oatmeal bath", "Cool compress",
                     "Avoid scratching", "Antihistamine"],
        "see_doctor_if": ["Spreading", "Fever", "Painful", "Blistering", "Face/genitals",
                         "Not improving in a week"],
        "specialist": "Dermatologist / Primary Care / Allergist"
    },
    "skin_lesion": {
        "common_causes": ["acne", "mole", "wart", "cyst", "skin tag"],
        "serious_causes": ["skin cancer", "melanoma", "basal cell carcinoma"],
        "questions": ["How long has it been there?", "Has it changed?", "Bleeding?",
                     "Irregular borders?", "Multiple colors?", "Larger than pencil eraser?"],
        "red_flags": ["ABCDE: Asymmetry, Border irregular, Color varied, Diameter >6mm, Evolving"],
        "home_care": ["Monitor for changes", "Sun protection", "Don't pick at it"],
        "see_doctor_if": ["Any changes in size/color/shape", "Bleeding", "New growth",
                         "Matches ABCDE criteria"],
        "specialist": "Dermatologist"
    },
    
    # EYE PROBLEMS
    "eye_pain": {
        "common_causes": ["eye strain", "dry eyes", "conjunctivitis", "foreign body",
                         "contact lens issues", "sinus pressure"],
        "serious_causes": ["glaucoma", "corneal ulcer", "uveitis", "optic neuritis"],
        "questions": ["Both eyes or one?", "Vision changes?", "Redness?", "Discharge?",
                     "Light sensitivity?", "Recent injury?", "Contact lens wearer?"],
        "red_flags": ["sudden vision loss", "severe pain", "halos around lights",
                     "eye injury", "chemical exposure"],
        "home_care": ["Rest eyes", "Artificial tears", "Warm compress", "Remove contacts"],
        "see_doctor_if": ["Vision changes", "Severe pain", "Doesn't improve in 24 hours",
                         "After injury"],
        "specialist": "Ophthalmologist (eye doctor) / Optometrist"
    },
    "vision_changes": {
        "common_causes": ["need glasses", "eye strain", "dry eyes", "migraine aura"],
        "serious_causes": ["retinal detachment", "stroke", "glaucoma", "macular degeneration",
                          "diabetic retinopathy"],
        "questions": ["Sudden or gradual?", "One eye or both?", "Floaters?", "Flashes of light?",
                     "Curtain over vision?", "Diabetic?", "High blood pressure?"],
        "red_flags": ["sudden vision loss", "curtain over vision", "many new floaters",
                     "flashes of light", "eye pain with vision loss"],
        "home_care": ["Rest eyes", "Good lighting", "Reduce screen time"],
        "see_doctor_if": ["Any sudden changes", "Floaters or flashes", "Gradual worsening"],
        "specialist": "Ophthalmologist URGENTLY for sudden changes"
    },
    "red_eye": {
        "common_causes": ["conjunctivitis (pink eye)", "allergies", "dry eyes", "irritation",
                         "broken blood vessel", "contact lens issues"],
        "serious_causes": ["glaucoma", "uveitis", "corneal ulcer", "scleritis"],
        "questions": ["Discharge?", "Itchy or painful?", "Vision affected?", "Light sensitive?",
                     "Both eyes?", "Recent cold?", "Contact lens wearer?"],
        "red_flags": ["severe pain", "vision changes", "light sensitivity", "recent eye surgery"],
        "home_care": ["Warm compress", "Artificial tears", "Don't rub", "Remove contacts"],
        "see_doctor_if": ["Pain", "Vision changes", "Doesn't improve in 2-3 days",
                         "Thick discharge"],
        "specialist": "Ophthalmologist / Optometrist"
    },
    
    # MENTAL HEALTH
    "anxiety": {
        "common_causes": ["stress", "caffeine", "lack of sleep", "life changes",
                         "generalized anxiety disorder", "panic disorder"],
        "serious_causes": ["panic disorder", "PTSD", "OCD", "thyroid issues"],
        "questions": ["How long have you felt this way?", "Panic attacks?", "Sleep issues?",
                     "Avoiding situations?", "Physical symptoms?", "Trauma history?"],
        "red_flags": ["suicidal thoughts", "can't function", "substance use to cope"],
        "home_care": ["Deep breathing", "Exercise", "Limit caffeine", "Sleep hygiene",
                     "Mindfulness", "Talk to someone"],
        "see_doctor_if": ["Interfering with daily life", "Panic attacks", "Can't sleep",
                         "Using substances to cope"],
        "specialist": "Psychiatrist / Psychologist / Therapist / Primary Care"
    },
    "depression": {
        "common_causes": ["life events", "grief", "chronic stress", "chemical imbalance",
                         "seasonal affective disorder", "hormonal changes"],
        "serious_causes": ["major depressive disorder", "bipolar disorder", "thyroid issues"],
        "questions": ["How long have you felt this way?", "Sleep changes?", "Appetite changes?",
                     "Loss of interest?", "Energy level?", "Thoughts of self-harm?"],
        "red_flags": ["suicidal thoughts", "self-harm", "can't get out of bed",
                     "not eating", "psychotic symptoms"],
        "home_care": ["Stay connected with others", "Exercise", "Routine", "Sunlight",
                     "Limit alcohol"],
        "see_doctor_if": ["Lasting more than 2 weeks", "Affecting work/relationships",
                         "Any thoughts of self-harm"],
        "specialist": "Psychiatrist / Psychologist / Therapist"
    },
    
    # MUSCULOSKELETAL
    "back_pain": {
        "common_causes": ["muscle strain", "poor posture", "lifting injury", "sitting too long",
                         "herniated disc", "arthritis"],
        "serious_causes": ["spinal stenosis", "kidney infection", "cancer", "cauda equina"],
        "questions": ["Where exactly?", "Radiating to legs?", "Numbness or weakness?",
                     "Bladder/bowel changes?", "Recent injury?", "How long?"],
        "red_flags": ["loss of bladder/bowel control", "numbness in groin", "leg weakness",
                     "fever", "unexplained weight loss"],
        "home_care": ["Ice first 48 hours, then heat", "OTC pain relievers", "Gentle stretching",
                     "Keep moving", "Good posture"],
        "see_doctor_if": ["Radiating to legs", "Numbness", "Weakness", "Lasts more than 2 weeks",
                         "After injury"],
        "specialist": "Orthopedist / Neurologist / Physical Therapist / Chiropractor"
    },
    "joint_pain": {
        "common_causes": ["overuse", "arthritis", "injury", "bursitis", "tendinitis"],
        "serious_causes": ["rheumatoid arthritis", "gout", "infection", "lupus"],
        "questions": ["Which joint?", "Swelling?", "Redness?", "Warm to touch?", "Fever?",
                     "Morning stiffness?", "Recent injury?"],
        "red_flags": ["hot red swollen joint with fever", "can't bear weight",
                     "visible deformity", "multiple joints suddenly"],
        "home_care": ["Rest", "Ice", "Compression", "Elevation", "OTC anti-inflammatory"],
        "see_doctor_if": ["Swelling", "Redness with warmth", "Can't use joint",
                         "Lasts more than a week"],
        "specialist": "Rheumatologist / Orthopedist / Primary Care"
    }
}

# ============================================================================
# SPECIALIST TYPES
# ============================================================================

MEDICAL_SPECIALISTS = {
    "primary_care": {
        "also_called": ["Family Doctor", "General Practitioner", "GP", "PCP", "Internist"],
        "treats": ["General health", "Preventive care", "Common illnesses", "Referrals"],
        "search_terms": ["family doctor", "primary care", "general practitioner", "internal medicine"]
    },
    "cardiologist": {
        "also_called": ["Heart Doctor", "Heart Specialist"],
        "treats": ["Heart disease", "High blood pressure", "Arrhythmia", "Heart failure"],
        "search_terms": ["cardiologist", "heart doctor", "cardiology"]
    },
    "dermatologist": {
        "also_called": ["Skin Doctor", "Skin Specialist"],
        "treats": ["Skin conditions", "Rashes", "Acne", "Skin cancer", "Eczema", "Psoriasis"],
        "search_terms": ["dermatologist", "skin doctor", "dermatology"]
    },
    "neurologist": {
        "also_called": ["Brain Doctor", "Nerve Specialist"],
        "treats": ["Headaches", "Seizures", "Stroke", "MS", "Parkinson's", "Neuropathy"],
        "search_terms": ["neurologist", "neurology"]
    },
    "ophthalmologist": {
        "also_called": ["Eye Doctor", "Eye Surgeon"],
        "treats": ["Eye diseases", "Vision problems", "Cataracts", "Glaucoma", "Eye surgery"],
        "search_terms": ["ophthalmologist", "eye doctor", "ophthalmology"]
    },
    "optometrist": {
        "also_called": ["Eye Doctor"],
        "treats": ["Vision exams", "Glasses", "Contacts", "Basic eye conditions"],
        "search_terms": ["optometrist", "eye exam", "vision center"]
    },
    "orthopedist": {
        "also_called": ["Bone Doctor", "Orthopedic Surgeon"],
        "treats": ["Bones", "Joints", "Muscles", "Fractures", "Sports injuries", "Arthritis"],
        "search_terms": ["orthopedic", "orthopedist", "bone doctor"]
    },
    "psychiatrist": {
        "also_called": ["Mental Health Doctor"],
        "treats": ["Mental illness", "Depression", "Anxiety", "Bipolar", "Schizophrenia", "Medication"],
        "search_terms": ["psychiatrist", "psychiatry", "mental health doctor"]
    },
    "psychologist": {
        "also_called": ["Therapist", "Counselor"],
        "treats": ["Therapy", "Counseling", "Mental health", "Behavioral issues"],
        "search_terms": ["psychologist", "therapist", "counselor", "mental health counseling"]
    },
    "gastroenterologist": {
        "also_called": ["GI Doctor", "Stomach Doctor"],
        "treats": ["Digestive issues", "IBS", "Crohn's", "Ulcers", "Liver disease", "Colonoscopy"],
        "search_terms": ["gastroenterologist", "GI doctor", "digestive health"]
    },
    "pulmonologist": {
        "also_called": ["Lung Doctor", "Respiratory Specialist"],
        "treats": ["Lung disease", "Asthma", "COPD", "Sleep apnea", "Pneumonia"],
        "search_terms": ["pulmonologist", "lung doctor", "pulmonology"]
    },
    "ent": {
        "also_called": ["Ear Nose Throat", "Otolaryngologist"],
        "treats": ["Ear problems", "Sinus issues", "Throat conditions", "Hearing loss", "Allergies"],
        "search_terms": ["ENT", "ear nose throat", "otolaryngologist"]
    },
    "allergist": {
        "also_called": ["Allergy Doctor", "Immunologist"],
        "treats": ["Allergies", "Asthma", "Immune disorders", "Food allergies"],
        "search_terms": ["allergist", "allergy doctor", "immunologist"]
    },
    "rheumatologist": {
        "also_called": ["Arthritis Doctor"],
        "treats": ["Arthritis", "Lupus", "Autoimmune diseases", "Joint inflammation"],
        "search_terms": ["rheumatologist", "arthritis doctor", "rheumatology"]
    },
    "endocrinologist": {
        "also_called": ["Hormone Doctor", "Diabetes Doctor"],
        "treats": ["Diabetes", "Thyroid", "Hormones", "Metabolism"],
        "search_terms": ["endocrinologist", "diabetes doctor", "thyroid doctor"]
    },
    "urologist": {
        "also_called": ["Bladder Doctor"],
        "treats": ["Urinary issues", "Kidney stones", "Prostate", "Bladder problems"],
        "search_terms": ["urologist", "urology"]
    },
    "gynecologist": {
        "also_called": ["OB-GYN", "Women's Health"],
        "treats": ["Women's health", "Pregnancy", "Menstrual issues", "Reproductive health"],
        "search_terms": ["gynecologist", "OB-GYN", "women's health"]
    }
}

# ============================================================================
# LOCATION SERVICES
# ============================================================================

def find_nearby_medical_facilities(facility_type: str = "hospital", 
                                   location: str = "auto") -> List[Dict]:
    """
    Find nearby medical facilities using location services.
    Uses OpenStreetMap Nominatim API (free, no API key required).
    
    Args:
        facility_type: hospital, pharmacy, clinic, emergency, etc.
        location: "auto" for IP-based location or city name
        
    Returns:
        List of nearby facilities with name, address, distance
    """
    try:
        # Get user's location from IP
        if location == "auto":
            try:
                ip_response = requests.get("https://ipapi.co/json/", timeout=5)
                if ip_response.status_code == 200:
                    ip_data = ip_response.json()
                    lat = ip_data.get("latitude")
                    lon = ip_data.get("longitude")
                    city = ip_data.get("city", "")
                else:
                    return []
            except:
                return []
        else:
            # Geocode the location
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
            geo_response = requests.get(geo_url, headers={"User-Agent": "MonicaAI/1.0"}, timeout=5)
            if geo_response.status_code == 200 and geo_response.json():
                geo_data = geo_response.json()[0]
                lat = float(geo_data["lat"])
                lon = float(geo_data["lon"])
                city = location
            else:
                return []
        
        # Map facility types to OSM amenity tags
        amenity_map = {
            "hospital": "hospital",
            "emergency": "hospital",
            "er": "hospital",
            "pharmacy": "pharmacy",
            "clinic": "clinic",
            "doctor": "doctors",
            "dentist": "dentist",
            "mental_health": "clinic",
            "behavioral_health": "clinic",
            "urgent_care": "clinic"
        }
        
        amenity = amenity_map.get(facility_type.lower(), "hospital")
        
        # Search for facilities using Overpass API
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Search within 10km radius
        query = f"""
        [out:json][timeout:10];
        (
          node["amenity"="{amenity}"](around:10000,{lat},{lon});
          way["amenity"="{amenity}"](around:10000,{lat},{lon});
        );
        out center 10;
        """
        
        response = requests.post(overpass_url, data={"data": query}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            facilities = []
            
            for element in data.get("elements", [])[:10]:  # Limit to 10 results
                tags = element.get("tags", {})
                name = tags.get("name", f"Unnamed {facility_type.title()}")
                
                # Get coordinates
                if element["type"] == "node":
                    elem_lat, elem_lon = element["lat"], element["lon"]
                else:
                    elem_lat = element.get("center", {}).get("lat", lat)
                    elem_lon = element.get("center", {}).get("lon", lon)
                
                # Build address
                address_parts = []
                if tags.get("addr:street"):
                    addr = tags.get("addr:housenumber", "") + " " + tags["addr:street"]
                    address_parts.append(addr.strip())
                if tags.get("addr:city"):
                    address_parts.append(tags["addr:city"])
                
                address = ", ".join(address_parts) if address_parts else "Address not available"
                
                facilities.append({
                    "name": name,
                    "address": address,
                    "phone": tags.get("phone", tags.get("contact:phone", "N/A")),
                    "type": facility_type,
                    "emergency": tags.get("emergency", "unknown"),
                    "lat": elem_lat,
                    "lon": elem_lon
                })
            
            return facilities
    except Exception as e:
        print(f"Error finding facilities: {e}")
    
    return []


def get_facility_search_url(facility_type: str, location: str = "") -> str:
    """Generate a Google Maps search URL for medical facilities."""
    search_terms = {
        "hospital": "hospital emergency room",
        "emergency": "emergency room ER",
        "urgent_care": "urgent care clinic",
        "pharmacy": "pharmacy",
        "mental_health": "mental health clinic behavioral health",
        "psychiatrist": "psychiatrist mental health",
        "dermatologist": "dermatologist skin doctor",
        "cardiologist": "cardiologist heart doctor",
        "neurologist": "neurologist",
        "ophthalmologist": "eye doctor ophthalmologist",
        "primary_care": "family doctor primary care physician"
    }
    
    search = search_terms.get(facility_type.lower(), facility_type)
    if location:
        search += f" near {location}"
    else:
        search += " near me"
    
    return f"https://www.google.com/maps/search/{search.replace(' ', '+')}"


# ============================================================================
# SYMPTOM CHECKER
# ============================================================================

class MedicalAssistant:
    """
    Monica's medical assistant for symptom checking and recommendations.
    Always recommends professional medical advice.
    """
    
    def __init__(self):
        self.symptoms_db = SYMPTOMS_DATABASE
        self.emergency_db = EMERGENCY_SYMPTOMS
        self.specialists = MEDICAL_SPECIALISTS
    
    def check_emergency(self, symptoms_text: str) -> Optional[Dict]:
        """Check if symptoms indicate an emergency."""
        symptoms_lower = symptoms_text.lower()
        
        for condition, data in self.emergency_db.items():
            for symptom in data["symptoms"]:
                if symptom in symptoms_lower:
                    return {
                        "is_emergency": True,
                        "condition": condition,
                        "action": data["action"],
                        "description": data["description"],
                        "specialist": data["specialist"],
                        "while_waiting": data["while_waiting"]
                    }
        
        return None
    
    def analyze_symptoms(self, symptoms_text: str) -> Dict:
        """Analyze symptoms and provide recommendations."""
        symptoms_lower = symptoms_text.lower()
        
        # First check for emergencies
        emergency = self.check_emergency(symptoms_text)
        if emergency:
            return emergency
        
        # Find matching symptoms
        matches = []
        for symptom_key, data in self.symptoms_db.items():
            # Check if symptom key or related terms are mentioned
            if symptom_key.replace("_", " ") in symptoms_lower:
                matches.append({
                    "symptom": symptom_key,
                    "data": data
                })
        
        if matches:
            primary = matches[0]
            return {
                "is_emergency": False,
                "symptom": primary["symptom"],
                "common_causes": primary["data"]["common_causes"],
                "questions": primary["data"]["questions"],
                "red_flags": primary["data"]["red_flags"],
                "home_care": primary["data"]["home_care"],
                "see_doctor_if": primary["data"]["see_doctor_if"],
                "specialist": primary["data"]["specialist"]
            }
        
        return {
            "is_emergency": False,
            "message": "I'd recommend describing your symptoms in more detail or consulting with a healthcare provider.",
            "specialist": "Primary Care Physician"
        }
    
    def get_specialist_info(self, specialist_type: str) -> Optional[Dict]:
        """Get information about a medical specialist."""
        specialist_lower = specialist_type.lower().replace(" ", "_")
        
        for key, data in self.specialists.items():
            if key == specialist_lower or specialist_type.lower() in [a.lower() for a in data["also_called"]]:
                return {
                    "type": key,
                    "also_called": data["also_called"],
                    "treats": data["treats"],
                    "search_terms": data["search_terms"]
                }
        
        return None


# Singleton instance
_medical_assistant = None

def get_medical_assistant() -> MedicalAssistant:
    """Get the medical assistant instance."""
    global _medical_assistant
    if _medical_assistant is None:
        _medical_assistant = MedicalAssistant()
    return _medical_assistant


# Export for knowledge connector
MEDICAL_KNOWLEDGE = {
    "emergency_symptoms": EMERGENCY_SYMPTOMS,
    "symptoms_database": SYMPTOMS_DATABASE,
    "specialists": MEDICAL_SPECIALISTS
}
