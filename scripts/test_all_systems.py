"""Comprehensive test of all Monica systems - knowledge bases, STT, TTS, new features."""
import sys
import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_script_dir, '..')
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)
os.chdir(_project_root)

ok = 0
fail = 0

def check(name, func):
    global ok, fail
    try:
        result = func()
        print(f"  [OK] {name}: {result}")
        ok += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        fail += 1

print("=" * 60)
print("MONICA AI - COMPREHENSIVE SYSTEM TEST")
print("=" * 60)

# ===== KNOWLEDGE BASES =====
print("\n--- KNOWLEDGE BASE MODULES ---")

check("University Teaching", lambda: (
    __import__('ai.monica_university', fromlist=['get_university', 'SUBJECTS']),
    f"{len(__import__('ai.monica_university', fromlist=['SUBJECTS']).SUBJECTS)} subjects"
)[1])

check("Subjects Part D (Pedagogy/Speaking/Interviewing)", lambda: (
    __import__('ai.monica_university_subjects_d', fromlist=['SUBJECTS_D']),
    f"{len(__import__('ai.monica_university_subjects_d', fromlist=['SUBJECTS_D']).SUBJECTS_D)} subjects"
)[1])

check("Knowledge Learner", lambda: (
    __import__('ai.monica_knowledge_learner', fromlist=['get_knowledge_learner']),
    "loaded"
)[1])

check("Knowledge Watcher", lambda: (
    __import__('ai.knowledge_watcher', fromlist=['get_knowledge_watcher']),
    "loaded"
)[1])

check("Knowledge Base Manager", lambda: (
    __import__('ai.knowledge_base_manager', fromlist=['get_knowledge_base_manager']),
    "loaded"
)[1])

check("Knowledge Connector", lambda: (
    __import__('ai.knowledge_connector', fromlist=['get_knowledge_connector']),
    "loaded"
)[1])

check("PDF Retriever", lambda: (
    __import__('ai.pdf_retriever', fromlist=['PDFRetriever']),
    "loaded"
)[1])

check("User Profile Learner", lambda: (
    __import__('ai.user_profile_learner', fromlist=['get_user_profile_learner']),
    "loaded"
)[1])

check("English Teacher", lambda: (
    __import__('ai.monica_english_teacher', fromlist=['get_english_teacher']),
    "loaded"
)[1])

check("World Teacher", lambda: (
    __import__('ai.monica_world_teacher', fromlist=['get_world_teacher']),
    "loaded"
)[1])

check("Creative Arts", lambda: (
    __import__('ai.monica_creative_arts', fromlist=['get_creative_arts']),
    "loaded"
)[1])

check("Session Memory", lambda: (
    __import__('ai.session_memory', fromlist=['get_session_memory']),
    "loaded"
)[1])

check("Education K-12", lambda: (
    __import__('ai.monica_education_k12', fromlist=['K12_CURRICULUM']),
    "loaded"
)[1])

check("Math Complete", lambda: (
    __import__('ai.monica_math_complete', fromlist=['MATHEMATICS_KNOWLEDGE']),
    "loaded"
)[1])

check("Counseling", lambda: (
    __import__('ai.monica_counseling_comprehensive', fromlist=['COUNSELING_MODALITIES']),
    "loaded"
)[1])

check("Software Skills", lambda: (
    __import__('ai.monica_software_skills', fromlist=['ADOBE_KNOWLEDGE']),
    "loaded"
)[1])

check("Medical Knowledge", lambda: (
    __import__('ai.monica_medical_knowledge', fromlist=['MEDICAL_KNOWLEDGE']),
    "loaded"
)[1])

# ===== UNIVERSITY DETAILS =====
print("\n--- UNIVERSITY SUBJECTS ---")
from ai.monica_university import get_university, SUBJECTS
u = get_university()
total_topics = sum(len(s.get('topics', {})) for s in SUBJECTS.values())
total_quiz = sum(len(s.get('quiz_questions', [])) for s in SUBJECTS.values())
print(f"  Subjects: {len(SUBJECTS)}")
print(f"  Topics: {total_topics}")
print(f"  Quiz questions: {total_quiz}")
for key in sorted(SUBJECTS.keys()):
    name = SUBJECTS[key].get('name', key)
    topics = len(SUBJECTS[key].get('topics', {}))
    quizzes = len(SUBJECTS[key].get('quiz_questions', []))
    print(f"    - {name}: {topics} topics, {quizzes} quizzes")

# ===== USER PROFILE =====
print("\n--- USER PROFILE ---")
from ai.user_profile_learner import get_user_profile_learner
upl = get_user_profile_learner()
health = upl.profile.get('health', {})
print(f"  Conditions: {health.get('conditions', [])}")
print(f"  Learning style: {health.get('learning_style', 'not set')[:80]}...")
ctx = upl.get_context_for_prompt()
has_health = 'ADHD' in ctx if ctx else False
print(f"  Health in prompt context: {has_health}")

# ===== KNOWLEDGE LEARNER =====
print("\n--- KNOWLEDGE LEARNER ---")
from ai.monica_knowledge_learner import get_knowledge_learner
kl = get_knowledge_learner()
stats = kl.get_stats()
print(f"  Entries: {stats['total_entries']}")
print(f"  URLs read: {stats['urls_read']}")
print(f"  Spoken facts: {stats['spoken_facts']}")
print(f"  Total chunks: {stats['total_chunks']}")

# ===== STT =====
print("\n--- STT ENGINE ---")
check("Whisper import", lambda: (
    __import__('whisper'),
    f"v{__import__('whisper').__version__}"
)[1])

check("PyAudio", lambda: (
    __import__('pyaudio'),
    "loaded"
)[1])

check("speech_recognition", lambda: (
    __import__('speech_recognition'),
    f"v{__import__('speech_recognition').__version__}"
)[1])

check("STT Service import", lambda: (
    __import__('services.stt_service', fromlist=['STTService']),
    "loaded"
)[1])

# ===== TTS =====
print("\n--- TTS ENGINE ---")
from pathlib import Path
piper_exe = Path(r"C:\Users\Marvi\AppData\Local\Temp\piper\piper\piper.exe")
check("Piper executable", lambda: f"{'FOUND' if piper_exe.exists() else 'MISSING'}")

voice_dir = Path("monica_ai/resources/voices")
if voice_dir.exists():
    models = list(voice_dir.rglob("*.onnx"))
    check("Voice models", lambda: f"{len(models)} models found")

check("TTS Service import", lambda: (
    __import__('services.tts_service', fromlist=['TTSService']),
    "loaded"
)[1])

# ===== AI SERVICE =====
print("\n--- AI SERVICE ---")
check("AI Service import", lambda: (
    __import__('services.ai_service', fromlist=['AIService']),
    "loaded"
)[1])

# ===== DOWNLOADED TEXTBOOKS =====
print("\n--- DOWNLOADED TEXTBOOKS ---")
tb_dir = Path("data/Monica_Knowledge_Base/Textbooks")
if tb_dir.exists():
    subjects = [d for d in tb_dir.iterdir() if d.is_dir()]
    total_pdfs = sum(len(list(s.glob("*.pdf"))) for s in subjects)
    print(f"  Subjects with textbooks: {len(subjects)}")
    print(f"  Total PDFs: {total_pdfs}")
    for s in sorted(subjects):
        pdfs = list(s.glob("*.pdf"))
        if pdfs:
            print(f"    {s.name}/: {len(pdfs)} PDFs")
else:
    print("  Textbooks directory not found (run download script first)")

# ===== KNOWLEDGE BASE SIZE =====
print("\n--- KNOWLEDGE BASE ---")
kb_dir = Path("data/Monica_Knowledge_Base")
if kb_dir.exists():
    all_pdfs = list(kb_dir.rglob("*.pdf"))
    print(f"  Total PDFs in knowledge base: {len(all_pdfs)}")
    total_size_mb = sum(p.stat().st_size for p in all_pdfs) / (1024*1024)
    print(f"  Total size: {total_size_mb:.0f} MB")

ki_dir = Path("data/knowledge_index")
if ki_dir.exists():
    chunks_file = ki_dir / "chunks.json"
    if chunks_file.exists():
        size_mb = chunks_file.stat().st_size / (1024*1024)
        print(f"  Knowledge index: {size_mb:.1f} MB")

# ===== SUMMARY =====
print("\n" + "=" * 60)
print(f"RESULTS: {ok} OK, {fail} FAIL")
print("=" * 60)
