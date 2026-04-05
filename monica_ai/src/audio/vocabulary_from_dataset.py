"""
Vocabulary extracted from multiple speech datasets:
- Mozilla Common Voice Spontaneous Speech
- Joe TTS Dataset (en-US) - General, Chat, CustomerService
- Dave TTS Dataset (es-ES) - Spanish support
- jim-schwoebel/voice_datasets
- NVIDIA NeMo

Used to improve Monica's speech recognition accuracy via initial_prompt.
"""
from pathlib import Path

# Common question patterns from the dataset
COMMON_QUESTIONS = [
    "What was your favorite thing in school?",
    "How do you get to the doctor?",
    "Are there local events or festivals your family attend?",
    "How can schools and parents help each other educate children?",
    "Describe some foods that are unhealthy",
    "Can you sing or play music?",
    "What local artist or craftsperson do you admire?",
    "What is a good gift for an adult?",
    "What is your earliest memory?",
    "Describe a visit to a cinema in your country",
    "What games do you like to play?",
    "What equipment is essential for your water sport?",
    "How do you keep warm in winter?",
    "What advice would you give a friend who is nervous?",
    "What is your favorite animal?",
    "What are your thoughts on indoor smoking?",
    "Did you have a favorite toy?",
    "What is a popular local children's book or story?",
    "What is one good quality about yourself?",
    "What music do you like?",
    "What do you think of school tests for young children?",
]

# Common conversational words and phrases from transcriptions
COMMON_WORDS = [
    # Fillers and discourse markers
    "um", "uh", "well", "actually", "basically", "probably", "definitely",
    "I think", "I guess", "I believe", "I mean", "you know",
    
    # User-specific vocabulary - Add your common phrases here
    "launch", "start", "stop", "pause", "resume", "exit", "quit",
    "camera", "video", "audio", "microphone", "sound", "volume",
    "what's", "where's", "how's", "when's", "why's", "who's",
    
    # Common responses
    "yes", "no", "maybe", "of course", "absolutely", "definitely",
    "I don't know", "I'm not sure", "that's right", "exactly",
    
    # Time expressions
    "when I was", "a long time ago", "recently", "nowadays", "these days",
    "back then", "in the past", "in the future",
    
    # Opinions
    "I like", "I love", "I prefer", "I enjoy", "I hate",
    "my favorite", "the best", "the worst",
    
    # Comparisons
    "better than", "worse than", "as good as", "different from",
    
    # Quantities
    "a lot of", "some", "many", "few", "most", "all",
    
    # Places
    "school", "university", "hospital", "cinema", "home", "work",
    "library", "restaurant", "store", "park",
    
    # People
    "friend", "family", "parents", "children", "teacher", "doctor",
    
    # Activities
    "play", "watch", "listen", "read", "write", "study", "work",
    "eat", "drink", "sleep", "walk", "run", "drive",
    
    # Monica-specific
    "Monica", "initialize", "stop", "help", "please", "thank you",
    "what time", "what date", "weather", "remind me",
    
    # From Joe TTS Dataset - General conversation
    "focus", "recipe", "distracted", "therapeutic", "baking",
    "measurements", "summer", "winter", "balcony", "living room",
    "furniture", "books", "couch", "washing machine",
    "church", "cemetery", "newspaper", "monkey", "tree", "river", "lake",
    
    # From Joe TTS Dataset - Chat
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "how are you", "nice to meet you", "goodbye", "see you later",
    "thank you", "you're welcome", "sorry", "excuse me",
    
    # Spanish support (from Dave dataset)
    "hola", "buenos días", "buenas tardes", "buenas noches",
    "gracias", "por favor", "sí", "no", "cómo estás",
]

# Common phrases that appear in spontaneous speech
COMMON_PHRASES = [
    # School/Education
    "high school", "elementary school", "middle school", "university",
    "favorite subject", "homework", "teacher", "classmate",
    
    # Health
    "go to the doctor", "hospital", "checkup", "medicine",
    
    # Food
    "fast food", "healthy food", "unhealthy food", "processed food",
    "saturated fat", "sugar", "salt",
    
    # Entertainment
    "video games", "board games", "card games", "music",
    "guitar", "piano", "sing", "play music",
    "cinema", "movie", "film", "popcorn",
    
    # Weather/Seasons
    "winter", "summer", "spring", "fall", "autumn",
    "keep warm", "stay cool", "jacket", "sweater",
    
    # Family
    "my family", "my parents", "my children", "my friends",
    
    # Emotions
    "happy", "sad", "nervous", "excited", "scared", "angry",
    "take a deep breath", "calm down", "relax",
]

def get_whisper_prompt():
    """
    Generate an initial_prompt for Whisper that includes common vocabulary.
    This helps Whisper recognize these words more accurately.
    """
    # Combine key vocabulary into a prompt
    key_words = [
        # Monica commands
        "Monica", "initialize", "stop", "cancel", "help", "please", "thank you",
        "MJP", "Marvin",
        
        # Common questions
        "What time is it?", "What's the date?", "What's the weather?",
        "How are you?", "Can you help me?",
        
        # Conversational
        "yes", "no", "maybe", "I think", "I don't know",
        "actually", "probably", "definitely", "basically",
        
        # Topics from datasets (Common Voice, Joe, Dave)
        "school", "favorite", "music", "games", "food", "family",
        "doctor", "cinema", "movie", "book", "animal",
        "recipe", "baking", "furniture", "summer", "winter",
        
        # Actions
        "open", "close", "show", "hide", "start", "stop",
        "play", "pause", "next", "previous",
        
        # Greetings (from Joe Chat dataset)
        "hello", "hi", "hey", "good morning", "good afternoon",
        "goodbye", "see you later", "nice to meet you",
        
        # Spanish basics (from Dave dataset)
        "hola", "gracias", "por favor",
    ]
    
    return " ".join(key_words)


def get_transcription_corrections():
    """
    Return common corrections for misheard words.
    Based on patterns observed in the dataset.
    """
    return {
        # Monica variations
        r'\bmonaco\b': 'Monica',
        r'\bmonika\b': 'Monica',
        r'\bmonica\b': 'Monica',
        
        # Common mishearings
        r'\bwanna\b': 'want to',
        r'\bgonna\b': 'going to',
        r'\bgotta\b': 'got to',
        r'\bkinda\b': 'kind of',
        r'\bsorta\b': 'sort of',
        r'\blotta\b': 'lot of',
        
        # Contractions
        r"\bdon't\b": "do not",
        r"\bcan't\b": "cannot",
        r"\bwon't\b": "will not",
        r"\bi'm\b": "I am",
        r"\byou're\b": "you are",
        r"\bthey're\b": "they are",
        r"\bwe're\b": "we are",
        r"\bit's\b": "it is",
        r"\bthat's\b": "that is",
        r"\bwhat's\b": "what is",
    }


# Voice Training Script for Monica AI
# Record your voice to improve speech recognition accuracy

def create_voice_training_script():
    """Create a script to record your voice saying specific phrases"""
    script_content = '''
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from pathlib import Path
import time

class VoiceTrainer:
    def __init__(self):
        self.sample_rate = 16000
        self.output_dir = Path("voice_recordings")
        self.output_dir.mkdir(exist_ok=True)
        
    def record_phrase(self, phrase, filename):
        """Record a single phrase"""
        print(f"\\nRecording: '{phrase}'")
        print("Press ENTER to start recording, speak clearly, then press ENTER again to stop...")
        input()
        
        print("Recording... (speak now)")
        recording = sd.rec(int(5 * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype=np.float32)
        input()  # Wait for user to press Enter to stop
        
        sd.stop()
        
        # Save recording
        filepath = self.output_dir / f"{filename}.wav"
        sf.write(filepath, recording, self.sample_rate)
        print(f"Saved: {filepath}")
        
    def record_training_phrases(self):
        """Record all training phrases - varied, complex, with tongue twisters"""
        phrases = [
            # Wake phrases (just a few)
            "Initialize system",
            "Wake up and start listening",
            "Activate voice recognition now",
            
            # Complex sentences with varied vocabulary
            "The quick brown fox jumps over the lazy dog near the riverbank",
            "She sells seashells by the seashore every single summer",
            "Peter Piper picked a peck of pickled peppers from the garden",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
            "Red lorry yellow lorry red lorry yellow lorry",
            "Unique New York unique New York you know you need unique New York",
            "The sixth sick sheik's sixth sheep's sick",
            "Fuzzy Wuzzy was a bear Fuzzy Wuzzy had no hair",
            
            # Technical and everyday phrases
            "Please open the application settings and configure the audio parameters",
            "Can you search for the nearest coffee shop with good reviews",
            "Set a reminder for tomorrow morning at eight thirty",
            "What is the current temperature and weather forecast for this weekend",
            "Calculate the square root of one thousand twenty four",
            "Send an email to the development team about the project deadline",
            "Schedule a meeting with the marketing department for next Tuesday",
            "Turn off all the lights and activate the security system",
            
            # Natural conversation phrases
            "I was thinking about going to the park later this afternoon",
            "That's an interesting perspective I hadn't considered before",
            "Could you please explain that concept in simpler terms",
            "The documentary I watched last night was absolutely fascinating",
            "I appreciate your help with this complicated situation",
            "Let me know when you're ready to proceed with the next step",
            
            # Questions with complex structure
            "What would be the best approach to solving this particular problem",
            "How long will it take to finish processing the requested information",
            "Where exactly did you put the configuration files we discussed",
            "Why does the system behave differently under heavy load conditions",
            
            # Tongue twisters for articulation training
            "Betty Botter bought some butter but she said the butter's bitter",
            "A proper copper coffee pot produces properly poured coffee",
            "Six slippery snails slid slowly seaward",
            "Irish wristwatch Swiss wristwatch Irish wristwatch",
            "Pad kid poured curd pulled cod",
            "Thirty three thousand feathers on a thrushes throat",
            
            # Numbers and technical terms
            "The meeting is scheduled for December sixteenth twenty twenty five",
            "Transfer approximately three thousand four hundred fifty dollars",
            "The coordinates are forty seven point three by negative one twenty two",
            "Version twelve point three point seven was released yesterday",
            
            # Short confirmations
            "Absolutely",
            "Understood",
            "Go ahead",
            "That's correct",
            "Please continue"
        ]
        
        print("=== Voice Training for Monica AI ===")
        print("This will record your voice to improve speech recognition.")
        print("Please speak clearly and naturally.")
        
        for i, phrase in enumerate(phrases):
            filename = f"phrase_{i:02d}_{phrase.replace(' ', '_').replace('?', '')}"
            self.record_phrase(phrase, filename)
            time.sleep(1)  # Brief pause between recordings
        
        print(f"\\nTraining complete! Recordings saved in: {self.output_dir}")
        print("These recordings will be used to fine-tune Whisper for your voice.")

if __name__ == "__main__":
    trainer = VoiceTrainer()
    trainer.record_training_phrases()
'''
    
    # Write the script
    script_path = Path(__file__).parent.parent.parent / "train_my_voice.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"Created voice training script: {script_path}")
    return script_path

def create_fine_tuning_script():
    """Create a script to fine-tune Whisper with your voice recordings"""
    script_content = '''
import torch
import whisper
import json
import os
from pathlib import Path
from datasets import Dataset
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from torch.utils.data import DataLoader
import soundfile as sf
import numpy as np

class WhisperFineTuner:
    def __init__(self, model_name="openai/whisper-tiny"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load model and processor
        self.processor = WhisperProcessor.from_pretrained(model_name, language="en", task="transcribe")
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
        
        # Training settings
        self.training_args = {
            "output_dir": "./whisper_finetuned",
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 2,
            "learning_rate": 1e-5,
            "warmup_steps": 50,
            "num_train_epochs": 10,
            "save_steps": 100,
            "eval_steps": 100,
            "logging_steps": 10,
            "evaluation_strategy": "steps",
            "save_total_limit": 2,
            "load_best_model_at_end": True,
            "metric_for_best_model": "wer",
            "greater_is_better": False,
            "fp16": True if self.device == "cuda" else False,
        }
        
    def prepare_dataset(self, recordings_dir="voice_recordings"):
        """Prepare dataset from voice recordings"""
        recordings_path = Path(recordings_dir)
        if not recordings_path.exists():
            raise FileNotFoundError(f"Recordings directory not found: {recordings_dir}")
        
        # Load recordings and create dataset
        audio_files = list(recordings_path.glob("*.wav"))
        if not audio_files:
            raise ValueError(f"No WAV files found in {recordings_dir}")
        
        dataset_items = []
        
        for wav_file in audio_files:
            # Load audio
            audio, sr = sf.read(wav_file)
            if sr != 16000:
                # Resample if needed
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            
            # Extract phrase from filename
            phrase = wav_file.stem.replace("_", " ").split(" ", 2)[-1]
            phrase = phrase.replace("phrase", "").strip()
            
            dataset_items.append({
                "audio": {"array": audio, "sampling_rate": 16000},
                "sentence": phrase,
                "file": str(wav_file)
            })
        
        # Create dataset
        dataset = Dataset.from_list(dataset_items)
        
        # Split dataset
        train_test_split = dataset.train_test_split(test_size=0.2, seed=42)
        return train_test_split["train"], train_test_split["test"]
    
    def prepare_data(self, dataset):
        """Prepare data for training"""
        def prepare_dataset(batch):
            # Process audio
            audio = batch["audio"]
            batch["input_features"] = self.processor(
                audio["array"], 
                sampling_rate=audio["sampling_rate"], 
                return_tensors="pt"
            ).input_features[0]
            
            # Process text
            batch["labels"] = self.processor(
                text=batch["sentence"], 
                return_tensors="pt"
            ).input_ids[0]
            
            return batch
        
        return dataset.map(
            prepare_dataset,
            remove_columns=dataset.column_names,
            num_proc=1
        )
    
    def compute_metrics(self, pred):
        """Compute WER (Word Error Rate) metric"""
        import jiwer
        
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        
        # Replace -100 with pad_token_id
        label_ids[label_ids == -100] = self.processor.tokenizer.pad_token_id
        
        # Decode predictions and labels
        pred_str = self.processor.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = self.processor.batch_decode(label_ids, skip_special_tokens=True)
        
        # Compute WER
        wer = jiwer.wer(label_str, pred_str)
        
        return {"wer": wer}
    
    def fine_tune(self, recordings_dir="voice_recordings"):
        """Fine-tune Whisper on your voice recordings"""
        print("=== Whisper Fine-Tuning ===")
        print("This will create a personalized Whisper model for your voice.")
        
        # Prepare dataset
        train_dataset, eval_dataset = self.prepare_dataset(recordings_dir)
        
        # Prepare data
        train_dataset = self.prepare_data(train_dataset)
        eval_dataset = self.prepare_data(eval_dataset)
        
        # Create data collator
        data_collator = lambda features: {
            "input_features": torch.stack([torch.tensor(f["input_features"]) for f in features]),
            "labels": torch.stack([torch.tensor(f["labels"]) for f in features])
        }
        
        # Create trainer
        from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments
        
        training_args = Seq2SeqTrainingArguments(**self.training_args)
        
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            tokenizer=self.processor.feature_extractor,
        )
        
        # Start training
        print("\\nStarting fine-tuning...")
        trainer.train()
        
        # Save model
        trainer.save_model("./whisper_finetuned/final_model")
        self.processor.save_pretrained("./whisper_finetuned/final_model")
        
        print("\\nFine-tuning complete!")
        print("Model saved to: ./whisper_finetuned/final_model")
        print("You can now use this model in Monica for better speech recognition.")
        
        return "./whisper_finetuned/final_model"

if __name__ == "__main__":
    # Install required packages first
    print("Installing required packages...")
    os.system("pip install torch datasets transformers soundfile librosa jiwer")
    
    tuner = WhisperFineTuner()
    model_path = tuner.fine_tune()
    
    print(f"\\nTo use your fine-tuned model in Monica:")
    print(f"1. Copy {model_path} to monica_ai/models/whisper/whisper_finetuned")
    print(f"2. Update config.json to use 'whisper_finetuned' as the model")
    print(f"3. Restart Monica")
'''
    
    # Write the script
    script_path = Path(__file__).parent.parent.parent / "fine_tune_whisper.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"Created Whisper fine-tuning script: {script_path}")
    return script_path

# Auto-create scripts when imported
if __name__ != "__main__":
    try:
        create_voice_training_script()
        create_fine_tuning_script()
    except Exception as e:
        print(f"Error creating training scripts: {e}")

# Export the prompt for use in faster_speech_recognition.py
WHISPER_INITIAL_PROMPT = get_whisper_prompt()
