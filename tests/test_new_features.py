"""
Comprehensive test for all new features:
1. Desktop shortcut
2. Intent anticipation in AI
3. Biometrics: head count, finger count, thermal estimation
4. Knowledge Base auto-watcher
5. Stop/resume system
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

passed = 0
failed = 0

def check(label, cond):
    global passed, failed
    if cond:
        print(f'  [OK] {label}')
        passed += 1
    else:
        print(f'  [FAIL] {label}')
        failed += 1

print('=' * 65)
print('  NEW FEATURES COMPREHENSIVE TEST')
print('=' * 65)

# === 1. Desktop Shortcut ===
print('\n--- Desktop Shortcut ---')
desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
shortcut_lnk = os.path.join(desktop, 'Monica AI.lnk')
shortcut_bat = os.path.join(desktop, 'Launch Monica AI.bat')
bat = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Launch_Monica.bat')
check('Launch_Monica.bat exists', os.path.exists(bat))
check('Desktop shortcut exists', os.path.exists(shortcut_lnk) or os.path.exists(shortcut_bat))

# === 2. Intent Anticipation ===
print('\n--- Intent Anticipation (AI Prompt) ---')
from services.ai_service import AIService
# Check source code has anticipation rules
import inspect
source = inspect.getsource(AIService._process_request)
check('AI prompt has INTENT ANTICIPATION', 'INTENT ANTICIPATION' in source)
check('AI prompt mentions incomplete speech', 'incomplete' in source.lower() or 'garbled' in source.lower())
check('AI prompt mentions predict/anticipate', 'anticipate' in source.lower() or 'predict' in source.lower())
check('AI prompt resolves ambiguity', 'ambiguous' in source.lower() or 'that thing' in source)
check('AI uses knowledge_watcher context', 'knowledge_watcher' in source)

# === 3. Biometrics ===
print('\n--- Biometric Detectors ---')
from biometric.biometric_detector import (
    BiometricDetector, HeadCountDetector, FingerCountDetector, ThermalEstimator,
    HeadCountResult, FingerCountResult, ThermalEstimationResult,
    EmotionDetector, AgeDetector, HeartbeatDetector
)

# Head Count
hcd = HeadCountDetector()
check('HeadCountDetector created', hcd is not None)
check('HeadCountDetector has detect()', hasattr(hcd, 'detect'))
check('HeadCountDetector has face_cascade', hcd.face_cascade is not None)
# Test with blank frame
blank = np.zeros((480, 640, 3), dtype=np.uint8)
result = hcd.detect(blank)
check('HeadCountDetector returns result on blank frame', result is not None)
check('HeadCountDetector: 0 heads in blank frame', result.count == 0 if result else False)

# Finger Count
fcd = FingerCountDetector()
check('FingerCountDetector created', fcd is not None)
check('FingerCountDetector has detect()', hasattr(fcd, 'detect'))
check('FingerCountDetector has _detect_convex_hull fallback', hasattr(fcd, '_detect_convex_hull'))

# Thermal
thermal = ThermalEstimator()
check('ThermalEstimator created', thermal is not None)
check('ThermalEstimator has estimate()', hasattr(thermal, 'estimate'))
check('ThermalEstimator has calibration params', hasattr(thermal, '_rg_ratio_min'))
check('ThermalEstimator baseline ratio ~1.05', abs(thermal._baseline_ratio - 1.05) < 0.01)
result = thermal.estimate(blank)
check('ThermalEstimator returns result on blank frame', result is not None)

# Full BiometricDetector integration
bd = BiometricDetector(owner_name="MJP")
check('BiometricDetector has head_count_detector', hasattr(bd, 'head_count_detector'))
check('BiometricDetector has finger_count_detector', hasattr(bd, 'finger_count_detector'))
check('BiometricDetector has thermal_estimator', hasattr(bd, 'thermal_estimator'))
check('BiometricDetector has current_head_count', hasattr(bd, 'current_head_count'))
check('BiometricDetector has current_finger_count', hasattr(bd, 'current_finger_count'))
check('BiometricDetector has current_thermal', hasattr(bd, 'current_thermal'))

# get_status includes new biometrics
status = bd.get_status()
check('get_status() has head_count key', 'head_count' in status)
check('get_status() has fingers key', 'fingers' in status)
check('get_status() has thermal key', 'thermal' in status)
check('get_status() has emotion key', 'emotion' in status)
check('get_status() has heartbeat key', 'heartbeat' in status)
check('get_status() has age key', 'age' in status)
check('get_status() has identity key', 'identity' in status)

# === 4. Knowledge Base Watcher ===
print('\n--- Knowledge Base Auto-Watcher ---')
from ai.knowledge_watcher import (
    KnowledgeWatcher, ChunkIndexer, TextExtractor, PDFTextExtractor,
    get_knowledge_watcher, DocumentChunk, IndexedDocument
)

# TextExtractor
ext = TextExtractor()
check('TextExtractor created', ext is not None)
check('TextExtractor has pdf_extractor', ext.pdf_extractor is not None)

# ChunkIndexer
import tempfile
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
indexer = ChunkIndexer(tmp / 'test_index')
check('ChunkIndexer created', indexer is not None)
check('ChunkIndexer has chunks list', isinstance(indexer.chunks, list))
check('ChunkIndexer has manifest', isinstance(indexer.manifest, dict))

# Test chunking
chunks = indexer._chunk_text("A" * 1200, chunk_size=500, overlap=50)
check(f'Chunking 1200 chars -> {len(chunks)} chunks', len(chunks) >= 2)

# Test add_document
pages = [{"page": 1, "text": "Machine learning is a subset of artificial intelligence."},
         {"page": 2, "text": "Neural networks consist of layers of interconnected nodes."}]
count = indexer.add_document("/test/doc.pdf", pages, "abc123")
check(f'add_document returned {count} chunks', count >= 2)
check('Manifest updated', '/test/doc.pdf' in indexer.manifest)

# Test search
results = indexer.search("neural networks", top_k=3)
check('Keyword search returns results', len(results) > 0)
check('Search result has score', 'score' in results[0] if results else False)

# Test remove
indexer.remove_document("/test/doc.pdf")
check('remove_document clears chunks', len(indexer.chunks) == 0)
check('remove_document clears manifest', '/test/doc.pdf' not in indexer.manifest)

# KnowledgeWatcher
watcher = KnowledgeWatcher(base_dir=tmp)
check('KnowledgeWatcher created', watcher is not None)
check('KnowledgeWatcher has watch_dirs', len(watcher.watch_dirs) > 0)
check('KnowledgeWatcher has extractor', watcher.extractor is not None)
check('KnowledgeWatcher has indexer', watcher.indexer is not None)
check('KnowledgeWatcher has start()', hasattr(watcher, 'start'))
check('KnowledgeWatcher has stop()', hasattr(watcher, 'stop'))
check('KnowledgeWatcher has force_reindex()', hasattr(watcher, 'force_reindex'))
check('KnowledgeWatcher has search()', hasattr(watcher, 'search'))
check('KnowledgeWatcher has get_context()', hasattr(watcher, 'get_context'))
check('KnowledgeWatcher has get_stats()', hasattr(watcher, 'get_stats'))

# Test: drop a text file and verify it gets indexed
test_file = watcher.watch_dirs[0] / "test_article.txt"
test_file.parent.mkdir(parents=True, exist_ok=True)
test_file.write_text("Quantum computing uses qubits for parallel computation.", encoding='utf-8')
watcher._scan_all()
stats = watcher.get_stats()
check(f'Auto-indexed test file ({stats["total_documents"]} docs)', stats['total_documents'] >= 1)
check(f'Chunks created ({stats["total_chunks"]})', stats['total_chunks'] >= 1)

# Search for the content we just added
results = watcher.search("quantum computing")
check('Search finds auto-indexed content', len(results) > 0)

context = watcher.get_context("quantum computing")
check('get_context returns formatted text', '[KNOWLEDGE_BASE]' in context if context else False)

# Cleanup
test_file.unlink()

# === 5. Stop/Resume Verification ===
print('\n--- Stop/Resume System ---')
from services.interrupt_manager import InterruptManager
import threading as _th

im = InterruptManager.__new__(InterruptManager)
im.orchestrator = None
im._suppression_list = {}
im._interrupted_task = None
im._interrupt_history = []
im._lock = _th.Lock()
im._last_interrupt_time = 0
im.interrupt_cooldown = 0.5
im._interrupt_active = False
im._on_interrupt_callbacks = []
im._on_resume_callbacks = []
im._data_dir = tmp
im._command_patterns = {
    'stop': ['stop', 'quiet', 'shut up', 'be quiet', 'enough', 'halt', 'pause'],
    'resume': ['continue', 'resume', 'go on', 'keep going', 'carry on'],
}

action = im.check_user_command("stop")
check('Stop command detected', action == 'stopped')

from services.interrupt_manager import InterruptedTask
im._interrupted_task = InterruptedTask(task_type='speaking', content='test full text', progress='test', remaining='full text')
import time as _time; _time.sleep(0.6)  # wait past cooldown
action = im.check_user_command("continue")
check('Resume command detected', action == 'resumed')

_time.sleep(0.6)
action = im.check_user_command("stop repeating yourself")
check('Suppression command detected', action is not None and 'suppressed' in str(action))

check('Suppression list populated', len(im._suppression_list) > 0)

# Summary
print()
print('=' * 65)
print(f'Results: {passed} passed, {failed} failed out of {passed + failed} checks')
print('=' * 65)
if failed == 0:
    print('ALL CHECKS PASSED!')
else:
    print(f'{failed} check(s) need attention.')
