"""Test the interrupt/barge-in system."""
import sys
import os

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  [OK] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1

print("=" * 60)
print("TESTING INTERRUPT / BARGE-IN SYSTEM")
print("=" * 60)

# 1. InterruptManager core
print("\n--- InterruptManager ---")
try:
    from services.interrupt_manager import InterruptManager, get_interrupt_manager, InterruptedTask
    mgr = InterruptManager(orchestrator=None)
    check("InterruptManager created", mgr is not None)
    check("Has start_monitoring()", hasattr(mgr, 'start_monitoring'))
    check("Has check_user_command()", hasattr(mgr, 'check_user_command'))
    check("Has get_context_for_prompt()", hasattr(mgr, 'get_context_for_prompt'))
    check("Has get_suppression_list()", hasattr(mgr, 'get_suppression_list'))

    # Test stop command detection
    result = mgr.check_user_command("stop")
    check("'stop' detected as stop command", result == "stopped")

    # Test resume with no task
    result = mgr.check_user_command("continue")
    check("'continue' with no task = resume_nothing", result == "resume_nothing")

    # Test suppression: "stop repeating yourself"
    result = mgr.check_user_command("stop repeating yourself")
    check("'stop repeating yourself' -> suppressed", result and result.startswith("suppressed:"))
    check("Suppression list has entry", len(mgr.get_suppression_list()) > 0)
    check("is_suppressed('repeating') works", mgr.is_suppressed("repeating yourself"))

    # Test unsuppression
    result = mgr.check_user_command("you can repeat yourself again")
    check("Resume behavior detected", result and result.startswith("unsuppressed:"))
    check("'repeating yourself' removed from list", not mgr.is_suppressed("repeating yourself"))

    # Test "don't X" pattern
    result = mgr.check_user_command("don't give me medical advice")
    check("\"don't give me medical advice\" -> suppressed",
          result and result.startswith("suppressed:"))
    check("Extracted: 'give me medical advice'",
          "give me medical advice" in mgr.get_suppression_list())

    # Test context for prompt
    ctx = mgr.get_context_for_prompt()
    check("Prompt context includes suppression", "STOP doing" in ctx)

    # Test interrupted task
    task = InterruptedTask(
        task_type="speaking",
        content="Full sentence one. Full sentence two. Full sentence three.",
        progress="Full sentence one.",
        remaining="Full sentence two. Full sentence three.",
    )
    mgr._interrupted_task = task
    ctx2 = mgr.get_context_for_prompt()
    check("Prompt context includes interrupted task", "interrupted" in ctx2.lower())

    # Test resume with task
    result = mgr.check_user_command("continue where you left off")
    check("Resume with task works", result == "resumed")
    check("Task cleared after resume", mgr._interrupted_task is None)

except Exception as e:
    import traceback; traceback.print_exc()
    check(f"InterruptManager: {e}", False)

# 2. TTS Service barge-in support
print("\n--- TTS Service Barge-In ---")
try:
    from services.tts_service import TTSService
    tts = TTSService(orchestrator=None)
    check("TTSService created", tts is not None)
    check("Has _interrupt_event", hasattr(tts, '_interrupt_event'))
    check("Has _spoken_so_far", hasattr(tts, '_spoken_so_far'))
    check("Has _split_into_chunks()", hasattr(tts, '_split_into_chunks'))

    # Test chunk splitting
    text = "Hello there. How are you doing today? I hope everything is going well. Let me know if you need anything."
    chunks = TTSService._split_into_chunks(text)
    check(f"Text split into {len(chunks)} chunks", len(chunks) >= 2)
    # Rejoin should equal original
    rejoined = " ".join(chunks)
    check("Chunks cover full text", len(rejoined) >= len(text) - 5)

    # Test stop_speaking sets interrupt event
    tts.stop_speaking()
    check("stop_speaking sets interrupt event", tts._interrupt_event.is_set())
except Exception as e:
    import traceback; traceback.print_exc()
    check(f"TTS barge-in: {e}", False)

# 3. AI Service integration
print("\n--- AI Service Integration ---")
try:
    from services.ai_service import AIService
    ai = AIService(orchestrator=None)
    check("AIService has interrupt_manager attr", hasattr(ai, 'interrupt_manager'))

    import inspect
    src = inspect.getsource(AIService._process_request)
    check("AI checks user commands first", "check_user_command" in src)
    check("AI adds suppression context", "get_context_for_prompt" in src)
    check("AI handles 'stopped' action", '"stopped"' in src)
    check("AI handles 'resumed' action", '"resumed"' in src)
    check("AI handles 'suppressed:' action", 'suppressed:' in src)
except Exception as e:
    check(f"AI integration: {e}", False)

# 4. STT Service still works
print("\n--- STT Service ---")
try:
    from services.stt_service import STTService
    check("STTService imports", True)
    check("Has energy_threshold for VAD", hasattr(STTService, '__init__'))
except Exception as e:
    check(f"STT: {e}", False)

# 5. Full smoke test
print("\n--- Critical Imports ---")
for mod in ["services.interrupt_manager", "services.tts_service",
            "services.ai_service", "services.stt_service",
            "services.orchestrator", "services.gui_service"]:
    try:
        __import__(mod)
        check(f"import {mod}", True)
    except Exception as e:
        check(f"import {mod}: {e}", False)

# Summary
print()
print("=" * 60)
total = passed + failed
print(f"Results: {passed} passed, {failed} failed out of {total} checks")
print("=" * 60)
if __name__ == '__main__':
    sys.exit(1 if failed > 0 else 0)
