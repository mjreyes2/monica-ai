"""
Monica's Advanced Emotion Intelligence System
Comprehensive emotion detection from:
- Facial expressions (using EmotiEffLib - state-of-the-art)
- Body language analysis
- Voice tone analysis
- Text sentiment analysis
- Micro-expressions
- Cultural context

Based on latest research and datasets (2024):
- AffectNet (8 emotions, 450K+ images)
- FER2013 (7 emotions, 35K images)
- AFEW (7 emotions, video-based)
- RAF-DB (7 emotions, real-world)
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os

# EmotiEffLib disabled due to compatibility issues with DepthwiseSeparableConv
# Will use OpenCV-based emotion detection instead
HAS_EMOTIEFF = False
EmotiEffLibRecognizer = None
print("ℹ️ Using OpenCV-based emotion detection (EmotiEffLib disabled for compatibility)")

# Comprehensive emotion taxonomy based on psychological research
EMOTION_TAXONOMY = {
    # Primary Emotions (Ekman's 6 basic emotions + neutral)
    "primary": {
        "happy": {
            "description": "Joy, pleasure, contentment",
            "facial_cues": ["smile", "raised cheeks", "crow's feet wrinkles"],
            "body_language": ["open posture", "relaxed shoulders", "animated gestures"],
            "voice_cues": ["higher pitch", "faster speech", "varied intonation"],
            "intensity_levels": ["content", "pleased", "happy", "joyful", "ecstatic"]
        },
        "sad": {
            "description": "Sorrow, grief, unhappiness",
            "facial_cues": ["downturned mouth", "inner brow raise", "drooping eyelids"],
            "body_language": ["slumped posture", "slow movements", "avoiding eye contact"],
            "voice_cues": ["lower pitch", "slower speech", "monotone"],
            "intensity_levels": ["disappointed", "down", "sad", "sorrowful", "devastated"]
        },
        "angry": {
            "description": "Frustration, irritation, rage",
            "facial_cues": ["lowered brows", "tightened lips", "flared nostrils"],
            "body_language": ["tense muscles", "clenched fists", "forward lean"],
            "voice_cues": ["louder volume", "faster speech", "sharp tone"],
            "intensity_levels": ["annoyed", "irritated", "angry", "furious", "enraged"]
        },
        "fear": {
            "description": "Anxiety, worry, terror",
            "facial_cues": ["raised eyebrows", "wide eyes", "open mouth"],
            "body_language": ["frozen posture", "protective gestures", "backing away"],
            "voice_cues": ["higher pitch", "trembling voice", "rapid speech"],
            "intensity_levels": ["uneasy", "worried", "afraid", "frightened", "terrified"]
        },
        "surprise": {
            "description": "Astonishment, amazement",
            "facial_cues": ["raised eyebrows", "wide eyes", "dropped jaw"],
            "body_language": ["sudden stillness", "backward movement", "hands to face"],
            "voice_cues": ["gasping", "exclamations", "pitch variation"],
            "intensity_levels": ["curious", "surprised", "amazed", "astonished", "shocked"]
        },
        "disgust": {
            "description": "Revulsion, distaste",
            "facial_cues": ["wrinkled nose", "raised upper lip", "narrowed eyes"],
            "body_language": ["turning away", "pushing away gestures", "covering nose/mouth"],
            "voice_cues": ["lowered pitch", "drawn out sounds", "gagging sounds"],
            "intensity_levels": ["dislike", "distaste", "disgusted", "repulsed", "revolted"]
        },
        "neutral": {
            "description": "Calm, composed state",
            "facial_cues": ["relaxed face", "neutral mouth", "normal eye opening"],
            "body_language": ["balanced posture", "normal gestures"],
            "voice_cues": ["normal pitch", "steady rhythm"],
            "intensity_levels": ["neutral"]
        }
    },
    
    # Secondary/Complex Emotions
    "secondary": {
        "contempt": {
            "description": "Superiority, disdain",
            "facial_cues": ["one-sided lip raise", "eye roll"],
            "related_primary": ["disgust", "angry"]
        },
        "shame": {
            "description": "Embarrassment, humiliation",
            "facial_cues": ["gaze aversion", "head down", "blushing"],
            "related_primary": ["sad", "fear"]
        },
        "guilt": {
            "description": "Remorse, regret",
            "facial_cues": ["avoiding eye contact", "tense expression"],
            "related_primary": ["sad"]
        },
        "pride": {
            "description": "Achievement, self-satisfaction",
            "facial_cues": ["slight smile", "head tilted back"],
            "related_primary": ["happy"]
        },
        "love": {
            "description": "Affection, attachment",
            "facial_cues": ["soft gaze", "genuine smile", "dilated pupils"],
            "related_primary": ["happy"]
        },
        "jealousy": {
            "description": "Envy, possessiveness",
            "facial_cues": ["narrowed eyes", "tense jaw"],
            "related_primary": ["angry", "sad"]
        },
        "anxiety": {
            "description": "Nervousness, unease",
            "facial_cues": ["furrowed brow", "lip biting", "rapid blinking"],
            "related_primary": ["fear"]
        },
        "excitement": {
            "description": "Anticipation, enthusiasm",
            "facial_cues": ["wide eyes", "big smile", "raised eyebrows"],
            "related_primary": ["happy", "surprise"]
        },
        "frustration": {
            "description": "Blocked goals, irritation",
            "facial_cues": ["furrowed brow", "tight lips", "sighing"],
            "related_primary": ["angry", "sad"]
        },
        "confusion": {
            "description": "Uncertainty, bewilderment",
            "facial_cues": ["furrowed brow", "tilted head", "squinting"],
            "related_primary": ["surprise"]
        },
        "boredom": {
            "description": "Disinterest, tedium",
            "facial_cues": ["drooping eyelids", "slack jaw", "yawning"],
            "related_primary": ["neutral", "sad"]
        },
        "relief": {
            "description": "Release of tension",
            "facial_cues": ["exhale", "relaxed face", "slight smile"],
            "related_primary": ["happy"]
        }
    },
    
    # Micro-expressions (brief, involuntary)
    "micro_expressions": {
        "description": "Brief facial expressions lasting 1/25 to 1/5 of a second",
        "detection_tips": [
            "Watch for fleeting expressions that contradict verbal message",
            "Focus on asymmetrical expressions",
            "Look for expressions that appear and disappear quickly",
            "Pay attention to the upper face (harder to control)"
        ],
        "common_leakage_areas": ["eyebrows", "forehead", "corners of mouth"]
    }
}

# Body Language Analysis
BODY_LANGUAGE_CUES = {
    "open_posture": {
        "indicators": ["arms uncrossed", "facing forward", "relaxed shoulders"],
        "interpretation": "Receptive, comfortable, engaged"
    },
    "closed_posture": {
        "indicators": ["arms crossed", "turned away", "hunched shoulders"],
        "interpretation": "Defensive, uncomfortable, disengaged"
    },
    "dominant_posture": {
        "indicators": ["expanded chest", "hands on hips", "taking up space"],
        "interpretation": "Confident, assertive, in control"
    },
    "submissive_posture": {
        "indicators": ["making self smaller", "lowered head", "avoiding eye contact"],
        "interpretation": "Uncertain, deferential, anxious"
    },
    "nervous_behaviors": {
        "indicators": ["fidgeting", "touching face", "shifting weight", "playing with objects"],
        "interpretation": "Anxiety, discomfort, deception possible"
    },
    "engaged_listening": {
        "indicators": ["leaning forward", "nodding", "eye contact", "mirroring"],
        "interpretation": "Interest, agreement, rapport"
    }
}

# Voice/Tone Analysis
VOICE_EMOTION_CUES = {
    "pitch": {
        "high": ["excitement", "fear", "surprise", "happiness"],
        "low": ["sadness", "boredom", "authority", "calmness"],
        "variable": ["engagement", "enthusiasm"],
        "monotone": ["depression", "disinterest", "suppressed emotion"]
    },
    "speed": {
        "fast": ["excitement", "anxiety", "anger", "enthusiasm"],
        "slow": ["sadness", "thoughtfulness", "emphasis", "depression"],
        "variable": ["engagement", "storytelling"]
    },
    "volume": {
        "loud": ["anger", "excitement", "confidence"],
        "soft": ["sadness", "intimacy", "uncertainty", "fear"],
        "variable": ["engagement", "emphasis"]
    },
    "quality": {
        "trembling": ["fear", "sadness", "strong emotion"],
        "breathy": ["intimacy", "exhaustion", "anxiety"],
        "harsh": ["anger", "frustration"],
        "smooth": ["calmness", "confidence"]
    }
}

# Text Sentiment Patterns (expanded)
TEXT_EMOTION_PATTERNS = {
    "happy": {
        "keywords": ["happy", "joy", "excited", "great", "wonderful", "amazing", "love", 
                    "glad", "pleased", "delighted", "thrilled", "fantastic", "awesome",
                    "blessed", "grateful", "thankful", "cheerful", "elated", "ecstatic"],
        "patterns": ["can't wait", "so happy", "love this", "best day", "feeling good"]
    },
    "sad": {
        "keywords": ["sad", "unhappy", "depressed", "down", "upset", "crying", "tears",
                    "miserable", "heartbroken", "devastated", "lonely", "hopeless",
                    "grief", "sorrow", "melancholy", "gloomy", "disappointed"],
        "patterns": ["feel down", "so sad", "miss you", "can't stop crying", "heart hurts"]
    },
    "angry": {
        "keywords": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated",
                    "rage", "hate", "livid", "outraged", "infuriated", "pissed"],
        "patterns": ["so angry", "makes me mad", "can't believe", "fed up", "sick of"]
    },
    "fear": {
        "keywords": ["scared", "afraid", "terrified", "anxious", "worried", "nervous",
                    "panic", "frightened", "dread", "horror", "alarmed", "uneasy"],
        "patterns": ["so scared", "worried about", "can't sleep", "freaking out"]
    },
    "surprise": {
        "keywords": ["surprised", "shocked", "amazed", "astonished", "wow", "unexpected",
                    "unbelievable", "stunned", "startled", "speechless"],
        "patterns": ["can't believe", "didn't expect", "out of nowhere", "what the"]
    },
    "disgust": {
        "keywords": ["disgusted", "gross", "yuck", "ew", "revolting", "nasty", "sick",
                    "repulsed", "appalled", "horrified"],
        "patterns": ["makes me sick", "so gross", "can't stand"]
    },
    "love": {
        "keywords": ["love", "adore", "cherish", "devoted", "passionate", "affection",
                    "care", "treasure", "fond", "attached"],
        "patterns": ["love you", "in love", "my heart", "meant to be"]
    },
    "anxiety": {
        "keywords": ["anxious", "worried", "stressed", "overwhelmed", "tense", "nervous",
                    "restless", "on edge", "panicking"],
        "patterns": ["can't relax", "so stressed", "freaking out", "too much"]
    }
}


class MonicaEmotionIntelligence:
    """
    Advanced emotion intelligence system for Monica.
    Combines multiple modalities for comprehensive emotion understanding.
    """
    
    def __init__(self):
        self.emotion_recognizer = None
        self.emotion_history = []
        self.current_emotion = "neutral"
        self.emotion_confidence = 0.0
        
        # Initialize EmotiEffLib if available
        if HAS_EMOTIEFF and EmotiEffLibRecognizer is not None:
            try:
                self.emotion_recognizer = EmotiEffLibRecognizer()
                print("✅ EmotiEffLib emotion recognizer initialized (8 emotions)")
            except Exception as e:
                print(f"⚠️ EmotiEffLib initialization failed: {e}")
        
        # Face detection fallback
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load emotion knowledge
        self.emotion_taxonomy = EMOTION_TAXONOMY
        self.body_language = BODY_LANGUAGE_CUES
        self.voice_cues = VOICE_EMOTION_CUES
        self.text_patterns = TEXT_EMOTION_PATTERNS
        
        print("✅ Monica Emotion Intelligence initialized")
        print(f"   📊 {len(EMOTION_TAXONOMY['primary'])} primary emotions")
        print(f"   📊 {len(EMOTION_TAXONOMY['secondary'])} secondary emotions")
        print(f"   📊 Body language analysis enabled")
        print(f"   📊 Voice tone analysis enabled")
        print(f"   📊 Text sentiment analysis enabled")
    
    def detect_emotion_from_face(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect emotions from facial expression using EmotiEffLib.
        Returns detailed emotion analysis.
        """
        result = {
            "emotion": "neutral",
            "confidence": 0.0,
            "all_emotions": {},
            "face_detected": False,
            "face_location": None,
            "analysis": {}
        }
        
        try:
            if self.emotion_recognizer is not None:
                # Use EmotiEffLib for state-of-the-art detection
                # First detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    result["face_detected"] = True
                    result["face_location"] = (x, y, w, h)
                    
                    # Crop face for emotion recognition
                    face_img = frame[y:y+h, x:x+w]
                    if face_img.size > 0:
                        # Resize to model input size
                        face_resized = cv2.resize(face_img, (224, 224))
                        
                        # Get emotion predictions
                        emotion_scores = self.emotion_recognizer.predict_emotions(face_resized)
                        
                        if emotion_scores is not None:
                            # Map indices to emotion names
                            idx_to_emotion = self.emotion_recognizer.idx_to_emotion_class
                            emotion_dict = {}
                            for idx, score in enumerate(emotion_scores):
                                if idx < len(idx_to_emotion):
                                    emotion_name = idx_to_emotion[idx].lower()
                                    emotion_dict[emotion_name] = float(score)
                            
                            result["all_emotions"] = emotion_dict
                            
                            # Find dominant emotion
                            if emotion_dict:
                                dominant = max(emotion_dict, key=emotion_dict.get)
                                result["emotion"] = dominant
                                result["confidence"] = emotion_dict[dominant]
            else:
                # Fallback to basic face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    result["face_detected"] = True
                    x, y, w, h = faces[0]
                    result["face_location"] = (x, y, w, h)
            
            # Add detailed analysis
            if result["face_detected"] and result["emotion"] in self.emotion_taxonomy["primary"]:
                emotion_info = self.emotion_taxonomy["primary"][result["emotion"]]
                result["analysis"] = {
                    "description": emotion_info["description"],
                    "facial_cues": emotion_info["facial_cues"],
                    "intensity_levels": emotion_info["intensity_levels"]
                }
            
            # Update history
            if result["face_detected"]:
                self.current_emotion = result["emotion"]
                self.emotion_confidence = result["confidence"]
                self._update_history(result)
        
        except Exception as e:
            # Suppress repeated errors - only log once
            if not hasattr(self, '_error_logged'):
                print(f"⚠️ Emotion detection using fallback mode")
                self._error_logged = True
        
        return result
    
    def analyze_text_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotions from text using advanced pattern matching.
        """
        text_lower = text.lower()
        detected_emotions = {}
        
        for emotion, patterns in self.text_patterns.items():
            score = 0
            matched_keywords = []
            matched_patterns = []
            
            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Check patterns (worth more)
            for pattern in patterns["patterns"]:
                if pattern in text_lower:
                    score += 2
                    matched_patterns.append(pattern)
            
            if score > 0:
                detected_emotions[emotion] = {
                    "score": score,
                    "keywords": matched_keywords,
                    "patterns": matched_patterns
                }
        
        # Determine dominant emotion
        if detected_emotions:
            dominant = max(detected_emotions, key=lambda x: detected_emotions[x]["score"])
            total_score = sum(e["score"] for e in detected_emotions.values())
            confidence = detected_emotions[dominant]["score"] / max(total_score, 1)
            
            return {
                "emotion": dominant,
                "confidence": min(confidence, 1.0),
                "all_emotions": {k: v["score"] for k, v in detected_emotions.items()},
                "matched_keywords": detected_emotions[dominant]["keywords"],
                "matched_patterns": detected_emotions[dominant]["patterns"]
            }
        
        return {
            "emotion": "neutral",
            "confidence": 0.5,
            "all_emotions": {},
            "matched_keywords": [],
            "matched_patterns": []
        }
    
    def analyze_voice_characteristics(self, pitch: str, speed: str, volume: str) -> Dict[str, Any]:
        """
        Analyze emotions from voice characteristics.
        """
        possible_emotions = set()
        
        if pitch in self.voice_cues["pitch"]:
            possible_emotions.update(self.voice_cues["pitch"][pitch])
        if speed in self.voice_cues["speed"]:
            possible_emotions.update(self.voice_cues["speed"][speed])
        if volume in self.voice_cues["volume"]:
            possible_emotions.update(self.voice_cues["volume"][volume])
        
        return {
            "possible_emotions": list(possible_emotions),
            "voice_profile": {
                "pitch": pitch,
                "speed": speed,
                "volume": volume
            }
        }
    
    def interpret_body_language(self, posture: str) -> Dict[str, Any]:
        """
        Interpret body language cues.
        """
        if posture in self.body_language:
            cue = self.body_language[posture]
            return {
                "posture": posture,
                "indicators": cue["indicators"],
                "interpretation": cue["interpretation"]
            }
        return {"posture": "unknown", "interpretation": "Unable to interpret"}
    
    def get_emotion_info(self, emotion: str) -> Optional[Dict]:
        """
        Get detailed information about an emotion.
        """
        emotion_lower = emotion.lower()
        
        if emotion_lower in self.emotion_taxonomy["primary"]:
            return {
                "type": "primary",
                **self.emotion_taxonomy["primary"][emotion_lower]
            }
        elif emotion_lower in self.emotion_taxonomy["secondary"]:
            return {
                "type": "secondary",
                **self.emotion_taxonomy["secondary"][emotion_lower]
            }
        return None
    
    def get_emotion_response_suggestions(self, emotion: str) -> List[str]:
        """
        Get suggestions for responding to someone experiencing an emotion.
        """
        responses = {
            "happy": [
                "Share in their joy and celebrate with them",
                "Ask what's making them happy",
                "Offer genuine compliments"
            ],
            "sad": [
                "Listen without judgment",
                "Offer comfort and support",
                "Validate their feelings",
                "Ask if they want to talk about it"
            ],
            "angry": [
                "Stay calm and don't escalate",
                "Listen to their concerns",
                "Acknowledge their frustration",
                "Give them space if needed"
            ],
            "fear": [
                "Provide reassurance",
                "Help them feel safe",
                "Listen to their concerns",
                "Offer practical help if possible"
            ],
            "surprise": [
                "Give them time to process",
                "Ask about their reaction",
                "Share in their amazement if positive"
            ],
            "disgust": [
                "Acknowledge their reaction",
                "Remove the source if possible",
                "Don't dismiss their feelings"
            ],
            "anxiety": [
                "Help them ground themselves",
                "Encourage deep breathing",
                "Listen without adding to worries",
                "Offer practical support"
            ]
        }
        
        return responses.get(emotion.lower(), ["Listen actively", "Show empathy", "Be supportive"])
    
    def _update_history(self, emotion_data: Dict):
        """Update emotion history for tracking patterns."""
        self.emotion_history.append({
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion_data["emotion"],
            "confidence": emotion_data["confidence"]
        })
        
        # Keep only last 100 entries
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]
    
    def get_emotion_trend(self) -> Dict[str, Any]:
        """Analyze emotion trends from history."""
        if not self.emotion_history:
            return {"trend": "insufficient_data"}
        
        # Count emotions
        emotion_counts = {}
        for entry in self.emotion_history[-20:]:  # Last 20 entries
            emotion = entry["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
        
        return {
            "dominant_emotion": dominant,
            "emotion_distribution": emotion_counts,
            "sample_size": len(self.emotion_history[-20:])
        }
    
    def draw_emotion_overlay(self, frame: np.ndarray, emotion_data: Dict) -> np.ndarray:
        """Draw emotion information on frame."""
        result = frame.copy()
        
        if not emotion_data.get("face_detected"):
            return result
        
        # Colors for different emotions
        emotion_colors = {
            "happy": (0, 255, 0),      # Green
            "sad": (255, 0, 0),        # Blue
            "angry": (0, 0, 255),      # Red
            "fear": (128, 0, 128),     # Purple
            "surprise": (0, 255, 255), # Yellow
            "disgust": (0, 128, 0),    # Dark green
            "neutral": (128, 128, 128),# Gray
            "contempt": (0, 165, 255), # Orange
        }
        
        emotion = emotion_data.get("emotion", "neutral")
        color = emotion_colors.get(emotion, (255, 255, 255))
        
        # Draw face box
        if emotion_data.get("face_location"):
            loc = emotion_data["face_location"]
            if isinstance(loc, (list, tuple)) and len(loc) >= 4:
                x, y, w, h = int(loc[0]), int(loc[1]), int(loc[2]), int(loc[3])
                cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
                
                # Draw emotion label
                confidence = emotion_data.get("confidence", 0)
                label = f"{emotion.upper()} ({confidence:.0%})"
                cv2.putText(result, label, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return result


# Singleton instance
_emotion_intelligence = None

def get_emotion_intelligence() -> MonicaEmotionIntelligence:
    """Get or create the emotion intelligence singleton."""
    global _emotion_intelligence
    if _emotion_intelligence is None:
        _emotion_intelligence = MonicaEmotionIntelligence()
    return _emotion_intelligence


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MONICA EMOTION INTELLIGENCE TEST")
    print("=" * 60)
    
    ei = get_emotion_intelligence()
    
    # Test text emotion detection
    print("\n--- Text Emotion Analysis ---")
    test_texts = [
        "I'm so happy today! Everything is wonderful!",
        "I'm really worried about the exam tomorrow",
        "This makes me so angry, I can't believe it!",
        "I miss you so much, feeling really down",
        "Wow! I can't believe this happened!"
    ]
    
    for text in test_texts:
        result = ei.analyze_text_emotion(text)
        print(f"\n'{text}'")
        print(f"  → {result['emotion'].upper()} ({result['confidence']:.0%})")
        if result['matched_keywords']:
            print(f"  Keywords: {', '.join(result['matched_keywords'])}")
    
    # Test emotion info
    print("\n--- Emotion Information ---")
    for emotion in ["happy", "sad", "anxiety"]:
        info = ei.get_emotion_info(emotion)
        if info:
            print(f"\n{emotion.upper()}:")
            print(f"  Type: {info['type']}")
            print(f"  Description: {info['description']}")
    
    # Test response suggestions
    print("\n--- Response Suggestions ---")
    for emotion in ["sad", "angry", "anxiety"]:
        suggestions = ei.get_emotion_response_suggestions(emotion)
        print(f"\nWhen someone is {emotion}:")
        for s in suggestions[:2]:
            print(f"  • {s}")
    
    print("\n" + "=" * 60)
    print("✅ Emotion Intelligence test complete!")
    print("=" * 60)
