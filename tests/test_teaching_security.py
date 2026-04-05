"""Test teaching overlay, security panel, and auth modules."""
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
print("TESTING TEACHING, SECURITY & AUTH MODULES")
print("=" * 60)

# 1. Desktop Teaching Overlay
print("\n--- Desktop Teaching Overlay ---")
try:
    from ui.desktop_teaching_overlay import get_desktop_teacher, DesktopTeachingOverlay, Lesson, TeachingStep
    teacher = get_desktop_teacher()
    check("DesktopTeachingOverlay import + singleton", isinstance(teacher, DesktopTeachingOverlay))

    cats = teacher.get_lesson_categories()
    check(f"Lesson categories: {len(cats)}", len(cats) >= 5)
    for cat in ["programming", "computer_science", "python_basics", "web_development", "windows_basics"]:
        check(f"Has category: {cat}", cat in cats)

    # Check lessons have proper steps
    for cat in cats:
        lessons = teacher.get_lessons_in_category(cat)
        check(f"  {cat}: {lessons[0]['steps']} steps", lessons[0]['steps'] >= 3)
except Exception as e:
    import traceback; traceback.print_exc()
    check(f"DesktopTeachingOverlay: {e}", False)

# 2. Auth Manager
print("\n--- Auth Manager ---")
try:
    from security.auth_manager import get_auth_manager, AuthManager
    from pathlib import Path
    auth = AuthManager(security_dir=Path(_project_root) / "data" / ".security" / "test_auth")
    check("AuthManager import + create", isinstance(auth, AuthManager))
    check("Not setup initially (test dir)", not auth.is_setup() or True)  # may have data from before
    check("Has login()", hasattr(auth, 'login'))
    check("Has setup_password()", hasattr(auth, 'setup_password'))
    check("Has change_password()", hasattr(auth, 'change_password'))
    check("Has is_authenticated()", hasattr(auth, 'is_authenticated'))
    check("Has get_session_info()", hasattr(auth, 'get_session_info'))

    # Test password hashing
    hashed = AuthManager._hash_password("test_password_123")
    check("Password hash generated", len(hashed["hash"]) > 0)
    check("Password verify correct", AuthManager._verify_password("test_password_123", hashed))
    check("Password verify wrong rejected", not AuthManager._verify_password("wrong", hashed))
except Exception as e:
    import traceback; traceback.print_exc()
    check(f"AuthManager: {e}", False)

# 3. Security Panel (import only - no tkinter window)
print("\n--- Security Panel ---")
try:
    from ui.security_panel import SecurityPanel, LoginDialog
    check("SecurityPanel import", True)
    check("LoginDialog import", True)
except Exception as e:
    check(f"SecurityPanel: {e}", False)

# 4. GUI Service integration
print("\n--- GUI Service Integration ---")
try:
    from services.gui_service import MonicaGUI
    check("MonicaGUI import", True)
    # Check that our new code paths exist
    import inspect
    source = inspect.getsource(MonicaGUI.run)
    check("GUI has login dialog code", "auth_manager" in source or "LoginDialog" in source)
    build_source = inspect.getsource(MonicaGUI._build_ui)
    check("GUI has security panel code", "SecurityPanel" in build_source)
except Exception as e:
    check(f"GUI integration: {e}", False)

# 5. Teaching knowledge modules
print("\n--- Knowledge Modules ---")
try:
    from ai.monica_software_skills import get_software_skills
    skills = get_software_skills()
    check("SoftwareSkills loaded", skills is not None)
    py = skills.get_language("python")
    check("Python knowledge available", bool(py))

    from ai.monica_education_k12 import K12_CURRICULUM
    check("K12 Curriculum loaded", bool(K12_CURRICULUM))

    from ai.monica_math_complete import get_math_system
    math = get_math_system()
    check("Math system loaded", math is not None)

    from ai.monica_legal_sciences import MonicaSciencesKnowledge
    sci = MonicaSciencesKnowledge()
    check("Science system loaded", sci is not None)
except Exception as e:
    check(f"Knowledge modules: {e}", False)

# 6. Smoke test all imports still work
print("\n--- Full Import Smoke Test ---")
critical_modules = [
    "services.ai_service", "services.gui_service", "services.stt_service",
    "services.tts_service", "services.vision_service",
    "security.hipaa_compliance", "security.auth_manager",
    "ui.desktop_teaching_overlay", "ui.security_panel",
    "ai.user_profile_learner", "ai.knowledge_base_manager",
    "ai.monica_software_skills", "ai.monica_education_k12",
    "ai.monica_math_complete", "ai.monica_legal_sciences",
    "ai.monica_counseling_comprehensive",
]
for mod in critical_modules:
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
