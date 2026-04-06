"""
Monica's Comprehensive Knowledge Base System
Uses local storage for large datasets to avoid overloading local PC
Supports 50+ academic and professional domains
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Knowledge domains organized by category
KNOWLEDGE_DOMAINS = {
    # STEM Sciences
    "sciences": {
        "physics": {
            "topics": ["classical_mechanics", "quantum_physics", "thermodynamics", "electromagnetism", "optics", "nuclear_physics", "particle_physics"],
            "datasets": ["physics_formulas.json", "physics_constants.json", "physics_problems.json"]
        },
        "chemistry": {
            "topics": ["organic_chemistry", "inorganic_chemistry", "biochemistry", "analytical_chemistry", "physical_chemistry", "electrochemistry"],
            "datasets": ["periodic_table.json", "chemical_reactions.json", "molecular_structures.json"]
        },
        "biology": {
            "topics": ["cell_biology", "genetics", "evolution", "ecology", "microbiology", "botany", "zoology", "neuroscience"],
            "datasets": ["species_database.json", "genetic_codes.json", "biological_processes.json"]
        },
        "mathematics": {
            "topics": ["algebra", "calculus", "geometry", "trigonometry", "statistics", "probability", "linear_algebra", "differential_equations", "number_theory"],
            "datasets": ["math_formulas.json", "theorems.json", "problem_sets.json"]
        },
        "statistics": {
            "topics": ["descriptive_statistics", "inferential_statistics", "regression", "hypothesis_testing", "bayesian_statistics", "multivariate_analysis"],
            "datasets": ["statistical_tables.json", "distributions.json", "statistical_tests.json"]
        },
        "astrophysics": {
            "topics": ["cosmology", "stellar_evolution", "planetary_science", "black_holes", "dark_matter", "gravitational_waves", "exoplanets"],
            "datasets": ["star_catalog.json", "galaxy_data.json", "astronomical_constants.json"]
        }
    },
    
    # Engineering
    "engineering": {
        "mechanical_engineering": {
            "topics": ["statics", "dynamics", "fluid_mechanics", "heat_transfer", "machine_design", "manufacturing"],
            "datasets": ["engineering_materials.json", "mechanical_formulas.json"]
        },
        "electrical_engineering": {
            "topics": ["circuit_analysis", "electronics", "power_systems", "control_systems", "signal_processing"],
            "datasets": ["circuit_components.json", "electrical_formulas.json"]
        },
        "civil_engineering": {
            "topics": ["structural_analysis", "geotechnical", "transportation", "environmental_engineering", "construction"],
            "datasets": ["building_codes.json", "material_properties.json"]
        },
        "computer_science": {
            "topics": ["algorithms", "data_structures", "operating_systems", "databases", "networking", "ai_ml", "cybersecurity", "software_engineering"],
            "datasets": ["programming_concepts.json", "algorithm_complexity.json", "design_patterns.json"]
        }
    },
    
    # Medical & Health Sciences
    "medical_health": {
        "medical_science": {
            "topics": ["anatomy", "pathology", "pharmacology", "immunology", "cardiology", "neurology", "oncology", "pediatrics", "geriatrics"],
            "datasets": ["diseases_database.json", "medications.json", "medical_procedures.json", "icd_codes.json"]
        },
        "human_physiology": {
            "topics": ["cardiovascular_system", "respiratory_system", "nervous_system", "digestive_system", "endocrine_system", "musculoskeletal_system", "reproductive_system"],
            "datasets": ["organ_systems.json", "physiological_values.json", "homeostasis.json"]
        },
        "physical_health": {
            "topics": ["exercise_science", "nutrition", "sleep_health", "preventive_care", "chronic_disease_management", "rehabilitation"],
            "datasets": ["exercise_guidelines.json", "health_metrics.json", "fitness_programs.json"]
        },
        "mental_health": {
            "topics": ["depression", "anxiety", "ptsd", "bipolar_disorder", "schizophrenia", "personality_disorders", "addiction", "eating_disorders"],
            "datasets": ["dsm5_criteria.json", "mental_health_assessments.json", "treatment_protocols.json"]
        },
        "diet_nutrition": {
            "topics": ["macronutrients", "micronutrients", "dietary_guidelines", "meal_planning", "special_diets", "food_allergies", "sports_nutrition"],
            "datasets": ["food_database.json", "nutritional_values.json", "diet_plans.json"]
        }
    },
    
    # Therapy & Counseling
    "therapy_counseling": {
        "psychology": {
            "topics": ["cognitive_psychology", "developmental_psychology", "social_psychology", "clinical_psychology", "neuropsychology", "positive_psychology"],
            "datasets": ["psychological_theories.json", "assessment_tools.json", "research_findings.json"]
        },
        "counseling_modalities": {
            "topics": ["cbt", "dbt", "psychodynamic", "humanistic", "gestalt", "emdr", "act", "motivational_interviewing", "solution_focused", "narrative_therapy", "family_systems", "group_therapy"],
            "datasets": ["therapy_techniques.json", "intervention_protocols.json", "case_formulations.json"]
        },
        "speech_therapy": {
            "topics": ["articulation", "fluency", "voice_disorders", "language_disorders", "swallowing_disorders", "aphasia", "apraxia", "autism_communication"],
            "datasets": ["speech_assessments.json", "therapy_exercises.json", "communication_aids.json"]
        },
        "physical_therapy": {
            "topics": ["orthopedic_pt", "neurological_pt", "cardiovascular_pt", "pediatric_pt", "geriatric_pt", "sports_pt", "manual_therapy"],
            "datasets": ["exercise_protocols.json", "rehabilitation_programs.json", "assessment_tools.json"]
        },
        "human_sexuality": {
            "topics": ["sexual_health", "gender_identity", "sexual_orientation", "relationship_dynamics", "sex_education", "sexual_dysfunction", "intimacy"],
            "datasets": ["sexuality_education.json", "relationship_guidance.json", "health_resources.json"]
        }
    },
    
    # Education & Communication
    "education_communication": {
        "teaching_methods": {
            "topics": ["pedagogy", "andragogy", "differentiated_instruction", "project_based_learning", "inquiry_based_learning", "flipped_classroom", "montessori", "waldorf"],
            "datasets": ["teaching_strategies.json", "lesson_plans.json", "assessment_methods.json"]
        },
        "education": {
            "topics": ["curriculum_design", "educational_psychology", "special_education", "early_childhood", "higher_education", "online_learning", "educational_technology"],
            "datasets": ["learning_theories.json", "educational_standards.json", "instructional_design.json"]
        },
        "communication_skills": {
            "topics": ["public_speaking", "interpersonal_communication", "nonverbal_communication", "active_listening", "conflict_resolution", "negotiation", "presentation_skills"],
            "datasets": ["communication_techniques.json", "speech_templates.json", "feedback_methods.json"]
        },
        "research_methods": {
            "topics": ["quantitative_research", "qualitative_research", "mixed_methods", "experimental_design", "survey_research", "case_studies", "meta_analysis", "literature_review"],
            "datasets": ["research_designs.json", "statistical_methods.json", "ethical_guidelines.json"]
        }
    },
    
    # Business & Administration
    "business": {
        "business_administration": {
            "topics": ["management", "marketing", "finance", "accounting", "operations", "human_resources", "strategic_planning", "entrepreneurship"],
            "datasets": ["business_models.json", "financial_formulas.json", "management_frameworks.json"]
        },
        "economics": {
            "topics": ["microeconomics", "macroeconomics", "international_economics", "behavioral_economics", "development_economics"],
            "datasets": ["economic_indicators.json", "economic_theories.json", "market_data.json"]
        }
    },
    
    # Humanities & Social Sciences
    "humanities": {
        "history": {
            "topics": ["ancient_history", "medieval_history", "modern_history", "world_wars", "american_history", "european_history", "asian_history", "african_history"],
            "datasets": ["historical_events.json", "historical_figures.json", "timelines.json"]
        },
        "african_studies": {
            "topics": ["african_history", "african_cultures", "african_languages", "african_politics", "african_economics", "african_art", "diaspora_studies"],
            "datasets": ["african_nations.json", "cultural_practices.json", "historical_movements.json"]
        },
        "cultural_religions": {
            "topics": ["christianity", "islam", "judaism", "hinduism", "buddhism", "sikhism", "indigenous_religions", "comparative_religion", "philosophy_of_religion"],
            "datasets": ["world_religions.json", "religious_texts.json", "cultural_practices.json"]
        }
    },
    
    # Languages
    "languages": {
        "world_languages": {
            "topics": [
                # Major world languages
                "english", "spanish", "mandarin", "hindi", "arabic", "portuguese", "bengali", "russian", "japanese", "german",
                "french", "italian", "korean", "turkish", "vietnamese", "polish", "ukrainian", "dutch", "thai", "greek",
                # African languages
                "swahili", "hausa", "yoruba", "igbo", "amharic", "zulu", "xhosa", "afrikaans", "somali", "oromo",
                # Asian languages
                "indonesian", "malay", "tagalog", "tamil", "telugu", "marathi", "gujarati", "kannada", "punjabi", "urdu",
                # European languages
                "swedish", "norwegian", "danish", "finnish", "czech", "hungarian", "romanian", "bulgarian", "serbian", "croatian",
                # Middle Eastern languages
                "persian", "hebrew", "kurdish", "pashto", "dari",
                # Indigenous languages
                "navajo", "cherokee", "quechua", "guarani", "maori", "hawaiian"
            ],
            "datasets": ["vocabulary.json", "grammar_rules.json", "phrases.json", "pronunciation.json"]
        }
    }
}


class MonicaKnowledgeBase:
    """
    Comprehensive knowledge base system with local storage support.
    Manages 50+ academic and professional domains.
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        self.onedrive_path = None  # Legacy: no longer using OneDrive
        if knowledge_path is None:
            knowledge_path = r"C:\Monica\knowledge_base"
        self.local_cache_path = os.path.join(os.path.dirname(__file__), 'knowledge_cache')
        self.knowledge_path = None
        
        # Set up storage paths
        if os.path.exists(knowledge_path):
            self.knowledge_path = knowledge_path
            self.storage_type = "local"
            print(f"✅ Knowledge base found: {knowledge_path}")
        else:
            self.knowledge_path = self.local_cache_path
            self.storage_type = "local"
            print(f"⚠️ Knowledge base path not found, using local storage: {self.local_cache_path}")
        
        # Create directory structure
        self._initialize_storage()
        
        # Load domain index
        self.domain_index = self._load_domain_index()
        
        # Statistics
        self.stats = {
            "total_domains": 0,
            "total_topics": 0,
            "total_datasets": 0,
            "storage_used_mb": 0
        }
        self._calculate_stats()
        
        print(f"📚 Monica Knowledge Base initialized")
        print(f"   Storage: {self.storage_type.upper()}")
        print(f"   Domains: {self.stats['total_domains']}")
        print(f"   Topics: {self.stats['total_topics']}")
    
    def _find_onedrive_path(self) -> Optional[str]:
        """Legacy method — OneDrive no longer used. Returns None."""
        return None
        
        return None
    
    def _initialize_storage(self):
        """Create directory structure for knowledge base"""
        os.makedirs(self.knowledge_path, exist_ok=True)
        os.makedirs(self.local_cache_path, exist_ok=True)
        
        # Create category directories
        for category, domains in KNOWLEDGE_DOMAINS.items():
            category_path = os.path.join(self.knowledge_path, category)
            os.makedirs(category_path, exist_ok=True)
            
            for domain_name, domain_info in domains.items():
                domain_path = os.path.join(category_path, domain_name)
                os.makedirs(domain_path, exist_ok=True)
                
                # Create topics subdirectory
                topics_path = os.path.join(domain_path, "topics")
                os.makedirs(topics_path, exist_ok=True)
                
                # Create datasets subdirectory
                datasets_path = os.path.join(domain_path, "datasets")
                os.makedirs(datasets_path, exist_ok=True)
    
    def _load_domain_index(self) -> Dict:
        """Load or create domain index"""
        index_path = os.path.join(self.knowledge_path, "domain_index.json")
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create initial index from KNOWLEDGE_DOMAINS
            index = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "domains": KNOWLEDGE_DOMAINS
            }
            self._save_domain_index(index)
            return index
    
    def _save_domain_index(self, index: Dict):
        """Save domain index"""
        index_path = os.path.join(self.knowledge_path, "domain_index.json")
        index["updated"] = datetime.now().isoformat()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    
    def _calculate_stats(self):
        """Calculate knowledge base statistics"""
        total_domains = 0
        total_topics = 0
        total_datasets = 0
        
        for category, domains in KNOWLEDGE_DOMAINS.items():
            for domain_name, domain_info in domains.items():
                total_domains += 1
                total_topics += len(domain_info.get("topics", []))
                total_datasets += len(domain_info.get("datasets", []))
        
        self.stats["total_domains"] = total_domains
        self.stats["total_topics"] = total_topics
        self.stats["total_datasets"] = total_datasets
        
        # Calculate storage used
        total_size = 0
        for root, dirs, files in os.walk(self.knowledge_path):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
        self.stats["storage_used_mb"] = total_size / (1024 * 1024)
    
    def get_domain_info(self, category: str, domain: str) -> Optional[Dict]:
        """Get information about a specific domain"""
        if category in KNOWLEDGE_DOMAINS:
            if domain in KNOWLEDGE_DOMAINS[category]:
                return KNOWLEDGE_DOMAINS[category][domain]
        return None
    
    def search_topics(self, query: str) -> List[Dict]:
        """Search for topics across all domains"""
        results = []
        query_lower = query.lower()
        
        for category, domains in KNOWLEDGE_DOMAINS.items():
            for domain_name, domain_info in domains.items():
                for topic in domain_info.get("topics", []):
                    if query_lower in topic.lower():
                        results.append({
                            "category": category,
                            "domain": domain_name,
                            "topic": topic,
                            "relevance": 1.0 if query_lower == topic.lower() else 0.5
                        })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
    
    def get_knowledge(self, category: str, domain: str, topic: str) -> Optional[Dict]:
        """Retrieve knowledge for a specific topic"""
        topic_path = os.path.join(self.knowledge_path, category, domain, "topics", f"{topic}.json")
        
        if os.path.exists(topic_path):
            with open(topic_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Return template if no data exists yet
        return {
            "topic": topic,
            "category": category,
            "domain": domain,
            "content": f"Knowledge about {topic.replace('_', ' ')} in {domain.replace('_', ' ')}",
            "status": "template",
            "last_updated": None
        }
    
    def add_knowledge(self, category: str, domain: str, topic: str, content: Dict) -> bool:
        """Add or update knowledge for a topic"""
        try:
            topic_path = os.path.join(self.knowledge_path, category, domain, "topics", f"{topic}.json")
            
            content["topic"] = topic
            content["category"] = category
            content["domain"] = domain
            content["last_updated"] = datetime.now().isoformat()
            
            with open(topic_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            return False
    
    def list_all_domains(self) -> Dict[str, List[str]]:
        """List all available domains by category"""
        result = {}
        for category, domains in KNOWLEDGE_DOMAINS.items():
            result[category] = list(domains.keys())
        return result
    
    def list_topics(self, category: str, domain: str) -> List[str]:
        """List all topics in a domain"""
        if category in KNOWLEDGE_DOMAINS:
            if domain in KNOWLEDGE_DOMAINS[category]:
                return KNOWLEDGE_DOMAINS[category][domain].get("topics", [])
        return []
    
    def get_languages(self) -> List[str]:
        """Get list of all supported languages"""
        return KNOWLEDGE_DOMAINS["languages"]["world_languages"]["topics"]
    
    def get_counseling_modalities(self) -> List[str]:
        """Get list of all counseling modalities"""
        return KNOWLEDGE_DOMAINS["therapy_counseling"]["counseling_modalities"]["topics"]
    
    def generate_knowledge_report(self) -> str:
        """Generate a report of the knowledge base"""
        report = []
        report.append("=" * 60)
        report.append("MONICA KNOWLEDGE BASE REPORT")
        report.append("=" * 60)
        report.append(f"Storage Type: {self.storage_type.upper()}")
        report.append(f"Storage Path: {self.knowledge_path}")
        report.append(f"Total Domains: {self.stats['total_domains']}")
        report.append(f"Total Topics: {self.stats['total_topics']}")
        report.append(f"Storage Used: {self.stats['storage_used_mb']:.2f} MB")
        report.append("")
        report.append("DOMAINS BY CATEGORY:")
        report.append("-" * 40)
        
        for category, domains in KNOWLEDGE_DOMAINS.items():
            report.append(f"\n📁 {category.upper().replace('_', ' ')}")
            for domain_name, domain_info in domains.items():
                topic_count = len(domain_info.get("topics", []))
                report.append(f"   • {domain_name.replace('_', ' ')}: {topic_count} topics")
        
        report.append("")
        report.append("=" * 60)
        return "\n".join(report)


# Singleton instance
_knowledge_base = None

def get_knowledge_base() -> MonicaKnowledgeBase:
    """Get or create the knowledge base singleton"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = MonicaKnowledgeBase()
    return _knowledge_base


if __name__ == "__main__":
    # Test the knowledge base
    kb = get_knowledge_base()
    print(kb.generate_knowledge_report())
    
    print("\n\nSUPPORTED LANGUAGES:")
    languages = kb.get_languages()
    for i, lang in enumerate(languages, 1):
        print(f"  {i}. {lang}")
    
    print(f"\nTotal languages: {len(languages)}")
    
    print("\n\nCOUNSELING MODALITIES:")
    modalities = kb.get_counseling_modalities()
    for mod in modalities:
        print(f"  • {mod.upper()}")
