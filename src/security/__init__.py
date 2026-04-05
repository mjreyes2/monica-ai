"""Monica AI Security Module - HIPAA Compliance & Authentication."""
try:
    from security.hipaa_compliance import HIPAACompliance, get_hipaa_compliance
except ImportError:
    pass
try:
    from security.auth_manager import AuthManager, get_auth_manager
except ImportError:
    pass
