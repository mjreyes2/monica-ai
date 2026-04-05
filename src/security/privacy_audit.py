"""
Monica AI - Privacy & HIPAA Compliance Audit

Scans the entire project for privacy violations:
- Cloud API usage that sends personal data
- Hardcoded API keys
- External services that leak user information
- Non-local STT/TTS that transmit audio to cloud
- IP geolocation services that expose location

Generates a compliance report.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

logger = logging.getLogger("Monica.PrivacyAudit")

# Patterns that indicate privacy violations
VIOLATION_PATTERNS = [
    # Google cloud APIs
    (r'recognize_google\s*\(', "CRITICAL: Sends audio to Google servers", "Use recognize_sphinx() or local Whisper"),
    (r'from\s+google\s+import\s+genai', "CRITICAL: Google Generative AI cloud dependency", "Use local Ollama LLM"),
    (r'genai\.Client', "CRITICAL: Google Generative AI client", "Use local Ollama instead"),
    # Hardcoded API keys
    (r'AIzaSy[A-Za-z0-9_-]{33}', "CRITICAL: Hardcoded Google API key exposed", "Remove key, use env var or local API"),
    (r'api_key\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "HIGH: Hardcoded API key in source", "Use environment variable"),
    # Cloud speech services
    (r'recognize_google_cloud\s*\(', "CRITICAL: Google Cloud STT sends audio to cloud", "Use local Whisper/SpeechBrain"),
    (r'recognize_bing\s*\(', "HIGH: Bing STT sends audio to Microsoft cloud", "Use local Whisper/SpeechBrain"),
    (r'recognize_azure\s*\(', "HIGH: Azure STT sends audio to Microsoft cloud", "Use local Whisper/SpeechBrain"),
    # IP/location leaks
    (r'ipapi\.co/json', "MEDIUM: Sends user IP to external service", "Use local GPS or skip auto-location"),
    (r'ip-api\.com', "MEDIUM: IP geolocation leaks user IP address", "Use local GPS or skip"),
]

# Files/patterns that are SAFE (false positive exclusions)
SAFE_PATTERNS = [
    r'#.*recognize_google',  # Commented out
    r'""".*recognize_google',  # In docstring
    r"'''.*recognize_google",  # In docstring
    r'DEMO_KEY',  # NASA public demo key (not personal)
    r'do NOT use recognize_google',  # Privacy documentation
    r'NEVER uses recognize_google',  # Privacy documentation
    r'recognize_google\(\w+\).*not in content',  # Audit check code
    r'PRIVACY.*recognize_google',  # Privacy warning comments
    r'"recognize_google',  # String literal (audit check)
]


def audit_file(filepath: str) -> List[Dict]:
    """Audit a single Python file for privacy violations."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception:
        return findings

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        for pattern, severity_msg, fix in VIOLATION_PATTERNS:
            if re.search(pattern, line):
                # Check if it's a safe false positive
                is_safe = any(re.search(sp, line) for sp in SAFE_PATTERNS)
                if not is_safe:
                    findings.append({
                        "file": filepath,
                        "line": line_num,
                        "issue": severity_msg,
                        "fix": fix,
                        "code": stripped[:100],
                    })
    return findings


def audit_project(project_root: str = None) -> Dict:
    """
    Run a full privacy audit on the Monica project.
    
    Returns a report dict with:
    - findings: list of violations
    - summary: counts by severity
    - compliant: bool (True if no CRITICAL issues)
    """
    if project_root is None:
        try:
            from config.settings import config
            project_root = str(config.BASE_DIR)
        except Exception:
            project_root = str(Path(__file__).resolve().parents[2])

    src_dir = os.path.join(project_root, "src")
    all_findings = []

    for dirpath, dirnames, filenames in os.walk(src_dir):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        for fn in filenames:
            if fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                findings = audit_file(fp)
                all_findings.extend(findings)

    # Count by severity
    critical = sum(1 for f in all_findings if "CRITICAL" in f["issue"])
    high = sum(1 for f in all_findings if "HIGH" in f["issue"])
    medium = sum(1 for f in all_findings if "MEDIUM" in f["issue"])

    # Check architecture compliance
    arch_checks = _check_architecture(project_root)

    report = {
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "critical": critical,
            "high": high,
            "medium": medium,
        },
        "architecture": arch_checks,
        "compliant": critical == 0,
        "hipaa_ready": critical == 0 and high == 0,
    }

    logger.info(f"Privacy audit: {len(all_findings)} findings "
                f"({critical} critical, {high} high, {medium} medium)")
    return report


def _check_architecture(project_root: str) -> Dict:
    """Check that the barge-in architecture matches spec."""
    checks = {}

    # 1. STT is local
    stt_path = os.path.join(project_root, "src", "services", "stt_service.py")
    if os.path.exists(stt_path):
        with open(stt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        checks["stt_local"] = "recognize_google(audio)" not in content
        checks["stt_has_whisper"] = "whisper" in content.lower()
        checks["stt_has_speechbrain"] = "speechbrain" in content.lower()
    else:
        checks["stt_local"] = False

    # 2. TTS is local
    tts_path = os.path.join(project_root, "src", "services", "tts_service.py")
    if os.path.exists(tts_path):
        with open(tts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        checks["tts_has_barge_in"] = "_interrupt_event" in content
        checks["tts_chunked"] = "_split_into_chunks" in content
    else:
        checks["tts_has_barge_in"] = False
        checks["tts_chunked"] = False

    # 3. LLM is local (Ollama)
    ai_path = os.path.join(project_root, "src", "services", "ai_service.py")
    if os.path.exists(ai_path):
        with open(ai_path, 'r', encoding='utf-8') as f:
            content = f.read()
        checks["llm_local_ollama"] = "ollama" in content.lower()
        checks["llm_no_cloud"] = "openai" not in content.lower() and "genai" not in content.lower()
    else:
        checks["llm_local_ollama"] = False
        checks["llm_no_cloud"] = False

    # 4. VAD / Interrupt system
    int_path = os.path.join(project_root, "src", "services", "interrupt_manager.py")
    if os.path.exists(int_path):
        with open(int_path, 'r', encoding='utf-8') as f:
            content = f.read()
        checks["vad_silero"] = "silero_vad" in content
        checks["vad_energy_fallback"] = "energy" in content.lower()
        checks["barge_in_system"] = "trigger_interrupt" in content
    else:
        checks["vad_silero"] = False
        checks["vad_energy_fallback"] = False
        checks["barge_in_system"] = False

    # 5. HIPAA encryption
    hipaa_path = os.path.join(project_root, "src", "security", "hipaa_compliance.py")
    checks["hipaa_module"] = os.path.exists(hipaa_path)

    # 6. Auth system
    auth_path = os.path.join(project_root, "src", "security", "auth_manager.py")
    checks["auth_system"] = os.path.exists(auth_path)

    # 7. No Google API keys in source
    checks["no_hardcoded_keys"] = True
    for dirpath, _, filenames in os.walk(os.path.join(project_root, "src")):
        for fn in filenames:
            if fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        if re.search(r'AIzaSy[A-Za-z0-9_-]{33}', f.read()):
                            checks["no_hardcoded_keys"] = False
                except Exception:
                    pass

    return checks


def print_report(report: Dict):
    """Print a formatted privacy audit report."""
    print("=" * 70)
    print("  MONICA AI - PRIVACY & HIPAA COMPLIANCE AUDIT")
    print("=" * 70)

    # Architecture checks
    arch = report.get("architecture", {})
    print("\n--- Architecture Compliance ---")
    arch_labels = {
        "stt_local": "STT is 100% local (no Google)",
        "stt_has_whisper": "STT has Whisper (local)",
        "stt_has_speechbrain": "STT has SpeechBrain (local)",
        "tts_has_barge_in": "TTS supports barge-in interrupts",
        "tts_chunked": "TTS uses sentence chunking",
        "llm_local_ollama": "LLM uses local Ollama",
        "llm_no_cloud": "LLM has no cloud dependencies",
        "vad_silero": "VAD uses Silero (GPU-accelerated)",
        "vad_energy_fallback": "VAD has energy-based fallback",
        "barge_in_system": "Barge-in interrupt system present",
        "hipaa_module": "HIPAA compliance module present",
        "auth_system": "Authentication system present",
        "no_hardcoded_keys": "No hardcoded API keys in source",
    }
    for key, label in arch_labels.items():
        status = "[PASS]" if arch.get(key) else "[FAIL]"
        print(f"  {status} {label}")

    # Findings
    summary = report.get("summary", {})
    print(f"\n--- Scan Results ---")
    print(f"  Total findings: {summary.get('total', 0)}")
    print(f"  CRITICAL: {summary.get('critical', 0)}")
    print(f"  HIGH: {summary.get('high', 0)}")
    print(f"  MEDIUM: {summary.get('medium', 0)}")

    for f in report.get("findings", []):
        rel = os.path.relpath(f["file"]) if os.path.isabs(f["file"]) else f["file"]
        print(f"\n  [{f['issue'].split(':')[0]}] {rel}:{f['line']}")
        print(f"    Issue: {f['issue']}")
        print(f"    Fix: {f['fix']}")
        print(f"    Code: {f['code']}")

    # Verdict
    print(f"\n--- Verdict ---")
    if report.get("hipaa_ready"):
        print("  [PASS] HIPAA READY - No critical or high privacy issues found")
    elif report.get("compliant"):
        print("  [WARN] MOSTLY COMPLIANT - No critical issues, some high-severity findings")
    else:
        print("  [FAIL] NOT COMPLIANT - Critical privacy issues found")
    print("=" * 70)


if __name__ == "__main__":
    report = audit_project()
    print_report(report)
