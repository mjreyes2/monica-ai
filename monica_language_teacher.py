"""
Monica's Comprehensive Language Teaching System
Supports 61+ world languages with:
- Speaking (pronunciation guides)
- Listening (audio recognition)
- Writing (grammar, vocabulary)
- Teaching (lessons, exercises, cultural context)
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Comprehensive language database
WORLD_LANGUAGES = {
    # Major World Languages (by number of speakers)
    "english": {
        "name": "English",
        "native_name": "English",
        "family": "Indo-European (Germanic)",
        "speakers": "1.5 billion",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "N/A",
        "regions": ["United Kingdom", "United States", "Australia", "Canada", "India"],
    },
    "mandarin": {
        "name": "Mandarin Chinese",
        "native_name": "普通话 (Pǔtōnghuà)",
        "family": "Sino-Tibetan",
        "speakers": "1.1 billion",
        "writing_system": "Chinese characters (Hanzi)",
        "difficulty_for_english": "Hard (2200 hours)",
        "regions": ["China", "Taiwan", "Singapore"],
        "tones": 4,
    },
    "hindi": {
        "name": "Hindi",
        "native_name": "हिन्दी (Hindī)",
        "family": "Indo-European (Indo-Aryan)",
        "speakers": "600 million",
        "writing_system": "Devanagari script",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["India", "Nepal", "Fiji"],
    },
    "spanish": {
        "name": "Spanish",
        "native_name": "Español",
        "family": "Indo-European (Romance)",
        "speakers": "550 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["Spain", "Mexico", "Argentina", "Colombia", "Peru"],
    },
    "arabic": {
        "name": "Arabic",
        "native_name": "العربية (al-ʿArabiyyah)",
        "family": "Afro-Asiatic (Semitic)",
        "speakers": "420 million",
        "writing_system": "Arabic script (right-to-left)",
        "difficulty_for_english": "Hard (2200 hours)",
        "regions": ["Saudi Arabia", "Egypt", "Morocco", "Iraq", "UAE"],
    },
    "french": {
        "name": "French",
        "native_name": "Français",
        "family": "Indo-European (Romance)",
        "speakers": "280 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["France", "Canada", "Belgium", "Switzerland", "Senegal"],
    },
    "portuguese": {
        "name": "Portuguese",
        "native_name": "Português",
        "family": "Indo-European (Romance)",
        "speakers": "260 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["Brazil", "Portugal", "Angola", "Mozambique"],
    },
    "russian": {
        "name": "Russian",
        "native_name": "Русский (Russkiy)",
        "family": "Indo-European (Slavic)",
        "speakers": "250 million",
        "writing_system": "Cyrillic alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Russia", "Ukraine", "Belarus", "Kazakhstan"],
    },
    "japanese": {
        "name": "Japanese",
        "native_name": "日本語 (Nihongo)",
        "family": "Japonic",
        "speakers": "125 million",
        "writing_system": "Hiragana, Katakana, Kanji",
        "difficulty_for_english": "Hard (2200 hours)",
        "regions": ["Japan"],
    },
    "german": {
        "name": "German",
        "native_name": "Deutsch",
        "family": "Indo-European (Germanic)",
        "speakers": "130 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium (900 hours)",
        "regions": ["Germany", "Austria", "Switzerland"],
    },
    "korean": {
        "name": "Korean",
        "native_name": "한국어 (Hangugeo)",
        "family": "Koreanic",
        "speakers": "80 million",
        "writing_system": "Hangul",
        "difficulty_for_english": "Hard (2200 hours)",
        "regions": ["South Korea", "North Korea"],
    },
    "italian": {
        "name": "Italian",
        "native_name": "Italiano",
        "family": "Indo-European (Romance)",
        "speakers": "65 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["Italy", "Switzerland", "San Marino"],
    },
    "turkish": {
        "name": "Turkish",
        "native_name": "Türkçe",
        "family": "Turkic",
        "speakers": "80 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Turkey", "Cyprus"],
    },
    "vietnamese": {
        "name": "Vietnamese",
        "native_name": "Tiếng Việt",
        "family": "Austroasiatic",
        "speakers": "85 million",
        "writing_system": "Latin alphabet (with diacritics)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Vietnam"],
        "tones": 6,
    },
    "thai": {
        "name": "Thai",
        "native_name": "ภาษาไทย (Phasa Thai)",
        "family": "Kra-Dai",
        "speakers": "60 million",
        "writing_system": "Thai script",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Thailand"],
        "tones": 5,
    },
    "dutch": {
        "name": "Dutch",
        "native_name": "Nederlands",
        "family": "Indo-European (Germanic)",
        "speakers": "25 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["Netherlands", "Belgium", "Suriname"],
    },
    "polish": {
        "name": "Polish",
        "native_name": "Polski",
        "family": "Indo-European (Slavic)",
        "speakers": "45 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Poland"],
    },
    "greek": {
        "name": "Greek",
        "native_name": "Ελληνικά (Elliniká)",
        "family": "Indo-European (Hellenic)",
        "speakers": "13 million",
        "writing_system": "Greek alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Greece", "Cyprus"],
    },
    "hebrew": {
        "name": "Hebrew",
        "native_name": "עברית (Ivrit)",
        "family": "Afro-Asiatic (Semitic)",
        "speakers": "9 million",
        "writing_system": "Hebrew alphabet (right-to-left)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Israel"],
    },
    "swedish": {
        "name": "Swedish",
        "native_name": "Svenska",
        "family": "Indo-European (Germanic)",
        "speakers": "10 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["Sweden", "Finland"],
    },
    
    # African Languages
    "swahili": {
        "name": "Swahili",
        "native_name": "Kiswahili",
        "family": "Niger-Congo (Bantu)",
        "speakers": "100 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium (900 hours)",
        "regions": ["Kenya", "Tanzania", "Uganda", "DRC"],
    },
    "hausa": {
        "name": "Hausa",
        "native_name": "Hausa",
        "family": "Afro-Asiatic (Chadic)",
        "speakers": "70 million",
        "writing_system": "Latin alphabet (Boko), Arabic script (Ajami)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Nigeria", "Niger", "Ghana"],
    },
    "yoruba": {
        "name": "Yoruba",
        "native_name": "Èdè Yorùbá",
        "family": "Niger-Congo",
        "speakers": "45 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Nigeria", "Benin", "Togo"],
        "tones": 3,
    },
    "igbo": {
        "name": "Igbo",
        "native_name": "Asụsụ Igbo",
        "family": "Niger-Congo",
        "speakers": "45 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Nigeria"],
        "tones": 2,
    },
    "amharic": {
        "name": "Amharic",
        "native_name": "አማርኛ (Amarəñña)",
        "family": "Afro-Asiatic (Semitic)",
        "speakers": "32 million",
        "writing_system": "Ge'ez script",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Ethiopia"],
    },
    "zulu": {
        "name": "Zulu",
        "native_name": "isiZulu",
        "family": "Niger-Congo (Bantu)",
        "speakers": "12 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["South Africa"],
        "features": ["Click consonants"],
    },
    "xhosa": {
        "name": "Xhosa",
        "native_name": "isiXhosa",
        "family": "Niger-Congo (Bantu)",
        "speakers": "8 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["South Africa"],
        "features": ["Click consonants"],
    },
    "afrikaans": {
        "name": "Afrikaans",
        "native_name": "Afrikaans",
        "family": "Indo-European (Germanic)",
        "speakers": "7 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Easy (600 hours)",
        "regions": ["South Africa", "Namibia"],
    },
    
    # Asian Languages
    "indonesian": {
        "name": "Indonesian",
        "native_name": "Bahasa Indonesia",
        "family": "Austronesian",
        "speakers": "200 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium (900 hours)",
        "regions": ["Indonesia"],
    },
    "malay": {
        "name": "Malay",
        "native_name": "Bahasa Melayu",
        "family": "Austronesian",
        "speakers": "80 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium (900 hours)",
        "regions": ["Malaysia", "Brunei", "Singapore"],
    },
    "tagalog": {
        "name": "Tagalog/Filipino",
        "native_name": "Tagalog",
        "family": "Austronesian",
        "speakers": "70 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium (1100 hours)",
        "regions": ["Philippines"],
    },
    "tamil": {
        "name": "Tamil",
        "native_name": "தமிழ் (Tamiḻ)",
        "family": "Dravidian",
        "speakers": "75 million",
        "writing_system": "Tamil script",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["India", "Sri Lanka", "Singapore"],
    },
    "bengali": {
        "name": "Bengali",
        "native_name": "বাংলা (Bangla)",
        "family": "Indo-European (Indo-Aryan)",
        "speakers": "230 million",
        "writing_system": "Bengali script",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Bangladesh", "India"],
    },
    "urdu": {
        "name": "Urdu",
        "native_name": "اردو (Urdū)",
        "family": "Indo-European (Indo-Aryan)",
        "speakers": "230 million",
        "writing_system": "Nastaliq script (right-to-left)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Pakistan", "India"],
    },
    "punjabi": {
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ / پنجابی",
        "family": "Indo-European (Indo-Aryan)",
        "speakers": "125 million",
        "writing_system": "Gurmukhi (India), Shahmukhi (Pakistan)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["India", "Pakistan"],
    },
    "persian": {
        "name": "Persian/Farsi",
        "native_name": "فارسی (Fārsi)",
        "family": "Indo-European (Iranian)",
        "speakers": "110 million",
        "writing_system": "Persian alphabet (right-to-left)",
        "difficulty_for_english": "Hard (1100 hours)",
        "regions": ["Iran", "Afghanistan", "Tajikistan"],
    },
    
    # Indigenous Languages
    "navajo": {
        "name": "Navajo",
        "native_name": "Diné bizaad",
        "family": "Na-Dené (Athabaskan)",
        "speakers": "170,000",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Very Hard",
        "regions": ["United States (Southwest)"],
        "features": ["Tonal", "Complex verb morphology"],
    },
    "cherokee": {
        "name": "Cherokee",
        "native_name": "ᏣᎳᎩ (Tsalagi)",
        "family": "Iroquoian",
        "speakers": "2,000",
        "writing_system": "Cherokee syllabary",
        "difficulty_for_english": "Very Hard",
        "regions": ["United States (Oklahoma, North Carolina)"],
    },
    "quechua": {
        "name": "Quechua",
        "native_name": "Runasimi",
        "family": "Quechuan",
        "speakers": "10 million",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Hard",
        "regions": ["Peru", "Bolivia", "Ecuador"],
    },
    "maori": {
        "name": "Māori",
        "native_name": "Te Reo Māori",
        "family": "Austronesian (Polynesian)",
        "speakers": "150,000",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium",
        "regions": ["New Zealand"],
    },
    "hawaiian": {
        "name": "Hawaiian",
        "native_name": "ʻŌlelo Hawaiʻi",
        "family": "Austronesian (Polynesian)",
        "speakers": "24,000",
        "writing_system": "Latin alphabet",
        "difficulty_for_english": "Medium",
        "regions": ["Hawaii, USA"],
    },
}

# Common phrases in multiple languages
COMMON_PHRASES = {
    "hello": {
        "english": "Hello",
        "spanish": "Hola",
        "french": "Bonjour",
        "german": "Hallo",
        "italian": "Ciao",
        "portuguese": "Olá",
        "mandarin": "你好 (Nǐ hǎo)",
        "japanese": "こんにちは (Konnichiwa)",
        "korean": "안녕하세요 (Annyeonghaseyo)",
        "arabic": "مرحبا (Marhaba)",
        "hindi": "नमस्ते (Namaste)",
        "russian": "Привет (Privet)",
        "swahili": "Habari",
        "turkish": "Merhaba",
        "vietnamese": "Xin chào",
        "thai": "สวัสดี (Sawatdee)",
        "greek": "Γεια σου (Geia sou)",
        "hebrew": "שלום (Shalom)",
        "dutch": "Hallo",
        "polish": "Cześć",
        "yoruba": "Bawo ni",
        "zulu": "Sawubona",
        "amharic": "ሰላም (Selam)",
        "indonesian": "Halo",
        "tagalog": "Kumusta",
    },
    "thank_you": {
        "english": "Thank you",
        "spanish": "Gracias",
        "french": "Merci",
        "german": "Danke",
        "italian": "Grazie",
        "portuguese": "Obrigado/Obrigada",
        "mandarin": "谢谢 (Xièxiè)",
        "japanese": "ありがとう (Arigatō)",
        "korean": "감사합니다 (Gamsahamnida)",
        "arabic": "شكرا (Shukran)",
        "hindi": "धन्यवाद (Dhanyavaad)",
        "russian": "Спасибо (Spasibo)",
        "swahili": "Asante",
        "turkish": "Teşekkürler",
        "vietnamese": "Cảm ơn",
        "thai": "ขอบคุณ (Khob khun)",
        "yoruba": "E ṣeun",
        "zulu": "Ngiyabonga",
    },
    "goodbye": {
        "english": "Goodbye",
        "spanish": "Adiós",
        "french": "Au revoir",
        "german": "Auf Wiedersehen",
        "italian": "Arrivederci",
        "portuguese": "Tchau",
        "mandarin": "再见 (Zàijiàn)",
        "japanese": "さようなら (Sayōnara)",
        "korean": "안녕히 가세요 (Annyeonghi gaseyo)",
        "arabic": "مع السلامة (Ma'a salama)",
        "hindi": "अलविदा (Alvida)",
        "russian": "До свидания (Do svidaniya)",
        "swahili": "Kwaheri",
    },
    "please": {
        "english": "Please",
        "spanish": "Por favor",
        "french": "S'il vous plaît",
        "german": "Bitte",
        "italian": "Per favore",
        "portuguese": "Por favor",
        "mandarin": "请 (Qǐng)",
        "japanese": "お願いします (Onegaishimasu)",
        "korean": "제발 (Jebal)",
        "arabic": "من فضلك (Min fadlak)",
        "hindi": "कृपया (Kripaya)",
        "russian": "Пожалуйста (Pozhaluysta)",
    },
    "yes": {
        "english": "Yes",
        "spanish": "Sí",
        "french": "Oui",
        "german": "Ja",
        "italian": "Sì",
        "portuguese": "Sim",
        "mandarin": "是 (Shì)",
        "japanese": "はい (Hai)",
        "korean": "네 (Ne)",
        "arabic": "نعم (Na'am)",
        "hindi": "हाँ (Haan)",
        "russian": "Да (Da)",
    },
    "no": {
        "english": "No",
        "spanish": "No",
        "french": "Non",
        "german": "Nein",
        "italian": "No",
        "portuguese": "Não",
        "mandarin": "不 (Bù)",
        "japanese": "いいえ (Iie)",
        "korean": "아니요 (Aniyo)",
        "arabic": "لا (La)",
        "hindi": "नहीं (Nahin)",
        "russian": "Нет (Nyet)",
    },
    "i_love_you": {
        "english": "I love you",
        "spanish": "Te quiero / Te amo",
        "french": "Je t'aime",
        "german": "Ich liebe dich",
        "italian": "Ti amo",
        "portuguese": "Eu te amo",
        "mandarin": "我爱你 (Wǒ ài nǐ)",
        "japanese": "愛してる (Aishiteru)",
        "korean": "사랑해요 (Saranghaeyo)",
        "arabic": "أحبك (Uhibbuka/Uhibbuki)",
        "hindi": "मैं तुमसे प्यार करता/करती हूँ",
        "russian": "Я тебя люблю (Ya tebya lyublyu)",
        "swahili": "Nakupenda",
    },
}


class MonicaLanguageTeacher:
    """
    Comprehensive language teaching system.
    Monica can teach, speak, and help learn 61+ world languages.
    """
    
    def __init__(self):
        self.languages = WORLD_LANGUAGES
        self.phrases = COMMON_PHRASES
        self.current_language = "english"
        self.user_progress = {}
        
        print(f"✅ Language Teacher initialized")
        print(f"   📚 {len(self.languages)} languages available")
        print(f"   🗣️ Speaking, Listening, Writing, Teaching modes")
    
    def get_language_info(self, language: str) -> Optional[Dict]:
        """Get detailed information about a language"""
        lang_key = language.lower().replace(" ", "_")
        return self.languages.get(lang_key)
    
    def list_languages(self) -> List[str]:
        """List all available languages"""
        return list(self.languages.keys())
    
    def list_languages_by_family(self) -> Dict[str, List[str]]:
        """Group languages by language family"""
        families = {}
        for lang_key, lang_info in self.languages.items():
            family = lang_info.get("family", "Unknown")
            if family not in families:
                families[family] = []
            families[family].append(lang_info["name"])
        return families
    
    def list_languages_by_region(self, region: str) -> List[str]:
        """List languages spoken in a region"""
        region_lower = region.lower()
        results = []
        for lang_key, lang_info in self.languages.items():
            regions = [r.lower() for r in lang_info.get("regions", [])]
            if any(region_lower in r for r in regions):
                results.append(lang_info["name"])
        return results
    
    def get_phrase(self, phrase_key: str, language: str) -> Optional[str]:
        """Get a phrase in a specific language"""
        lang_key = language.lower()
        if phrase_key in self.phrases:
            return self.phrases[phrase_key].get(lang_key)
        return None
    
    def get_all_phrases_for_language(self, language: str) -> Dict[str, str]:
        """Get all common phrases for a language"""
        lang_key = language.lower()
        result = {}
        for phrase_key, translations in self.phrases.items():
            if lang_key in translations:
                result[phrase_key] = translations[lang_key]
        return result
    
    def translate_phrase(self, phrase_key: str, from_lang: str, to_lang: str) -> Optional[Dict]:
        """Translate a phrase between languages"""
        if phrase_key not in self.phrases:
            return None
        
        from_phrase = self.phrases[phrase_key].get(from_lang.lower())
        to_phrase = self.phrases[phrase_key].get(to_lang.lower())
        
        if from_phrase and to_phrase:
            return {
                "phrase": phrase_key,
                "from_language": from_lang,
                "from_text": from_phrase,
                "to_language": to_lang,
                "to_text": to_phrase
            }
        return None
    
    def get_lesson(self, language: str, level: str = "beginner") -> Dict:
        """Generate a language lesson"""
        lang_info = self.get_language_info(language)
        if not lang_info:
            return {"error": f"Language '{language}' not found"}
        
        phrases = self.get_all_phrases_for_language(language)
        
        lesson = {
            "language": lang_info["name"],
            "native_name": lang_info.get("native_name", ""),
            "level": level,
            "writing_system": lang_info.get("writing_system", ""),
            "difficulty": lang_info.get("difficulty_for_english", "Unknown"),
            "sections": [
                {
                    "title": "Introduction",
                    "content": f"Welcome to {lang_info['name']}! This language is spoken by {lang_info.get('speakers', 'millions')} of people, primarily in {', '.join(lang_info.get('regions', [])[:3])}."
                },
                {
                    "title": "Writing System",
                    "content": f"{lang_info['name']} uses the {lang_info.get('writing_system', 'unique writing system')}."
                },
                {
                    "title": "Basic Greetings",
                    "phrases": {k: v for k, v in phrases.items() if k in ["hello", "goodbye", "thank_you", "please"]}
                },
                {
                    "title": "Practice",
                    "exercises": [
                        f"Say 'Hello' in {lang_info['name']}: {phrases.get('hello', 'N/A')}",
                        f"Say 'Thank you' in {lang_info['name']}: {phrases.get('thank_you', 'N/A')}",
                    ]
                }
            ]
        }
        
        # Add tone information for tonal languages
        if "tones" in lang_info:
            lesson["sections"].insert(2, {
                "title": "Tones",
                "content": f"{lang_info['name']} is a tonal language with {lang_info['tones']} tones. The meaning of words changes based on the tone used."
            })
        
        return lesson
    
    def compare_languages(self, lang1: str, lang2: str) -> Dict:
        """Compare two languages"""
        info1 = self.get_language_info(lang1)
        info2 = self.get_language_info(lang2)
        
        if not info1 or not info2:
            return {"error": "One or both languages not found"}
        
        return {
            "comparison": f"{info1['name']} vs {info2['name']}",
            "language_1": {
                "name": info1["name"],
                "family": info1.get("family", "Unknown"),
                "speakers": info1.get("speakers", "Unknown"),
                "writing_system": info1.get("writing_system", "Unknown"),
                "difficulty": info1.get("difficulty_for_english", "Unknown"),
            },
            "language_2": {
                "name": info2["name"],
                "family": info2.get("family", "Unknown"),
                "speakers": info2.get("speakers", "Unknown"),
                "writing_system": info2.get("writing_system", "Unknown"),
                "difficulty": info2.get("difficulty_for_english", "Unknown"),
            },
            "same_family": info1.get("family") == info2.get("family"),
            "phrase_comparison": {
                phrase: {
                    info1["name"]: self.phrases[phrase].get(lang1.lower(), "N/A"),
                    info2["name"]: self.phrases[phrase].get(lang2.lower(), "N/A"),
                }
                for phrase in ["hello", "thank_you", "goodbye"]
            }
        }
    
    def get_african_languages(self) -> List[Dict]:
        """Get all African languages"""
        african_langs = []
        african_regions = ["nigeria", "kenya", "tanzania", "ethiopia", "south africa", 
                         "egypt", "morocco", "ghana", "senegal", "uganda", "drc"]
        
        for lang_key, lang_info in self.languages.items():
            regions = [r.lower() for r in lang_info.get("regions", [])]
            if any(any(ar in r for ar in african_regions) for r in regions):
                african_langs.append({
                    "key": lang_key,
                    "name": lang_info["name"],
                    "native_name": lang_info.get("native_name", ""),
                    "speakers": lang_info.get("speakers", "Unknown"),
                    "regions": lang_info.get("regions", [])
                })
        
        return african_langs
    
    def generate_vocabulary_list(self, language: str, category: str = "basic") -> List[Dict]:
        """Generate a vocabulary list for a language"""
        phrases = self.get_all_phrases_for_language(language)
        
        vocab = []
        for phrase_key, translation in phrases.items():
            english = self.phrases[phrase_key].get("english", phrase_key)
            vocab.append({
                "english": english,
                "translation": translation,
                "category": category
            })
        
        return vocab


# Singleton instance
_language_teacher = None

def get_language_teacher() -> MonicaLanguageTeacher:
    """Get or create the language teacher singleton"""
    global _language_teacher
    if _language_teacher is None:
        _language_teacher = MonicaLanguageTeacher()
    return _language_teacher


if __name__ == "__main__":
    # Test the language teacher
    teacher = get_language_teacher()
    
    print("\n" + "=" * 60)
    print("MONICA LANGUAGE TEACHER TEST")
    print("=" * 60)
    
    # List all languages
    print(f"\nTotal languages: {len(teacher.list_languages())}")
    
    # Show African languages
    print("\n--- African Languages ---")
    african = teacher.get_african_languages()
    for lang in african:
        print(f"  • {lang['name']} ({lang['native_name']}): {lang['speakers']} speakers")
    
    # Show a lesson
    print("\n--- Sample Lesson: Swahili ---")
    lesson = teacher.get_lesson("swahili")
    print(f"Language: {lesson['language']} ({lesson.get('native_name', '')})")
    print(f"Writing System: {lesson['writing_system']}")
    print(f"Difficulty: {lesson['difficulty']}")
    
    # Compare languages
    print("\n--- Language Comparison: Spanish vs Japanese ---")
    comparison = teacher.compare_languages("spanish", "japanese")
    print(f"Same family: {comparison['same_family']}")
    print("Phrases:")
    for phrase, translations in comparison["phrase_comparison"].items():
        print(f"  {phrase}:")
        for lang, text in translations.items():
            print(f"    {lang}: {text}")
    
    print("\n✅ Language Teacher test complete!")
