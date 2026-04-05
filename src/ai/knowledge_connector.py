"""
Knowledge Connector for Monica AI.
Integrates all of Monica's knowledge bases to provide comprehensive, intelligent responses.
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re

# Add parent project to path for knowledge base imports
MONICA_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MONICA_PROJECT_ROOT))


class KnowledgeConnector:
    """
    Connects Monica to all her knowledge bases for comprehensive responses.
    
    Knowledge Domains:
    - Education (K-12 curriculum)
    - Mathematics (arithmetic to calculus)
    - Software Skills (Adobe, programming, 3D)
    - Counseling & Therapy (19 modalities)
    - Emotion Intelligence
    - Language Teaching (61+ languages)
    - Legal & Sciences
    - General Knowledge
    """
    
    def __init__(self, lazy_load: bool = True):
        """
        Initialize the knowledge connector.
        
        Args:
            lazy_load: If True, knowledge bases are loaded on first use (faster startup)
        """
        self.knowledge_bases = {}
        self.is_loaded = False
        self._lazy_load = lazy_load
        
        if not lazy_load:
            self._load_knowledge_bases()
    
    def _ensure_loaded(self):
        """Ensure knowledge bases are loaded (for lazy loading)."""
        if not self.is_loaded and self._lazy_load:
            self._load_knowledge_bases()
    
    def _load_knowledge_bases(self):
        """Load all available knowledge bases."""
        if self.is_loaded:
            return  # Already loaded
        
        self.is_loaded = True  # Set early to prevent re-entry
        print("Loading Monica's knowledge bases...")
        
        # Education K-12
        try:
            from ai.monica_education_k12 import K12_CURRICULUM
            self.knowledge_bases['education'] = {
                'name': 'K-12 Education',
                'data': K12_CURRICULUM,
                'search_func': self._search_education
            }
            print("  [*] K-12 Education loaded")
        except ImportError as e:
            print(f"  [*] K-12 Education not available: {e}")
        
        # Mathematics
        try:
            from ai.monica_math_complete import MATHEMATICS_KNOWLEDGE
            self.knowledge_bases['math'] = {
                'name': 'Complete Mathematics',
                'data': MATHEMATICS_KNOWLEDGE,
                'search_func': self._search_math
            }
            print("  [*] Mathematics loaded")
        except ImportError as e:
            print(f"  [*] Mathematics not available: {e}")
        
        # Software Skills
        try:
            from ai.monica_software_skills import ADOBE_KNOWLEDGE, PROGRAMMING_LANGUAGES
            self.knowledge_bases['software'] = {
                'name': 'Software & Programming',
                'data': {'adobe': ADOBE_KNOWLEDGE, 'programming': PROGRAMMING_LANGUAGES},
                'search_func': self._search_software
            }
            print("  [*] Software Skills loaded")
        except ImportError as e:
            print(f"  [*] Software Skills not available: {e}")
        
        # Counseling & Therapy
        try:
            from ai.monica_counseling_comprehensive import COUNSELING_MODALITIES, ACADEMIC_SOURCES, MENTAL_HEALTH_CONDITIONS
            self.knowledge_bases['counseling'] = {
                'name': 'Counseling & Therapy',
                'data': {'modalities': COUNSELING_MODALITIES, 'sources': ACADEMIC_SOURCES, 'conditions': MENTAL_HEALTH_CONDITIONS},
                'search_func': self._search_counseling
            }
            print("  [*] Counseling & Therapy loaded")
        except ImportError as e:
            print(f"  [*] Counseling not available: {e}")
        
        # Emotion Intelligence
        try:
            from ai.monica_emotion_intelligence import EMOTION_TAXONOMY
            self.knowledge_bases['emotions'] = {
                'name': 'Emotion Intelligence',
                'data': EMOTION_TAXONOMY,
                'search_func': self._search_emotions
            }
            print("  [*] Emotion Intelligence loaded")
        except ImportError as e:
            print(f"  [*] Emotion Intelligence not available: {e}")
        
        # Language Teaching
        try:
            from ai.monica_language_teacher import WORLD_LANGUAGES
            self.knowledge_bases['languages'] = {
                'name': 'Language Teaching',
                'data': WORLD_LANGUAGES,
                'search_func': self._search_languages
            }
            print("  [*] Language Teaching loaded")
        except ImportError as e:
            print(f"  [*] Language Teaching not available: {e}")
        
        # General Knowledge Base
        try:
            from ai.monica_knowledge_2025 import KNOWLEDGE_2025 as KNOWLEDGE_DOMAINS
            self.knowledge_bases['general'] = {
                'name': 'General Knowledge',
                'data': KNOWLEDGE_DOMAINS,
                'search_func': self._search_general
            }
            print("  [*] General Knowledge loaded")
        except ImportError as e:
            print(f"  [*] General Knowledge not available: {e}")
        
        # Legal & Sciences
        try:
            from ai.monica_legal_sciences import MonicaLegalKnowledge, MonicaSciencesKnowledge
            self.legal_knowledge = MonicaLegalKnowledge()
            self.sciences_knowledge = MonicaSciencesKnowledge()
            self.knowledge_bases['legal'] = {
                'name': 'Legal & Sciences',
                'data': {'legal': self.legal_knowledge, 'sciences': self.sciences_knowledge},
                'search_func': self._search_legal
            }
            print("  [*] Legal & Sciences loaded")
        except ImportError as e:
            print(f"  [*] Legal Sciences not available: {e}")
        
        # 2025 Current Knowledge
        try:
            from ai.monica_knowledge_2025 import KNOWLEDGE_2025, CURRENT_CONTEXT, MONICA_QUICK_FACTS_2025
            self.knowledge_bases['current_2025'] = {
                'name': '2025 Current Knowledge',
                'data': {'knowledge': KNOWLEDGE_2025, 'context': CURRENT_CONTEXT, 'quick_facts': MONICA_QUICK_FACTS_2025},
                'search_func': self._search_2025
            }
            print("  [*] 2025 Current Knowledge loaded")
        except ImportError as e:
            print(f"  [*] 2025 Knowledge not available: {e}")
        
        # Global Webcams
        try:
            from ui.monica_global_webcams import GLOBAL_WEBCAMS
            self.knowledge_bases['webcams'] = {
                'name': 'Global Webcams',
                'data': GLOBAL_WEBCAMS,
                'search_func': self._search_webcams
            }
            print("  [*] Global Webcams loaded")
        except ImportError as e:
            print(f"  [*] Global Webcams not available: {e}")
        
        # Medical Knowledge
        try:
            from ai.monica_medical_knowledge import MEDICAL_KNOWLEDGE, get_medical_assistant
            self.knowledge_bases['medical'] = {
                'name': 'Medical Knowledge',
                'data': MEDICAL_KNOWLEDGE,
                'search_func': self._search_medical,
                'assistant': get_medical_assistant()
            }
            print("  [*] Medical Knowledge loaded")
        except ImportError as e:
            print(f"  [*] Medical Knowledge not available: {e}")
        
        # Intelligence/Brain
        try:
            from ai.monica_intelligence import INTELLIGENCE_KNOWLEDGE
            self.knowledge_bases['intelligence'] = {
                'name': 'Intelligence & Brain',
                'data': INTELLIGENCE_KNOWLEDGE,
                'search_func': self._search_generic
            }
            print("  [*] Intelligence loaded")
        except ImportError as e:
            pass  # Optional
        
        # Authentic Personality
        try:
            from ai.monica_authentic_personality import MonicaAuthenticPersonality
            self.personality = MonicaAuthenticPersonality()
            self.knowledge_bases['personality'] = {
                'name': 'Personality',
                'data': getattr(self.personality, '__dict__', {}),
                'search_func': self._search_generic
            }
            print("  [OK] Personality loaded")
        except ImportError as e:
            pass  # Optional
        
        # Location Services
        try:
            from utils.location_services import get_location_services
            self.location_services = get_location_services()
            self.knowledge_bases['location'] = {
                'name': 'Location Services',
                'data': None,
                'search_func': self._search_location
            }
            print("  [OK] Location Services loaded")
        except ImportError as e:
            self.location_services = None
            print(f"  [X] Location Services not available: {e}")
        
        # Satellite Services
        try:
            from utils.satellite_services import get_satellite_services
            self.satellite_services = get_satellite_services()
            self.knowledge_bases['satellite'] = {
                'name': 'Satellite Services',
                'data': None,
                'search_func': self._search_satellite
            }
            print("  [OK] Satellite Services loaded")
        except ImportError as e:
            self.satellite_services = None
            print(f"  [X] Satellite Services not available: {e}")
        
        # Free APIs (Weather, Dictionary, Wikipedia, NASA, etc.)
        try:
            from utils.free_apis import get_free_apis
            self.free_apis = get_free_apis()
            self.knowledge_bases['free_apis'] = {
                'name': 'Free APIs (Weather, Dictionary, NASA, etc.)',
                'data': None,
                'search_func': self._search_free_apis
            }
            print("  [*] Free APIs loaded (Weather, Dictionary, Wikipedia, NASA, Jokes, etc.)")
        except ImportError as e:
            self.free_apis = None
            print(f"  [X] Free APIs not available: {e}")
        
        # University Teaching System (23+ academic subjects)
        try:
            from ai.monica_university import get_university, SUBJECTS
            self.university = get_university()
            self.knowledge_bases['university'] = {
                'name': 'University Teaching (23 subjects)',
                'data': SUBJECTS,
                'search_func': self._search_university
            }
            print(f"  [*] University Teaching loaded ({len(SUBJECTS)} subjects)")
        except ImportError as e:
            print(f"  [*] University Teaching not available: {e}")
        
        # Knowledge Learner (URLs read, spoken facts)
        try:
            from ai.monica_knowledge_learner import get_knowledge_learner
            self.knowledge_learner = get_knowledge_learner()
            self.knowledge_bases['learned'] = {
                'name': 'Learned Knowledge',
                'data': None,
                'search_func': self._search_learned
            }
            stats = self.knowledge_learner.get_stats()
            print(f"  [*] Learned Knowledge loaded ({stats['total_entries']} entries)")
        except ImportError as e:
            self.knowledge_learner = None
            print(f"  [*] Learned Knowledge not available: {e}")
        
        # Weather System (global weather data)
        self.weather_system = None
        try:
            from services.monica_weather_system import get_weather_system
            self.weather_system = get_weather_system()
            self.knowledge_bases['weather'] = {
                'name': 'Global Weather System',
                'data': None,
                'search_func': self._search_weather
            }
            print("  [OK] Weather System loaded (global weather data)")
        except ImportError as e:
            print(f"  [X] Weather System not available: {e}")
        
        # World Camera Network
        self.world_cameras = None
        try:
            from services.monica_world_cameras import get_world_cameras
            self.world_cameras = get_world_cameras()
            stats = self.world_cameras.get_stats()
            self.knowledge_bases['cameras'] = {
                'name': f'World Camera Network ({stats["total_cameras"]} cameras)',
                'data': None,
                'search_func': self._search_cameras
            }
            print(f"  [OK] World Camera Network loaded ({stats['total_cameras']} cameras, {stats['regions']} regions)")
        except ImportError as e:
            print(f"  [X] World Camera Network not available: {e}")
        
        self.is_loaded = len(self.knowledge_bases) > 0
        print(f"Knowledge bases loaded: {len(self.knowledge_bases)}")
    
    def search_all(self, query: str) -> Dict[str, Any]:
        """
        Search all knowledge bases for relevant information.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with results from all relevant knowledge bases
        """
        # Lazy load knowledge bases on first search
        self._ensure_loaded()
        
        results = {
            'query': query,
            'found': False,
            'sources': [],
            'context': ""
        }
        
        query_lower = query.lower()
        context_parts = []
        
        # Determine which knowledge bases to search based on query
        for kb_name, kb_info in self.knowledge_bases.items():
            try:
                search_func = kb_info.get('search_func')
                if search_func:
                    kb_results = search_func(query_lower, kb_info['data'])
                    if kb_results:
                        results['found'] = True
                        results['sources'].append(kb_info['name'])
                        context_parts.append(f"[{kb_info['name']}]\n{kb_results}")
            except Exception as e:
                print(f"Error searching {kb_name}: {e}")
        
        if context_parts:
            results['context'] = "\n\n".join(context_parts)
        
        return results
    
    def get_context_for_query(self, query: str) -> str:
        """
        Get relevant context from knowledge bases for a query.
        This context can be added to the AI prompt for better responses.
        
        Args:
            query: User's question or message
            
        Returns:
            Relevant context string to add to prompt
        """
        results = self.search_all(query)
        
        if results['found']:
            return f"""
I have access to the following relevant knowledge:

{results['context']}

Use this information to provide an accurate, helpful response.
"""
        return ""
    
    def _search_education(self, query: str, data: Dict) -> Optional[str]:
        """Search K-12 education knowledge."""
        results = []
        
        # Keywords for education
        edu_keywords = ['grade', 'school', 'learn', 'teach', 'student', 'homework', 
                       'math', 'reading', 'writing', 'science', 'history', 'kindergarten',
                       'elementary', 'middle school', 'high school']
        
        if not any(kw in query for kw in edu_keywords):
            return None
        
        # Search through grades
        for grade_key, grade_data in data.items():
            grade_name = grade_data.get('grade', grade_key)
            subjects = grade_data.get('subjects', {})
            
            for subject, content in subjects.items():
                if subject.lower() in query or grade_key in query:
                    if isinstance(content, dict):
                        skills = content.get('skills', content.get('topics', []))
                        if skills:
                            results.append(f"{grade_name} - {subject.replace('_', ' ').title()}:")
                            for skill in skills[:5]:  # Limit to 5 items
                                results.append(f"  - {skill}")
        
        return "\n".join(results) if results else None
    
    def _search_math(self, query: str, data: Dict) -> Optional[str]:
        """Search mathematics knowledge."""
        results = []
        
        math_keywords = ['math', 'algebra', 'calculus', 'geometry', 'equation', 'formula',
                        'number', 'calculate', 'solve', 'trigonometry', 'statistics',
                        'probability', 'fraction', 'decimal', 'percent', 'derivative',
                        'integral', 'function', 'graph', 'theorem']
        
        if not any(kw in query for kw in math_keywords):
            return None
        
        for topic_key, topic_data in data.items():
            title = topic_data.get('title', topic_key)
            description = topic_data.get('description', '')
            
            if topic_key in query or title.lower() in query:
                results.append(f"**{title}**: {description}")
                
                topics = topic_data.get('topics', {})
                for subtopic, content in list(topics.items())[:3]:
                    if isinstance(content, dict):
                        results.append(f"  {subtopic.replace('_', ' ').title()}:")
                        for k, v in list(content.items())[:3]:
                            results.append(f"    - {k}: {v}")
                    else:
                        results.append(f"  - {subtopic}: {content}")
        
        return "\n".join(results) if results else None
    
    def _search_software(self, query: str, data: Dict) -> Optional[str]:
        """Search software and programming knowledge."""
        results = []
        
        software_keywords = ['photoshop', 'illustrator', 'premiere', 'after effects',
                           'python', 'javascript', 'java', 'code', 'programming',
                           'blender', 'unity', 'unreal', 'adobe', 'software', 'app',
                           'shortcut', 'tool', 'feature']
        
        if not any(kw in query for kw in software_keywords):
            return None
        
        # Search Adobe
        adobe = data.get('adobe', {})
        for app_key, app_data in adobe.items():
            if app_key in query or app_data.get('name', '').lower() in query:
                results.append(f"**{app_data.get('name', app_key)}**")
                results.append(f"Purpose: {app_data.get('purpose', '')}")
                
                features = app_data.get('key_features', [])[:5]
                if features:
                    results.append("Key Features:")
                    for f in features:
                        results.append(f"  - {f}")
                
                shortcuts = app_data.get('shortcuts', {})
                if shortcuts and 'shortcut' in query:
                    results.append("Shortcuts:")
                    for key, action in list(shortcuts.items())[:5]:
                        results.append(f"  - {key}: {action}")
        
        # Search Programming Languages
        programming = data.get('programming', {})
        for lang_key, lang_data in programming.items():
            if lang_key in query or lang_data.get('name', '').lower() in query:
                results.append(f"**{lang_data.get('name', lang_key)}**")
                results.append(f"Type: {lang_data.get('type', '')}")
                results.append(f"Use cases: {', '.join(lang_data.get('use_cases', [])[:3])}")
        
        return "\n".join(results) if results else None
    
    def _search_counseling(self, query: str, data: Dict) -> Optional[str]:
        """Search counseling and therapy knowledge."""
        results = []
        
        therapy_keywords = ['therapy', 'counseling', 'mental health', 'anxiety', 'depression',
                          'cbt', 'dbt', 'trauma', 'stress', 'emotion', 'feeling', 'cope',
                          'mindfulness', 'meditation', 'psychology', 'therapist']
        
        if not any(kw in query for kw in therapy_keywords):
            return None
        
        modalities = data.get('modalities', {})
        for mod_key, mod_data in modalities.items():
            if mod_key in query or mod_data.get('name', '').lower() in query:
                results.append(f"**{mod_data.get('name', mod_key)}**")
                results.append(f"Description: {mod_data.get('description', '')}")
                
                techniques = mod_data.get('techniques', [])[:3]
                if techniques:
                    results.append("Techniques:")
                    for t in techniques:
                        results.append(f"  - {t}")
        
        return "\n".join(results) if results else None
    
    def _search_emotions(self, query: str, data: Dict) -> Optional[str]:
        """Search emotion intelligence knowledge."""
        results = []
        
        emotion_keywords = ['emotion', 'feeling', 'happy', 'sad', 'angry', 'fear',
                          'surprise', 'disgust', 'expression', 'mood', 'sentiment']
        
        if not any(kw in query for kw in emotion_keywords):
            return None
        
        primary = data.get('primary', {})
        for emotion, info in primary.items():
            if emotion in query:
                results.append(f"**{emotion.title()}**")
                results.append(f"Description: {info.get('description', '')}")
                
                facial = info.get('facial_cues', [])
                if facial:
                    results.append(f"Facial cues: {', '.join(facial)}")
                
                body = info.get('body_language', [])
                if body:
                    results.append(f"Body language: {', '.join(body)}")
        
        return "\n".join(results) if results else None
    
    def _search_languages(self, query: str, data: Dict) -> Optional[str]:
        """Search language teaching knowledge."""
        results = []
        
        lang_keywords = ['language', 'speak', 'translate', 'learn', 'spanish', 'french',
                        'german', 'chinese', 'japanese', 'korean', 'italian', 'portuguese',
                        'arabic', 'russian', 'hindi', 'word', 'phrase', 'grammar']
        
        if not any(kw in query for kw in lang_keywords):
            return None
        
        for lang_key, lang_data in data.items():
            if lang_key in query or lang_data.get('name', '').lower() in query:
                results.append(f"**{lang_data.get('name', lang_key)}**")
                results.append(f"Native name: {lang_data.get('native_name', '')}")
                results.append(f"Family: {lang_data.get('family', '')}")
                results.append(f"Speakers: {lang_data.get('speakers', '')}")
                results.append(f"Writing system: {lang_data.get('writing_system', '')}")
        
        return "\n".join(results) if results else None
    
    def _search_general(self, query: str, data: Dict) -> Optional[str]:
        """Search general knowledge base."""
        results = []
        
        # Search through all domains
        for category, domains in data.items():
            for domain_key, domain_data in domains.items():
                if domain_key.replace('_', ' ') in query:
                    topics = domain_data.get('topics', [])
                    if topics:
                        results.append(f"**{domain_key.replace('_', ' ').title()}**")
                        results.append(f"Topics: {', '.join(topics[:5])}")
        
        return "\n".join(results) if results else None
    
    def _search_legal(self, query: str, data: Dict) -> Optional[str]:
        """Search legal knowledge."""
        results = []
        
        legal_keywords = ['law', 'legal', 'court', 'rights', 'contract', 'criminal',
                         'civil', 'attorney', 'lawyer', 'judge', 'constitution']
        
        if not any(kw in query for kw in legal_keywords):
            return None
        
        for topic_key, topic_data in data.items():
            if topic_key.replace('_', ' ') in query:
                results.append(f"**{topic_key.replace('_', ' ').title()}**")
                if isinstance(topic_data, dict):
                    for k, v in list(topic_data.items())[:3]:
                        results.append(f"  - {k}: {v}")
        
        return "\n".join(results) if results else None
    
    def _search_2025(self, query: str, data: Dict) -> Optional[str]:
        """Search 2025 current knowledge."""
        results = []
        
        # Keywords that trigger 2025 knowledge search
        current_keywords = ['2024', '2025', 'current', 'latest', 'new', 'recent', 'today',
                          'now', 'modern', 'ai', 'chatgpt', 'claude', 'gpt', 'llama',
                          'iphone', 'apple', 'google', 'microsoft', 'nvidia', 'tesla',
                          'movie', 'film', 'show', 'series', 'music', 'artist', 'singer',
                          'game', 'gaming', 'olympics', 'election', 'president',
                          'tiktok', 'instagram', 'twitter', 'x', 'social media',
                          'ozempic', 'weight loss', 'taylor swift', 'beyonce']
        
        if not any(kw in query for kw in current_keywords):
            return None
        
        knowledge = data.get('knowledge', {})
        quick_facts = data.get('quick_facts', '')
        
        # Search through knowledge structure
        def search_nested(d, prefix=""):
            for key, value in d.items():
                if isinstance(value, dict):
                    search_nested(value, f"{prefix}{key}/")
                elif isinstance(value, list):
                    for item in value:
                        if query.lower() in str(item).lower() or any(kw in str(item).lower() for kw in query.lower().split()):
                            results.append(f"- {item}")
                elif isinstance(value, str):
                    if query.lower() in value.lower() or query.lower() in key.lower():
                        results.append(f"**{key.replace('_', ' ').title()}**: {value}")
        
        search_nested(knowledge)
        
        # If asking about current/2025, include quick facts
        if any(kw in query for kw in ['current', '2025', 'today', 'now', 'latest']):
            if quick_facts:
                results.append(quick_facts)
        
        return "\n".join(results[:15]) if results else None
    
    def _search_webcams(self, query: str, data: Dict) -> Optional[str]:
        """Search global webcams knowledge."""
        results = []
        
        webcam_keywords = ['webcam', 'camera', 'live', 'stream', 'city', 'country', 
                          'world', 'view', 'watch', 'see', 'location']
        
        if not any(kw in query for kw in webcam_keywords):
            return None
        
        for location, info in data.items():
            if location.lower() in query or query.lower() in str(info).lower():
                results.append(f"**{location}**: {info.get('description', info)}")
        
        return "\n".join(results[:10]) if results else None
    
    def _search_generic(self, query: str, data: Dict) -> Optional[str]:
        """Generic search for any dictionary-based knowledge."""
        results = []
        
        def search_dict(d, prefix=""):
            for key, value in d.items():
                key_str = str(key)
                if isinstance(value, dict):
                    search_dict(value, f"{prefix}{key_str}/")
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if query.lower() in str(item).lower():
                            results.append(f"- {item}")
                elif isinstance(value, str):
                    if query.lower() in value.lower() or query.lower() in key_str.lower():
                        results.append(f"{key_str}: {value}")
        
        search_dict(data)
        return "\n".join(results[:10]) if results else None
    
    def _search_medical(self, query: str, data: Dict) -> Optional[str]:
        """Search medical knowledge base for symptoms and conditions."""
        results = []
        query_lower = query.lower()
        
        # Medical keywords that trigger this search
        medical_keywords = ['pain', 'ache', 'hurt', 'sick', 'symptom', 'doctor', 'hospital',
                          'headache', 'stomach', 'fever', 'cough', 'rash', 'dizzy', 'nausea',
                          'breathing', 'chest', 'heart', 'eye', 'skin', 'throat', 'ear',
                          'anxiety', 'depression', 'tired', 'fatigue', 'swollen', 'bleeding',
                          'emergency', 'urgent', 'medical', 'health', 'diagnosis', 'treatment']
        
        if not any(kw in query_lower for kw in medical_keywords):
            return None
        
        # Check for emergencies first
        emergency_symptoms = data.get('emergency_symptoms', {})
        for condition, info in emergency_symptoms.items():
            for symptom in info.get('symptoms', []):
                if symptom in query_lower:
                    results.append(f"[WARNING] EMERGENCY: {info['action']}")
                    results.append(f"Condition: {info['description']}")
                    results.append(f"Specialist: {info['specialist']}")
                    if info.get('while_waiting'):
                        results.append(f"While waiting: {', '.join(info['while_waiting'][:3])}")
                    return "\n".join(results)
        
        # Search symptoms database
        symptoms_db = data.get('symptoms_database', {})
        for symptom_key, info in symptoms_db.items():
            if symptom_key.replace('_', ' ') in query_lower:
                results.append(f"**{symptom_key.replace('_', ' ').title()}**")
                results.append(f"Common causes: {', '.join(info.get('common_causes', [])[:4])}")
                results.append(f"Questions to ask: {info.get('questions', [''])[0]}")
                results.append(f"See doctor if: {', '.join(info.get('see_doctor_if', [])[:2])}")
                results.append(f"Recommended specialist: {info.get('specialist', 'Primary Care')}")
                break
        
        # Add disclaimer
        if results:
            results.append("\n[*] DISCLAIMER: This is for informational purposes only. Always consult a healthcare professional.")
        
        return "\n".join(results) if results else None
    
    def get_system_prompt_with_knowledge(self) -> str:
        """
        Get an enhanced system prompt that describes Monica's knowledge.
        """
        kb_list = ", ".join([kb['name'] for kb in self.knowledge_bases.values()])
        
        return f"""You are Monica, an advanced AI assistant with comprehensive knowledge across many domains.

Your knowledge bases include: {kb_list}

You have expertise in:
- K-12 Education (all subjects, kindergarten through 12th grade)
- Mathematics (from basic arithmetic to advanced calculus, statistics, and beyond)
- Software & Programming (Adobe Creative Cloud, 12+ programming languages, game engines)
- Counseling & Therapy (19 therapeutic modalities including CBT, DBT, ACT, EMDR)
- Emotion Intelligence (facial expressions, body language, sentiment analysis)
- Language Teaching (61+ world languages with grammar, vocabulary, pronunciation)
- Legal & Sciences (law, physics, chemistry, biology, and more)
- 2025 Current Knowledge (AI developments, tech, entertainment, world events, sports)

Current Date Context: December 2025
- You know about GPT-4, Claude 3, Gemini, Llama 3, and other 2024-2025 AI models
- You know about iPhone 16, Apple Intelligence, Vision Pro, RTX 50 series
- You know about 2024 movies, music (Taylor Swift Eras Tour), and TV shows
- You know about the 2024 Paris Olympics and other recent events
- You know about current social media (TikTok, Instagram, X/Twitter, Threads)

When answering questions:
1. Draw from your knowledge bases when relevant
2. Provide accurate, helpful, and detailed responses
3. If you're not sure about something, say so
4. Be warm, friendly, and supportive
5. For complex topics, break down explanations clearly

You can also search the internet for current information when needed.

You have access to:
- Location Services: Get current location, find nearby places, get directions
- Satellite Services: Track ISS, view Earth imagery, get space data, see astronauts in space
"""
    
    def _search_location(self, query: str, data: Any) -> Optional[str]:
        """Search location services for location-based queries."""
        if not self.location_services:
            return None
        
        query_lower = query.lower()
        results = []
        
        # Location keywords
        location_keywords = ['where am i', 'my location', 'current location', 'nearby',
                           'latitude', 'longitude', 'coordinates', 'city', 'country',
                           'timezone', 'ip address']
        
        if not any(kw in query_lower for kw in location_keywords):
            return None
        
        try:
            loc = self.location_services.get_current_location()
            if loc:
                results.append(f"Your current location: {loc.get('city', '?')}, {loc.get('region', '')}, {loc.get('country', '?')}")
                results.append(f"Coordinates: {loc.get('lat', 0):.4f}, {loc.get('lon', 0):.4f}")
                if loc.get('timezone'):
                    results.append(f"Timezone: {loc.get('timezone')}")
                if loc.get('isp'):
                    results.append(f"ISP: {loc.get('isp')}")
            
            # Geocode a place if the user is asking about a specific location
            for prefix in ['where is ', 'find ', 'locate ']:
                if prefix in query_lower:
                    place = query_lower.split(prefix)[-1].strip().strip('?')
                    if place and len(place) > 1:
                        geo = self.location_services.geocode(place)
                        if geo:
                            results.append(f"\n{geo.get('display_name', place)}:")
                            results.append(f"  Coordinates: {geo.get('lat', 0):.4f}, {geo.get('lon', 0):.4f}")
                    break
        
        except Exception as e:
            print(f"[KNOWLEDGE] Location search error: {e}")
        
        return "\n".join(results) if results else None
    
    def _search_satellite(self, query: str, data: Any) -> Optional[str]:
        """Search satellite services for space-related queries."""
        if not self.satellite_services:
            return None
        
        query_lower = query.lower()
        results = []
        
        # Satellite keywords
        satellite_keywords = ['iss', 'space station', 'satellite', 'astronaut', 'space',
                            'nasa', 'mars', 'asteroid', 'hubble', 'earth imagery',
                            'people in space', 'orbit', 'tracking']
        
        if not any(kw in query_lower for kw in satellite_keywords):
            return None
        
        try:
            # ISS position
            if any(kw in query_lower for kw in ['iss', 'space station', 'international space']):
                iss = self.satellite_services.get_iss_position()
                if iss:
                    results.append(f"International Space Station (ISS):")
                    results.append(f"  Position: {iss.latitude:.2f}N, {iss.longitude:.2f}E")
                    results.append(f"  Altitude: {iss.altitude_km:.0f} km")
                    results.append(f"  Speed: {iss.velocity_km_s:.1f} km/s ({iss.velocity_km_s * 3600:.0f} km/h)")
                    results.append(f"  Track live: {self.satellite_services.get_satellite_map_url('iss')}")
            
            # People in space
            if any(kw in query_lower for kw in ['astronaut', 'people in space', 'who is in space']):
                astros = self.satellite_services.get_people_in_space()
                if astros['count'] > 0:
                    results.append(f"\nPeople currently in space: {astros['count']}")
                    for person in astros['people']:
                        results.append(f"  - {person['name']} ({person['craft']})")
            
            # NASA Picture of the Day
            if 'nasa' in query_lower and ('picture' in query_lower or 'image' in query_lower or 'photo' in query_lower):
                apod = self.satellite_services.get_nasa_apod()
                if apod:
                    results.append(f"\nNASA Astronomy Picture of the Day:")
                    results.append(f"  Title: {apod['title']}")
                    results.append(f"  Date: {apod['date']}")
                    results.append(f"  URL: {apod['url']}")
            
            # Near Earth Objects (asteroids)
            if 'asteroid' in query_lower:
                asteroids = self.satellite_services.get_neo_asteroids()
                if asteroids:
                    results.append(f"\nNear Earth Asteroids (next 7 days):")
                    hazardous = [a for a in asteroids if a['is_hazardous']]
                    results.append(f"  Total: {len(asteroids)}, Potentially hazardous: {len(hazardous)}")
                    for a in asteroids[:3]:
                        results.append(f"  - {a['name']}: {a['miss_distance_km']:.0f} km away on {a['close_approach_date']}")
            
            # Weather satellite imagery
            if 'weather' in query_lower and 'satellite' in query_lower:
                imagery = self.satellite_services.get_weather_satellite_imagery()
                results.append("\nWeather Satellite Imagery (GOES-16):")
                results.append(f"  Full Disk: {imagery['full_disk']}")
                results.append(f"  Continental US: {imagery['conus']}")
            
            # Space summary
            if query_lower.strip() in ['space', 'space news', 'space update']:
                summary = self.satellite_services.get_space_summary()
                results.append(summary)
        
        except Exception as e:
            print(f"[KNOWLEDGE] Satellite search error: {e}")
        
        return "\n".join(results) if results else None
    
    def _search_free_apis(self, query: str, data: Any) -> Optional[str]:
        """Search free APIs for real-time information.
        
        Uses the FreeAPIs class which provides:
        - get_weather(lat, lon) -> dict with temperature_f, condition, etc.
        - search_wikipedia(query) -> dict with title, summary
        - define_word(word) -> dict with word, meanings
        - get_nasa_apod() -> dict with title, explanation
        - get_joke() -> str
        - get_world_time(tz) -> dict with datetime, timezone
        - search(query) -> dict with results from relevant APIs
        """
        if not self.free_apis:
            return None
        
        query_lower = query.lower()
        results = []
        
        try:
            # Use the smart search method which auto-detects query type
            api_results = self.free_apis.search(query)
            
            # === WEATHER ===
            if 'weather' in api_results:
                w = api_results['weather']
                results.append(f"Current Weather:")
                if w.get('temperature_f') is not None:
                    results.append(f"  Temperature: {w['temperature_f']}°F (feels like {w.get('feels_like_f', '?')}°F)")
                if w.get('condition'):
                    results.append(f"  Condition: {w['condition']}")
                if w.get('humidity') is not None:
                    results.append(f"  Humidity: {w['humidity']}%")
                if w.get('wind_speed_mph') is not None:
                    results.append(f"  Wind: {w['wind_speed_mph']} mph")
            
            # === WIKIPEDIA ===
            if 'wikipedia' in api_results:
                wiki = api_results['wikipedia']
                results.append(f"Wikipedia - {wiki.get('title', '')}:")
                summary = wiki.get('summary', '')
                if len(summary) > 400:
                    summary = summary[:400] + "..."
                results.append(f"  {summary}")
            
            # === DICTIONARY ===
            if 'dictionary' in api_results:
                defn = api_results['dictionary']
                results.append(f"Definition of '{defn.get('word', '')}':")
                if defn.get('phonetic'):
                    results.append(f"  Pronunciation: {defn['phonetic']}")
                for meaning in defn.get('meanings', [])[:2]:
                    results.append(f"  ({meaning.get('part_of_speech', '')})")
                    for d in meaning.get('definitions', [])[:2]:
                        results.append(f"    - {d}")
            
            # === NASA APOD ===
            if 'nasa_apod' in api_results:
                apod = api_results['nasa_apod']
                results.append(f"NASA Astronomy Picture of the Day:")
                results.append(f"  Title: {apod.get('title', '')}")
                results.append(f"  Date: {apod.get('date', '')}")
                explanation = apod.get('explanation', '')[:300]
                if len(apod.get('explanation', '')) > 300:
                    explanation += "..."
                results.append(f"  {explanation}")
            
            # === JOKE ===
            if 'joke' in api_results:
                results.append(f"Joke: {api_results['joke']}")
            
            # === WORLD TIME ===
            if 'world_time' in api_results:
                t = api_results['world_time']
                results.append(f"Current Time ({t.get('timezone', '')}):")
                results.append(f"  {t.get('datetime', '')}")
            
            # If smart search found nothing, try direct weather with location services
            if not results:
                weather_keywords = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy']
                if any(kw in query_lower for kw in weather_keywords):
                    try:
                        from utils.location_services import get_location_services
                        loc = get_location_services().get_current_location()
                        if loc:
                            weather = self.free_apis.get_weather(loc['lat'], loc['lon'])
                            if weather:
                                results.append(f"Weather in {loc.get('city', 'your area')}:")
                                results.append(f"  {weather.get('temperature_f', '?')}°F, {weather.get('condition', '?')}")
                    except Exception:
                        pass
            
            # Wikipedia fallback for general "who is" / "what is" queries
            if not results:
                wiki_keywords = ['who is', 'who was', 'what is', 'what was', 'tell me about', 'wikipedia']
                if any(kw in query_lower for kw in wiki_keywords):
                    search_term = query
                    for kw in wiki_keywords:
                        search_term = search_term.lower().replace(kw, '').strip()
                    search_term = search_term.strip('?').strip()
                    if search_term and len(search_term) > 2:
                        wiki = self.free_apis.search_wikipedia(search_term)
                        if wiki:
                            results.append(f"Wikipedia - {wiki.get('title', '')}:")
                            summary = wiki.get('summary', '')[:400]
                            results.append(f"  {summary}")
        
        except Exception as e:
            print(f"[KNOWLEDGE] Free APIs search error: {e}")
            import traceback
            traceback.print_exc()
        
        return "\n".join(results) if results else None


    def _search_university(self, query: str, data: Dict) -> Optional[str]:
        """Search university teaching subjects."""
        if not data:
            return None
        results = []
        for subj_key, subj_data in data.items():
            subj_name = subj_data.get('name', subj_key).lower()
            # Check if query matches subject name or topic names
            if any(word in subj_name for word in query.split() if len(word) > 2):
                results.append(f"Subject: {subj_data.get('name', subj_key)}")
                results.append(f"Overview: {subj_data.get('overview', '')[:200]}")
                for topic_key, topic_data in subj_data.get('topics', {}).items():
                    results.append(f"  Topic: {topic_data.get('title', topic_key)}")
                break  # One subject match is enough
            # Also check topic content
            for topic_key, topic_data in subj_data.get('topics', {}).items():
                content = topic_data.get('content', '').lower()
                if any(word in content for word in query.split() if len(word) > 3):
                    results.append(f"Subject: {subj_data.get('name', subj_key)}")
                    results.append(f"Topic: {topic_data.get('title', topic_key)}")
                    # Return relevant snippet
                    snippet = topic_data.get('content', '')[:400]
                    results.append(snippet)
                    break
            if results:
                break
        return "\n".join(results) if results else None

    def _search_learned(self, query: str, data) -> Optional[str]:
        """Search learned knowledge (URLs, spoken facts)."""
        if not hasattr(self, 'knowledge_learner') or not self.knowledge_learner:
            return None
        try:
            return self.knowledge_learner.get_relevant_knowledge(query, top_k=2)
        except Exception:
            return None

    def _search_weather(self, query: str, data: Any) -> Optional[str]:
        """Search weather system for weather-related queries."""
        if not self.weather_system:
            return None
        
        query_lower = query.lower()
        weather_keywords = ['weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny',
                           'cloudy', 'wind', 'humidity', 'storm', 'hot', 'cold', 'warm',
                           'degrees', 'celsius', 'fahrenheit', 'climate']
        
        if not any(kw in query_lower for kw in weather_keywords):
            return None
        
        try:
            # Extract location from query
            location = query
            for kw in weather_keywords + ['what is the', 'how is the', 'in', 'for', 'at', 'whats']:
                location = location.lower().replace(kw, '').strip()
            location = location.strip('?').strip()
            
            if not location or len(location) < 2:
                location = "Orlando, FL"  # Default to user's location
            
            summary = self.weather_system.get_weather_summary(location)
            return summary
        except Exception as e:
            print(f"[KNOWLEDGE] Weather search error: {e}")
            return None

    def _search_cameras(self, query: str, data: Any) -> Optional[str]:
        """Search world camera network for camera/webcam queries."""
        if not self.world_cameras:
            return None
        
        query_lower = query.lower()
        camera_keywords = ['camera', 'webcam', 'cam', 'live view', 'live feed', 'watch',
                          'see', 'look at', 'show me', 'zoom in', 'view of']
        
        if not any(kw in query_lower for kw in camera_keywords):
            return None
        
        try:
            # Extract location from query
            location = query
            for kw in camera_keywords + ['the', 'in', 'at', 'of', 'from', 'near']:
                location = location.lower().replace(kw, '').strip()
            location = location.strip('?').strip()
            
            if not location or len(location) < 2:
                return None
            
            cameras = self.world_cameras.search_cameras(location, limit=5)
            if not cameras:
                return f"No cameras found for '{location}'."
            
            results = [f"Public Cameras near {location.title()} ({len(cameras)} found):"]
            for cam in cameras[:5]:
                results.append(f"  - {cam.title} ({cam.category})")
                results.append(f"    Location: {cam.city}, {cam.country}")
                results.append(f"    View: {cam.url}")
            
            stats = self.world_cameras.get_stats()
            results.append(f"\nTotal network: {stats['total_cameras']} cameras across {stats['regions']} regions")
            return "\n".join(results)
        except Exception as e:
            print(f"[KNOWLEDGE] Camera search error: {e}")
            return None


# Singleton instance
_knowledge_connector = None

def get_knowledge_connector() -> KnowledgeConnector:
    """Get the singleton knowledge connector instance."""
    global _knowledge_connector
    if _knowledge_connector is None:
        _knowledge_connector = KnowledgeConnector()
    return _knowledge_connector
