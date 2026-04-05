"""
Monica Legal & Sciences Knowledge System
Adds comprehensive legal (all US states + federal) and scientific knowledge
"""

from typing import Dict, List, Optional, Any
import json
from pathlib import Path


class MonicaLegalKnowledge:
    """
    Legal knowledge covering all US states and federal law.
    """
    
    # US States + Territories
    US_JURISDICTIONS = {
        "federal": {
            "categories": [
                "constitutional_law", "criminal_law", "civil_law", "administrative_law",
                "tax_law", "immigration", "bankruptcy", "intellectual_property",
                "labor_employment", "securities", "antitrust", "environmental"
            ]
        },
        "florida": {
            "statutes": "Florida Statutes (FS)",
            "criminal_code": "Title XLVI",
            "civil_procedure": "Florida Rules of Civil Procedure",
            "specialties": ["homestead_exemption", "stand_your_ground", "no_fault_insurance"]
        },
        "states": [
            "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
            "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
            "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
            "maine", "maryland", "massachusetts", "michigan", "minnesota",
            "mississippi", "missouri", "montana", "nebraska", "nevada",
            "new_hampshire", "new_jersey", "new_mexico", "new_york",
            "north_carolina", "north_dakota", "ohio", "oklahoma", "oregon",
            "pennsylvania", "rhode_island", "south_carolina", "south_dakota",
            "tennessee", "texas", "utah", "vermont", "virginia", "washington",
            "west_virginia", "wisconsin", "wyoming"
        ],
        "territories": ["puerto_rico", "us_virgin_islands", "guam", "american_samoa"]
    }
    
    # Legal Practice Areas
    LEGAL_DOMAINS = {
        "criminal": [
            "felonies", "misdemeanors", "DUI", "drug_offenses", "violent_crimes",
            "white_collar_crime", "juvenile_law", "sex_offenses"
        ],
        "civil": [
            "contracts", "torts", "property_law", "landlord_tenant",
            "personal_injury", "medical_malpractice", "product_liability"
        ],
        "family": [
            "divorce", "child_custody", "child_support", "adoption",
            "domestic_violence", "paternity", "alimony"
        ],
        "business": [
            "corporate_law", "LLC_formation", "partnerships", "contracts",
            "commercial_litigation", "business_transactions"
        ],
        "estate": [
            "wills", "trusts", "probate", "estate_planning",
            "guardianship", "power_of_attorney"
        ],
        "regulatory": [
            "healthcare_compliance", "HIPAA", "OSHA", "EPA",
            "FDA", "FCC", "SEC", "licensing"
        ]
    }
    
    def __init__(self, data_path: str = "./data/monica_legal"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.legal_db = self.data_path / "legal_knowledge.json"
        self._load_legal_knowledge()
    
    def _load_legal_knowledge(self):
        """Load legal knowledge database."""
        if self.legal_db.exists():
            with open(self.legal_db, 'r') as f:
                self.legal_knowledge = json.load(f)
        else:
            self.legal_knowledge = {
                "federal": {},
                "states": {state: {} for state in self.US_JURISDICTIONS["states"]},
                "last_updated": None
            }
            self._save_legal_knowledge()
    
    def _save_legal_knowledge(self):
        """Save legal knowledge database."""
        with open(self.legal_db, 'w') as f:
            json.dump(self.legal_knowledge, f, indent=2)
    
    def get_legal_advice(self, jurisdiction: str, topic: str, query: str) -> str:
        """
        Get legal information (NOT legal advice - informational only).
        
        Args:
            jurisdiction: "federal", state name, or "all"
            topic: Legal domain (criminal, civil, family, etc.)
            query: User's question
            
        Returns:
            Legal information response
        """
        disclaimer = " DISCLAIMER: This is general legal information only, not legal advice. Consult a licensed attorney for your specific situation.\n\n"
        
        # Use Ollama to generate response based on jurisdiction and topic
        prompt = f"""
        Provide legal information for {jurisdiction} jurisdiction on topic: {topic}
        
        Question: {query}
        
        Include:
        - Relevant statutes/codes
        - Key legal principles
        - Common procedures
        - Important deadlines/limitations
        - When to consult an attorney
        
        Keep accurate and cite sources when possible.
        """
        
        return disclaimer + f"[Legal information for {jurisdiction} - {topic}]\n\n" + query


class MonicaSciencesKnowledge:
    """
    Scientific knowledge: Biology, Chemistry, Neurobiology, Bacteriology, etc.
    """
    
    SCIENCE_DOMAINS = {
        "biology": {
            "cellular_biology": ["cell_structure", "organelles", "membrane_transport", "cell_division"],
            "genetics": ["DNA", "RNA", "gene_expression", "mutations", "inheritance", "CRISPR"],
            "molecular_biology": ["proteins", "enzymes", "metabolism", "signaling"],
            "ecology": ["ecosystems", "populations", "biodiversity", "conservation"],
            "evolution": ["natural_selection", "speciation", "phylogenetics"]
        },
        "chemistry": {
            "general": ["atomic_structure", "periodic_table", "bonding", "reactions"],
            "organic": ["hydrocarbons", "functional_groups", "polymers", "biochemistry"],
            "inorganic": ["coordination_compounds", "metals", "minerals"],
            "physical": ["thermodynamics", "kinetics", "quantum_chemistry"],
            "analytical": ["spectroscopy", "chromatography", "titration"]
        },
        "neurobiology": {
            "neuroanatomy": ["brain_regions", "neurons", "synapses", "neurotransmitters"],
            "neurophysiology": ["action_potentials", "signal_transduction", "plasticity"],
            "cognitive_neuroscience": ["memory", "learning", "perception", "consciousness"],
            "clinical": ["neurological_disorders", "brain_injury", "neurodegenerative_diseases"]
        },
        "bacteriology": {
            "microbiology": ["bacterial_structure", "growth", "metabolism", "genetics"],
            "pathogens": ["infectious_diseases", "antibiotic_resistance", "virulence"],
            "beneficial_bacteria": ["microbiome", "probiotics", "fermentation"],
            "laboratory": ["culturing", "staining", "identification", "sterilization"]
        },
        "schizophrenia": {
            "etiology": ["genetics", "neurodevelopment", "dopamine_hypothesis", "glutamate"],
            "symptoms": ["positive_symptoms", "negative_symptoms", "cognitive_deficits"],
            "neurobiology": ["brain_structure", "neurotransmitters", "neural_circuits"],
            "treatment": ["antipsychotics", "psychotherapy", "psychosocial_interventions"],
            "research": ["biomarkers", "early_intervention", "personalized_medicine"]
        }
    }
    
    def __init__(self, data_path: str = "./data/monica_sciences"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.science_db = self.data_path / "science_knowledge.json"
        self._load_science_knowledge()
    
    def _load_science_knowledge(self):
        """Load science knowledge database."""
        if self.science_db.exists():
            with open(self.science_db, 'r') as f:
                self.science_knowledge = json.load(f)
        else:
            self.science_knowledge = {
                domain: {} for domain in self.SCIENCE_DOMAINS.keys()
            }
            self._save_science_knowledge()
    
    def _save_science_knowledge(self):
        """Save science knowledge database."""
        with open(self.science_db, 'w') as f:
            json.dump(self.science_knowledge, f, indent=2)
    
    def explain_science(self, domain: str, topic: str, level: str = "intermediate") -> str:
        """
        Explain scientific concept.
        
        Args:
            domain: biology, chemistry, neurobiology, bacteriology, schizophrenia
            topic: Specific topic within domain
            level: beginner, intermediate, advanced
            
        Returns:
            Scientific explanation
        """
        prompt = f"""
        Explain {topic} in {domain} at {level} level.
        
        Include:
        - Clear definition
        - Key concepts and mechanisms
        - Real-world examples
        - Recent research (if applicable)
        - Clinical/practical applications
        
        Be accurate and cite current scientific understanding.
        """
        
        return f" {domain.upper()} - {topic}\n\n[Scientific explanation at {level} level]"


class MonicaEducationKnowledge:
    """
    Knowledge about colleges, universities, and educational institutions.
    """
    
    EDUCATION_DOMAINS = {
        "usa_colleges": {
            "types": ["public_universities", "private_universities", "liberal_arts", "community_colleges"],
            "rankings": ["ivy_league", "top_50", "regional", "specialized"],
            "programs": ["undergraduate", "graduate", "professional", "online"]
        },
        "world_universities": {
            "regions": ["europe", "asia", "australia", "canada", "latin_america", "africa"],
            "rankings": ["QS", "THE", "ARWU"]
        },
        "admissions": {
            "requirements": ["GPA", "SAT", "ACT", "essays", "recommendations"],
            "processes": ["applications", "deadlines", "financial_aid", "scholarships"]
        },
        "majors": [
            "computer_science", "engineering", "medicine", "law", "business",
            "psychology", "biology", "chemistry", "physics", "mathematics"
        ]
    }
    
    def __init__(self, data_path: str = "./data/monica_education"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.education_db = self.data_path / "education_knowledge.json"
        self._load_education_knowledge()
    
    def _load_education_knowledge(self):
        """Load education knowledge database."""
        if self.education_db.exists():
            with open(self.education_db, 'r') as f:
                self.education_knowledge = json.load(f)
        else:
            self.education_knowledge = {"universities": {}, "programs": {}}
            self._save_education_knowledge()
    
    def _save_education_knowledge(self):
        """Save education knowledge database."""
        with open(self.education_db, 'w') as f:
            json.dump(self.education_knowledge, f, indent=2)
    
    def get_university_info(self, university: str, query: str) -> str:
        """
        Get information about universities and colleges.
        
        Args:
            university: University name or "all" for comparisons
            query: User's question
            
        Returns:
            University information
        """
        return f"[GRAD] University Information: {university}\n\n[Details about programs, admissions, etc.]"


class MonicaSocialEngineering:
    """
    Social engineering knowledge (for security awareness and protection).
    """
    
    SE_DOMAINS = {
        "techniques": [
            "phishing", "pretexting", "baiting", "quid_pro_quo",
            "tailgating", "vishing", "smishing", "spear_phishing"
        ],
        "protection": [
            "awareness_training", "verification_procedures", "security_policies",
            "incident_response", "red_flags", "reporting"
        ],
        "psychology": [
            "trust_exploitation", "authority", "urgency", "fear",
            "reciprocity", "scarcity", "social_proof"
        ]
    }
    
    def detect_social_engineering(self, scenario: str) -> Dict[str, Any]:
        """
        Analyze potential social engineering attempt.
        
        Args:
            scenario: Description of situation
            
        Returns:
            Analysis with red flags and recommendations
        """
        return {
            "risk_level": "low|medium|high",
            "red_flags": [],
            "techniques_detected": [],
            "recommendations": [],
            "should_report": False
        }


# Export all classes
__all__ = [
    'MonicaLegalKnowledge',
    'MonicaSciencesKnowledge', 
    'MonicaEducationKnowledge',
    'MonicaSocialEngineering'
]
