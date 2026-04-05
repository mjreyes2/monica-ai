#!/usr/bin/env python3
"""
Automatic Crash Reporter for Monica AI
Saves crash logs and emails them automatically
"""
import sys
import traceback
import datetime
from pathlib import Path
import platform
import json

class CrashReporter:
    """Handles crash reporting for Monica AI"""

    def __init__(self, user_email="marvinjr18@hotmail.com"):
        self.user_email = user_email
        self.project_root = Path(__file__).parent.parent
        self.crash_dir = self.project_root / "crash_reports"
        self.crash_dir.mkdir(exist_ok=True)

    def generate_report(self, error_type, error_message, error_traceback=None, context=None):
        """Generate a crash report and save to file"""

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.crash_dir / f"crash_report_{timestamp}.txt"

        # Collect system info
        system_info = {
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": str(error_message),
            "python_version": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        # Build report
        report = []
        report.append("=" * 80)
        report.append("MONICA AI - CRASH REPORT")
        report.append("=" * 80)
        report.append(f"Date/Time: {datetime.datetime.now()}")
        report.append(f"Error Type: {error_type}")
        report.append("")

        report.append("-" * 80)
        report.append("ERROR MESSAGE:")
        report.append("-" * 80)
        report.append(str(error_message))
        report.append("")

        if error_traceback:
            report.append("-" * 80)
            report.append("STACK TRACE:")
            report.append("-" * 80)
            report.append(error_traceback)
            report.append("")

        if context:
            report.append("-" * 80)
            report.append("CONTEXT:")
            report.append("-" * 80)
            for key, value in context.items():
                report.append(f"{key}: {value}")
            report.append("")

        report.append("-" * 80)
        report.append("SYSTEM INFORMATION:")
        report.append("-" * 80)
        report.append(f"Python: {sys.version}")
        report.append(f"Platform: {platform.platform()}")
        report.append(f"Machine: {platform.machine()}")
        report.append(f"Processor: {platform.processor()}")
        report.append("")

        # Try to get package versions
        try:
            import torch
            report.append(f"PyTorch: {torch.__version__}")
        except:
            pass

        try:
            import speechbrain
            report.append(f"SpeechBrain: {speechbrain.__version__}")
        except:
            pass

        try:
            import pyaudio
            report.append(f"PyAudio: {pyaudio.__version__}")
        except:
            pass

        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        # Save to file
        report_text = "\n".join(report)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"\n[CRASH REPORTER] Report saved to: {report_file}")

        # Try to email it
        self.email_report(report_file, report_text)

        return report_file

    def email_report(self, report_file, report_text):
        """Email the crash report or save draft if SMTP not configured"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import os

            # Check for SMTP configuration
            smtp_enabled = os.environ.get('MONICA_SMTP_ENABLED', '').lower() == 'true'
            smtp_server = os.environ.get('MONICA_SMTP_SERVER', '')
            smtp_port = int(os.environ.get('MONICA_SMTP_PORT', '587'))
            smtp_user = os.environ.get('MONICA_SMTP_USER', '')
            smtp_password = os.environ.get('MONICA_SMTP_PASSWORD', '')
            smtp_from = os.environ.get('MONICA_SMTP_FROM', 'monica-crash-reporter@localhost')

            email_file = report_file.with_suffix('.email.txt')

            email_content = f"""To: {self.user_email}
From: {smtp_from}
Subject: Monica AI Crash Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{report_text}

---
This is an automatic crash report from Monica AI.
Report saved to: {report_file}
"""

            # Save email draft regardless of SMTP status
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write(email_content)

            print(f"[CRASH REPORTER] Email draft saved to: {email_file}")

            # Try to send via SMTP if configured
            if smtp_enabled and smtp_server and smtp_user:
                try:
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = smtp_from
                    msg['To'] = self.user_email
                    msg['Subject'] = f"Monica AI Crash Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    # Attach report text
                    body = f"{report_text}\n\n---\nThis is an automatic crash report from Monica AI.\nReport saved to: {report_file}"
                    msg.attach(MIMEText(body, 'plain'))

                    # Connect and send
                    print(f"[CRASH REPORTER] Connecting to SMTP server: {smtp_server}:{smtp_port}")
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(smtp_user, smtp_password)
                        server.send_message(msg)

                    print(f"[CRASH REPORTER] ✅ Email sent successfully to: {self.user_email}")

                except Exception as smtp_err:
                    print(f"[CRASH REPORTER] ⚠️ SMTP send failed: {smtp_err}")
                    print(f"[CRASH REPORTER] Email draft saved instead: {email_file}")

            else:
                print(f"[CRASH REPORTER] SMTP not configured - email draft saved only")
                print(f"[CRASH REPORTER] To enable auto-email, set environment variables:")
                print(f"  MONICA_SMTP_ENABLED=true")
                print(f"  MONICA_SMTP_SERVER=smtp.example.com")
                print(f"  MONICA_SMTP_PORT=587")
                print(f"  MONICA_SMTP_USER=your_email@example.com")
                print(f"  MONICA_SMTP_PASSWORD=your_password")
                print(f"  MONICA_SMTP_FROM=monica@example.com")

        except Exception as e:
            print(f"[CRASH REPORTER] Could not prepare email: {e}")

    def capture_exception(self, error_type="Unknown Error", context=None):
        """Capture current exception and generate report"""
        exc_type, exc_value, exc_tb = sys.exc_info()

        if exc_type is None:
            return None

        error_message = str(exc_value)
        error_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        return self.generate_report(error_type, error_message, error_traceback, context)


# Global crash reporter instance
_crash_reporter = None

def get_crash_reporter():
    """Get or create global crash reporter"""
    global _crash_reporter
    if _crash_reporter is None:
        _crash_reporter = CrashReporter()
    return _crash_reporter

def report_crash(error_type, error_message, error_traceback=None, context=None):
    """Quick function to report a crash"""
    reporter = get_crash_reporter()
    return reporter.generate_report(error_type, error_message, error_traceback, context)

def capture_exception(error_type="Unknown Error", context=None):
    """Quick function to capture and report current exception"""
    reporter = get_crash_reporter()
    return reporter.capture_exception(error_type, context)


if __name__ == "__main__":
    # Test crash reporter
    print("Testing crash reporter...")

    try:
        # Simulate a crash
        raise ValueError("This is a test error for crash reporting")
    except:
        report_file = capture_exception("Test Crash", {
            "test_mode": True,
            "component": "crash_reporter test"
        })
        print(f"\nTest report generated: {report_file}")
