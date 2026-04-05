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
            from monica_education_k12 import K12_CURRICULUM
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
            from monica_math_complete import MATHEMATICS_KNOWLEDGE
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
            from monica_software_skills import ADOBE_KNOWLEDGE, PROGRAMMING_LANGUAGES
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
            from monica_counseling_comprehensive import COUNSELING_MODALITIES, ACADEMIC_SOURCES, MENTAL_HEALTH_CONDITIONS
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
            from monica_emotion_intelligence import EMOTION_TAXONOMY
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
            from monica_language_teacher import WORLD_LANGUAGES
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
            from monica_knowledge_base import KNOWLEDGE_DOMAINS
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
            from monica_legal_sciences import MonicaLegalKnowledge, MonicaSciencesKnowledge
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
            from monica_knowledge_2025 import KNOWLEDGE_2025, CURRENT_CONTEXT, MONICA_QUICK_FACTS_2025
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
            from monica_global_webcams import GLOBAL_WEBCAMS
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
            from monica_medical_knowledge import MEDICAL_KNOWLEDGE, get_medical_assistant
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
            from monica_intelligence import INTELLIGENCE_KNOWLEDGE
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
            from monica_authentic_personality import MonicaAuthenticPersonality
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
            from ..utils.location_services import get_location_services
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
            from ..utils.satellite_services import get_satellite_services
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
            from ..utils.free_apis import get_free_apis
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
                                results.append(f"  • {skill}")
        
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
                            results.append(f"    • {k}: {v}")
                    else:
                        results.append(f"  • {subtopic}: {content}")
        
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
                        results.append(f"  • {f}")
                
                shortcuts = app_data.get('shortcuts', {})
                if shortcuts and 'shortcut' in query:
                    results.append("Shortcuts:")
                    for key, action in list(shortcuts.items())[:5]:
                        results.append(f"  • {key}: {action}")
        
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
                        results.append(f"  • {t}")
        
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
                        results.append(f"  • {k}: {v}")
        
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
                            results.append(f"• {item}")
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
                            results.append(f"• {item}")
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
                           'find', 'restaurant', 'hospital', 'pharmacy', 'gas station',
                           'atm', 'bank', 'park', 'directions', 'map', 'address',
                           'latitude', 'longitude', 'coordinates', 'city', 'country']
        
        if not any(kw in query_lower for kw in location_keywords):
            return None
        
        try:
            # Get current location
            if any(kw in query_lower for kw in ['where am i', 'my location', 'current location', 'city', 'country']):
                loc = self.location_services.get_current_location()
                if loc:
                    results.append(f"Your current location: {loc.city}, {loc.region}, {loc.country}")
                    results.append(f"Coordinates: {loc.latitude:.4f}, {loc.longitude:.4f}")
                    results.append(f"Timezone: {loc.timezone}")
            
            # Find nearby places
            place_types = ['restaurant', 'cafe', 'hospital', 'pharmacy', 'gas station', 
                          'atm', 'bank', 'supermarket', 'park', 'hotel', 'gym']
            for place_type in place_types:
                if place_type in query_lower:
                    places = self.location_services.find_nearby_places(place_type.replace(' ', '_'), radius_meters=2000)
                    if places:
                        results.append(f"\nNearby {place_type}s:")
                        for p in places[:5]:
                            results.append(f"  - {p['name']}")
                            if p.get('address'):
                                results.append(f"    Address: {p['address']}")
                    else:
                        results.append(f"No {place_type}s found nearby.")
                    break
            
            # Get map URL
            if 'map' in query_lower:
                map_url = self.location_services.get_map_url()
                results.append(f"\nMap: {map_url}")
        
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
        """Search free APIs for real-time information."""
        if not self.free_apis:
            return None
        
        query_lower = query.lower()
        results = []
        
        try:
            # === WEATHER ===
            weather_keywords = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy', 'hot', 'cold']
            if any(kw in query_lower for kw in weather_keywords):
                # Extract location from query
                location = None
                for word in ['in', 'at', 'for']:
                    if word in query_lower:
                        parts = query_lower.split(word)
                        if len(parts) > 1:
                            location = parts[-1].strip().strip('?').strip()
                            break
                
                if not location:
                    location = "New York"  # Default
                
                weather = self.free_apis.get_weather(location=location)
                if weather.get("success"):
                    current = weather.get("current", {})
                    results.append(f"Weather in {weather.get('location', location)}:")
                    results.append(f"  Temperature: {current.get('temperature')}°F (feels like {current.get('feels_like')}°F)")
                    results.append(f"  Condition: {current.get('condition')}")
                    results.append(f"  Humidity: {current.get('humidity')}%")
                    results.append(f"  Wind: {current.get('wind_speed')} mph")
            
            # === DICTIONARY / DEFINE ===
            define_keywords = ['define', 'definition', 'meaning of', 'what does', 'what is a ', 'what is an ']
            if any(kw in query_lower for kw in define_keywords):
                # Extract word to define
                word = None
                for kw in define_keywords:
                    if kw in query_lower:
                        word = query_lower.split(kw)[-1].strip().strip('?').split()[0]
                        break
                
                if word:
                    defn = self.free_apis.define_word(word)
                    if defn.get("success"):
                        results.append(f"Definition of '{defn.get('word')}':")
                        if defn.get("phonetic"):
                            results.append(f"  Pronunciation: {defn.get('phonetic')}")
                        for meaning in defn.get("meanings", [])[:2]:
                            results.append(f"  ({meaning.get('part_of_speech')})")
                            for d in meaning.get("definitions", [])[:1]:
                                results.append(f"    - {d.get('definition')}")
                                if d.get("example"):
                                    results.append(f"      Example: \"{d.get('example')}\"")
            
            # === JOKES ===
            joke_keywords = ['joke', 'funny', 'make me laugh', 'tell me something funny']
            if any(kw in query_lower for kw in joke_keywords):
                if 'dad' in query_lower:
                    joke = self.free_apis.get_dad_joke()
                    if joke.get("success"):
                        results.append(f"Dad Joke: {joke.get('joke')}")
                elif 'chuck' in query_lower or 'norris' in query_lower:
                    joke = self.free_apis.get_chuck_norris_joke()
                    if joke.get("success"):
                        results.append(f"Chuck Norris Fact: {joke.get('joke')}")
                else:
                    joke = self.free_apis.get_joke()
                    if joke.get("success"):
                        if joke.get("type") == "single":
                            results.append(f"Joke: {joke.get('joke')}")
                        else:
                            results.append(f"Joke: {joke.get('setup')} ... {joke.get('delivery')}")
            
            # === QUOTES ===
            quote_keywords = ['quote', 'inspirational', 'motivational', 'wisdom']
            if any(kw in query_lower for kw in quote_keywords):
                quote = self.free_apis.get_quote()
                if quote.get("success"):
                    results.append(f'Quote: "{quote.get("content")}" - {quote.get("author")}')
            
            # === ADVICE ===
            advice_keywords = ['advice', 'tip', 'suggestion', 'what should i']
            if any(kw in query_lower for kw in advice_keywords):
                advice = self.free_apis.get_advice()
                if advice.get("success"):
                    results.append(f"Advice: {advice.get('advice')}")
            
            # === AFFIRMATION ===
            affirmation_keywords = ['affirmation', 'positive', 'encourage', 'cheer me up']
            if any(kw in query_lower for kw in affirmation_keywords):
                affirmation = self.free_apis.get_affirmation()
                if affirmation.get("success"):
                    results.append(f"Affirmation: {affirmation.get('affirmation')}")
            
            # === ISS / SPACE STATION ===
            iss_keywords = ['iss', 'space station', 'international space']
            if any(kw in query_lower for kw in iss_keywords):
                iss = self.free_apis.get_iss_location()
                if iss.get("success"):
                    results.append(f"ISS Location: Currently over {iss.get('location')}")
                    results.append(f"  Coordinates: {iss.get('latitude'):.2f}°, {iss.get('longitude'):.2f}°")
            
            # === ASTRONAUTS ===
            astronaut_keywords = ['astronaut', 'people in space', 'who is in space']
            if any(kw in query_lower for kw in astronaut_keywords):
                astros = self.free_apis.get_astronauts_in_space()
                if astros.get("success"):
                    results.append(f"People in Space: {astros.get('count')} astronauts")
                    for craft, names in astros.get("by_craft", {}).items():
                        results.append(f"  {craft}: {', '.join(names)}")
            
            # === EARTHQUAKES ===
            earthquake_keywords = ['earthquake', 'seismic', 'quake']
            if any(kw in query_lower for kw in earthquake_keywords):
                quakes = self.free_apis.get_earthquakes(min_magnitude=4.0, days=7)
                if quakes.get("success"):
                    results.append(f"Recent Earthquakes (M4.0+, last 7 days): {quakes.get('count')} events")
                    for q in quakes.get("earthquakes", [])[:5]:
                        results.append(f"  - M{q.get('magnitude')} near {q.get('location')} ({q.get('time')})")
            
            # === CURRENCY CONVERSION ===
            currency_keywords = ['convert', 'currency', 'exchange', 'dollars to', 'euros to', 'usd', 'eur', 'gbp']
            if any(kw in query_lower for kw in currency_keywords):
                # Try to extract amount and currencies
                import re
                # Pattern: "100 usd to eur" or "convert 50 dollars to euros"
                match = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)\s+to\s+(\w+)', query_lower)
                if match:
                    amount = float(match.group(1))
                    from_curr = match.group(2).upper()
                    to_curr = match.group(3).upper()
                    
                    # Map common names to codes
                    currency_map = {
                        'DOLLARS': 'USD', 'DOLLAR': 'USD', 'BUCKS': 'USD',
                        'EUROS': 'EUR', 'EURO': 'EUR',
                        'POUNDS': 'GBP', 'POUND': 'GBP',
                        'YEN': 'JPY', 'YUAN': 'CNY'
                    }
                    from_curr = currency_map.get(from_curr, from_curr)
                    to_curr = currency_map.get(to_curr, to_curr)
                    
                    result = self.free_apis.convert_currency(amount, from_curr, to_curr)
                    if result.get("success"):
                        results.append(f"Currency Conversion: {amount} {from_curr} = {result.get('converted')} {to_curr}")
                        results.append(f"  Exchange rate: 1 {from_curr} = {result.get('rate')} {to_curr}")
            
            # === NASA APOD ===
            nasa_keywords = ['nasa', 'astronomy picture', 'space picture', 'apod']
            if any(kw in query_lower for kw in nasa_keywords) and ('picture' in query_lower or 'image' in query_lower or 'photo' in query_lower or 'apod' in query_lower):
                apod = self.free_apis.get_nasa_apod()
                if apod.get("success"):
                    results.append(f"NASA Astronomy Picture of the Day:")
                    results.append(f"  Title: {apod.get('title')}")
                    results.append(f"  Date: {apod.get('date')}")
                    # Truncate explanation
                    explanation = apod.get('explanation', '')[:300]
                    if len(apod.get('explanation', '')) > 300:
                        explanation += "..."
                    results.append(f"  Description: {explanation}")
            
            # === SPACEX ===
            spacex_keywords = ['spacex', 'rocket launch', 'falcon', 'starship']
            if any(kw in query_lower for kw in spacex_keywords):
                launch = self.free_apis.get_spacex_latest_launch()
                if launch.get("success"):
                    results.append(f"Latest SpaceX Launch:")
                    results.append(f"  Mission: {launch.get('name')}")
                    results.append(f"  Date: {launch.get('date')}")
                    results.append(f"  Success: {'Yes' if launch.get('success') else 'No' if launch.get('success') is False else 'Unknown'}")
            
            # === TRIVIA ===
            trivia_keywords = ['trivia', 'quiz', 'test me', 'random fact']
            if any(kw in query_lower for kw in trivia_keywords):
                trivia = self.free_apis.get_trivia()
                if trivia.get("success"):
                    results.append(f"Trivia Question ({trivia.get('category')}, {trivia.get('difficulty')}):")
                    results.append(f"  Q: {trivia.get('question')}")
                    results.append(f"  A: {trivia.get('correct_answer')}")
            
            # === NUMBER FACTS ===
            number_keywords = ['number fact', 'fact about']
            if any(kw in query_lower for kw in number_keywords):
                # Try to extract a number
                import re
                numbers = re.findall(r'\d+', query)
                num = int(numbers[0]) if numbers else None
                fact = self.free_apis.get_number_fact(num)
                if fact.get("success"):
                    results.append(f"Number Fact: {fact.get('fact')}")
            
            # === SUNRISE/SUNSET ===
            sun_keywords = ['sunrise', 'sunset', 'sun time', 'daylight']
            if any(kw in query_lower for kw in sun_keywords):
                # Default to NYC coordinates
                sun = self.free_apis.get_sunrise_sunset(40.7128, -74.0060)
                if sun.get("success"):
                    results.append(f"Sun Times (New York):")
                    results.append(f"  Sunrise: {sun.get('sunrise')}")
                    results.append(f"  Sunset: {sun.get('sunset')}")
                    results.append(f"  Day Length: {sun.get('day_length')}")
            
            # === COUNTRY INFORMATION ===
            country_keywords = ['capital of', 'population of', 'language in', 'languages in', 
                              'currency in', 'currency of', 'about country', 'tell me about',
                              'where is', 'country', 'countries in', 'speak', 'spoken in']
            if any(kw in query_lower for kw in country_keywords):
                # Extract country name
                country_name = None
                
                # Pattern: "capital of Japan" or "what is the capital of Japan"
                for pattern in ['capital of ', 'population of ', 'currency of ', 'currency in ',
                               'language in ', 'languages in ', 'about country ', 'where is ']:
                    if pattern in query_lower:
                        country_name = query_lower.split(pattern)[-1].strip().strip('?')
                        break
                
                # Pattern: "countries in Asia" or "countries in Europe"
                if 'countries in ' in query_lower:
                    region = query_lower.split('countries in ')[-1].strip().strip('?')
                    region_data = self.free_apis.get_countries_by_region(region)
                    if region_data.get("success"):
                        results.append(f"Countries in {region.title()} ({region_data.get('count')} total):")
                        for c in region_data.get("countries", [])[:10]:
                            pop_millions = c.get('population', 0) / 1_000_000
                            results.append(f"  {c.get('flag_emoji', '')} {c.get('name')} - Capital: {c.get('capital')}, Pop: {pop_millions:.1f}M")
                
                # Pattern: "what countries speak Spanish"
                elif 'speak' in query_lower or 'spoken' in query_lower:
                    for lang in ['spanish', 'french', 'arabic', 'portuguese', 'german', 'chinese', 
                                'japanese', 'russian', 'italian', 'korean', 'hindi', 'english']:
                        if lang in query_lower:
                            lang_data = self.free_apis.get_countries_by_language(lang)
                            if lang_data.get("success"):
                                results.append(f"Countries where {lang.title()} is spoken ({lang_data.get('count')} countries):")
                                for c in lang_data.get("countries", [])[:10]:
                                    results.append(f"  {c.get('flag_emoji', '')} {c.get('name')}")
                            break
                
                # Get specific country info
                elif country_name:
                    country_data = self.free_apis.get_country_info(country_name)
                    if country_data.get("success"):
                        results.append(f"{country_data.get('flag_emoji', '')} {country_data.get('name')} ({country_data.get('official_name', '')}):")
                        results.append(f"  Capital: {country_data.get('capital')}")
                        pop_millions = country_data.get('population', 0) / 1_000_000
                        results.append(f"  Population: {pop_millions:.1f} million")
                        results.append(f"  Region: {country_data.get('region')} / {country_data.get('subregion')}")
                        if country_data.get('languages'):
                            results.append(f"  Languages: {', '.join(country_data.get('languages', []))}")
                        if country_data.get('currencies'):
                            curr = country_data['currencies'][0]
                            results.append(f"  Currency: {curr.get('name')} ({curr.get('symbol', '')} {curr.get('code')})")
                        results.append(f"  Coordinates: {country_data.get('lat'):.2f}°, {country_data.get('lon'):.2f}°")
                        if country_data.get('timezones'):
                            results.append(f"  Timezones: {', '.join(country_data.get('timezones', [])[:3])}")
            
            # === WIKIPEDIA (general knowledge fallback) ===
            wiki_keywords = ['who is', 'who was', 'what is', 'what was', 'tell me about', 'wikipedia']
            if not results and any(kw in query_lower for kw in wiki_keywords):
                # Extract search term
                search_term = query
                for kw in wiki_keywords:
                    search_term = search_term.lower().replace(kw, '').strip()
                search_term = search_term.strip('?').strip()
                
                if search_term and len(search_term) > 2:
                    wiki = self.free_apis.search_wikipedia(search_term, sentences=3)
                    if wiki.get("success"):
                        results.append(f"Wikipedia - {wiki.get('title')}:")
                        results.append(f"  {wiki.get('summary')}")
        
        except Exception as e:
            print(f"[KNOWLEDGE] Free APIs search error: {e}")
            import traceback
            traceback.print_exc()
        
        return "\n".join(results) if results else None


# Singleton instance
_knowledge_connector = None

def get_knowledge_connector() -> KnowledgeConnector:
    """Get the singleton knowledge connector instance."""
    global _knowledge_connector
    if _knowledge_connector is None:
        _knowledge_connector = KnowledgeConnector()
    return _knowledge_connector
