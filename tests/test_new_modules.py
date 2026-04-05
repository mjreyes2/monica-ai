"""Test all newly created modules."""
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
print("TESTING NEW MODULES")
print("=" * 60)

# 1. User Profile Learner
print("\n--- User Profile Learner ---")
try:
    from ai.user_profile_learner import get_user_profile_learner, UserProfileLearner
    upl = get_user_profile_learner()
    check("UserProfileLearner import + singleton", isinstance(upl, UserProfileLearner))
    check("Has learn_from_message()", hasattr(upl, 'learn_from_message'))
    check("Has get_context_for_prompt()", hasattr(upl, 'get_context_for_prompt'))
    check("Has update_from_vision()", hasattr(upl, 'update_from_vision'))
    check("Profile dir exists", upl.profile_dir.exists())

    # Test learning
    upl.learn_from_message("My name is Marvin and I love coding")
    check("Learned name", upl.profile.get("identity", {}).get("name") is not None)
    check("Learned preference", len(upl.profile.get("preferences", {}).get("likes", [])) > 0)
    upl.save()
    check("Save succeeded", upl.profile_file.exists())
except Exception as e:
    check(f"UserProfileLearner: {e}", False)

# 2. HIPAA Compliance
print("\n--- HIPAA Compliance ---")
try:
    from security.hipaa_compliance import get_hipaa_compliance, HIPAACompliance
    h = get_hipaa_compliance()
    check("HIPAACompliance import + singleton", isinstance(h, HIPAACompliance))
    check("Has audit logger", h.audit is not None)
    check("Has encryption manager", h.encryption is not None)
    check("Has integrity checker", h.integrity is not None)

    # Test encryption round-trip
    test_data = {"secret": "HIPAA test data", "phi": True}
    encrypted = h.encryption.encrypt_json(test_data)
    check("Encryption produces output", len(encrypted) > 0)
    decrypted = h.encryption.decrypt_json(encrypted)
    check("Decryption matches original", decrypted == test_data)

    # Test secure save/load
    from pathlib import Path
    test_path = h.security_dir / "test_secure.json"
    saved = h.secure_save(test_data, test_path)
    check("Secure save succeeded", saved)
    loaded = h.secure_load(test_path)
    check("Secure load matches", loaded == test_data)

    # Test integrity
    checksum = h.integrity.compute_checksum("test data")
    check("Integrity checksum", h.integrity.verify_checksum("test data", checksum))

    # Compliance report
    report = h.get_compliance_report()
    check("Compliance report generated", report.get("audit_logging") is True)

    # Cleanup
    if test_path.exists():
        test_path.unlink()
except Exception as e:
    import traceback
    traceback.print_exc()
    check(f"HIPAACompliance: {e}", False)

# 3. Knowledge Base Manager
print("\n--- Knowledge Base Manager ---")
try:
    from ai.knowledge_base_manager import get_knowledge_base_manager, KnowledgeBaseManager
    kb = get_knowledge_base_manager()
    check("KnowledgeBaseManager import + singleton", isinstance(kb, KnowledgeBaseManager))

    domains = kb.list_knowledge_domains()
    check(f"Domains found: {len(domains)}", len(domains) > 0)

    counts = kb.count_resources()
    check(f"PDF files: {counts.get('pdf_files', 0)}", counts.get('pdf_files', 0) > 0)

    books_dir = kb.get_books_pdf_dir()
    check("Textbooks dir found", books_dir is not None)
except Exception as e:
    check(f"KnowledgeBaseManager: {e}", False)

# 4. Enhanced Free APIs
print("\n--- Enhanced Free APIs ---")
try:
    from utils.free_apis import get_free_apis, FreeAPIs
    fa = get_free_apis()
    check("FreeAPIs import + singleton", isinstance(fa, FreeAPIs))

    api_methods = [m for m in dir(fa) if m.startswith('get_') or m in ('search_wikipedia', 'define_word', 'search_books', 'instant_answer', 'search')]
    check(f"API methods count: {len(api_methods)}", len(api_methods) >= 15)

    # Check key methods exist
    for method in ['get_weather', 'search_wikipedia', 'define_word', 'get_nasa_apod',
                   'get_joke', 'get_world_time', 'get_exchange_rate', 'get_trivia',
                   'search_books', 'instant_answer', 'get_earthquakes', 'get_country_info',
                   'get_advice', 'get_quote', 'get_iss_location', 'get_people_in_space']:
        check(f"Has {method}()", hasattr(fa, method))
except Exception as e:
    check(f"FreeAPIs: {e}", False)

# 5. AI Service wiring
print("\n--- AI Service Integration ---")
try:
    from services.ai_service import AIService
    ai = AIService(orchestrator=None)
    check("AIService has user_profile_learner attr", hasattr(ai, 'user_profile_learner'))
    check("AIService has hipaa attr", hasattr(ai, 'hipaa'))
except Exception as e:
    check(f"AIService: {e}", False)

# 6. PDF Retriever auto-path
print("\n--- PDF Retriever ---")
try:
    from ai.pdf_retriever import PDFRetriever
    pr = PDFRetriever()
    check("PDFRetriever created", pr is not None)
    check(f"Index dir: {pr.index_dir.name}", "books_pdf" in str(pr.index_dir))
    check("Source root set to Textbooks", pr.source_root is not None and "Textbooks" in str(pr.source_root))
except Exception as e:
    check(f"PDFRetriever: {e}", False)

# Summary
print()
print("=" * 60)
total = passed + failed
print(f"Results: {passed} passed, {failed} failed out of {total} checks")
print("=" * 60)
if __name__ == '__main__':
    sys.exit(1 if failed > 0 else 0)
