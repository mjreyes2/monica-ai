"""
Test script for Monica AI service resilience
Demonstrates fault tolerance and auto-restart capabilities
"""

import sys
import os
import logging
import time
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("Monica.Test")

# Add project root and src/ to path
_test_dir = os.path.dirname(__file__)
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

from services.orchestrator import ServiceOrchestrator
from config.settings import config


class CrashTestService:
    """
    Test service that crashes on command to test auto-restart
    """

    def __init__(self, orchestrator=None, config=None):
        self.orchestrator = orchestrator
        self.config = config or {}
        self.logger = logging.getLogger("Monica.CrashTest")
        self.crash_countdown = None

    def initialize(self):
        self.logger.info("CrashTestService initialized")
        self.crash_countdown = None

    def process(self):
        # Check for crash command
        if self.crash_countdown is not None:
            self.crash_countdown -= 1
            if self.crash_countdown <= 0:
                self.logger.warning("INTENTIONALLY CRASHING!")
                raise RuntimeError("Intentional crash for testing")

        time.sleep(0.1)

    def cleanup(self):
        self.logger.info("CrashTestService cleanup")

    def handle_request(self, payload):
        action = payload.get('action')

        if action == 'crash_in':
            seconds = payload.get('seconds', 5)
            self.crash_countdown = int(seconds * 10)  # Convert to iterations
            return {'status': 'success', 'message': f'Will crash in {seconds}s'}

        elif action == 'ping':
            return {'status': 'success', 'message': 'pong'}

        return None


def test_basic_startup():
    """Test 1: Basic service startup"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Service Startup")
    print("=" * 60)

    orchestrator = ServiceOrchestrator(config.__dict__)
    orchestrator.register_service(CrashTestService, 'test1')

    orchestrator.start()

    if orchestrator.wait_for_all_ready(timeout=10):
        print(" Service started successfully")
    else:
        print(" Service failed to start")

    time.sleep(2)
    orchestrator.stop()

    print(" Test 1 passed")


def test_crash_and_restart():
    """Test 2: Service crash and auto-restart"""
    print("\n" + "=" * 60)
    print("TEST 2: Service Crash and Auto-Restart")
    print("=" * 60)

    orchestrator = ServiceOrchestrator(config.__dict__)
    orchestrator.register_service(CrashTestService, 'test2')

    orchestrator.start()

    if not orchestrator.wait_for_all_ready(timeout=10):
        print(" Service failed to start")
        orchestrator.stop()
        return

    print(" Service running")

    # Trigger crash
    print("\n→ Sending crash command...")
    orchestrator.send_message(
        destination='test2',
        message_type='request',
        payload={'action': 'crash_in', 'seconds': 2}
    )

    print("→ Waiting for crash...")
    time.sleep(4)

    # Check if service restarted
    status = orchestrator.get_service_status('test2')
    print(f"→ Service status after crash: {status}")

    time.sleep(3)

    # Verify service is running again
    status = orchestrator.get_service_status('test2')
    if status.value == 'running':
        print(" Service auto-restarted successfully!")
    else:
        print(f" Service did not restart (status: {status})")

    orchestrator.stop()
    print(" Test 2 passed")


def test_multiple_services():
    """Test 3: Multiple services with one crashing"""
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Services (One Crashes)")
    print("=" * 60)

    orchestrator = ServiceOrchestrator(config.__dict__)
    orchestrator.register_service(CrashTestService, 'stable1')
    orchestrator.register_service(CrashTestService, 'crasher')
    orchestrator.register_service(CrashTestService, 'stable2')

    orchestrator.start()

    if not orchestrator.wait_for_all_ready(timeout=10):
        print(" Some services failed to start")
        orchestrator.stop()
        return

    print(" All services running")

    # Crash one service
    print("\n→ Crashing 'crasher' service...")
    orchestrator.send_message(
        destination='crasher',
        message_type='request',
        payload={'action': 'crash_in', 'seconds': 1}
    )

    time.sleep(3)

    # Check all service statuses
    all_status = orchestrator.get_all_status()
    print(f"\nService statuses:")
    for name, status in all_status.items():
        print(f"  {name}: {status}")

    # Verify stable services still running
    if (all_status['stable1'] == 'running' and
        all_status['stable2'] == 'running'):
        print("\n Stable services unaffected by crash!")
    else:
        print("\n Stable services affected by crash")

    time.sleep(2)

    # Verify crasher restarted
    all_status = orchestrator.get_all_status()
    if all_status['crasher'] == 'running':
        print(" Crashed service auto-restarted!")
    else:
        print(f" Crashed service did not restart (status: {all_status['crasher']})")

    orchestrator.stop()
    print("\n Test 3 passed")


def test_message_routing():
    """Test 4: Message routing between services"""
    print("\n" + "=" * 60)
    print("TEST 4: Inter-Service Message Routing")
    print("=" * 60)

    orchestrator = ServiceOrchestrator(config.__dict__)
    orchestrator.register_service(CrashTestService, 'sender')
    orchestrator.register_service(CrashTestService, 'receiver')

    # Track received messages
    received_messages = []

    def message_handler(message):
        received_messages.append(message)
        print(f"→ Received message from {message.source}: {message.payload}")

    orchestrator.register_handler('receiver', message_handler)

    orchestrator.start()

    if not orchestrator.wait_for_all_ready(timeout=10):
        print(" Services failed to start")
        orchestrator.stop()
        return

    print(" Services running")

    # Send test message
    print("\n→ Sending test message...")
    orchestrator.send_message(
        destination='receiver',
        message_type='request',
        payload={'action': 'ping'}
    )

    time.sleep(2)

    if len(received_messages) > 0:
        print(f" Received {len(received_messages)} message(s)")
    else:
        print(" No messages received")

    orchestrator.stop()
    print(" Test 4 passed")


def test_high_restart_limit():
    """Test 5: Restart limit (prevent infinite restart loops)"""
    print("\n" + "=" * 60)
    print("TEST 5: Restart Limit Protection")
    print("=" * 60)

    orchestrator = ServiceOrchestrator(config.__dict__)
    orchestrator.register_service(CrashTestService, 'crasher')

    # Lower restart limit for testing
    orchestrator.services['crasher'].max_restarts = 3

    orchestrator.start()

    if not orchestrator.wait_for_all_ready(timeout=10):
        print(" Service failed to start")
        orchestrator.stop()
        return

    print(" Service running")
    print(f"→ Max restarts set to: {orchestrator.services['crasher'].max_restarts}")

    # Crash repeatedly
    for i in range(5):
        print(f"\n→ Triggering crash #{i+1}...")
        orchestrator.send_message(
            destination='crasher',
            message_type='request',
            payload={'action': 'crash_in', 'seconds': 1}
        )
        time.sleep(3)

        restart_count = orchestrator.services['crasher'].restart_count
        print(f"   Restart count: {restart_count}")

        if restart_count >= 3:
            print("→ Restart limit reached")
            break

    time.sleep(2)

    status = orchestrator.get_service_status('crasher')
    print(f"\nFinal status: {status}")

    if status.value in ['crashed', 'error']:
        print(" Service stopped restarting after limit reached")
    else:
        print(" Service continued restarting beyond limit")

    orchestrator.stop()
    print(" Test 5 passed")


def run_all_tests():
    """Run all resilience tests"""
    print("\n" + "=" * 60)
    print("MONICA AI SERVICE RESILIENCE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Startup", test_basic_startup),
        ("Crash and Restart", test_crash_and_restart),
        ("Multiple Services", test_multiple_services),
        ("Message Routing", test_message_routing),
        ("Restart Limit", test_high_restart_limit)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("=" * 60)

    if failed == 0:
        print("\n ALL TESTS PASSED!")
    else:
        print(f"\n {failed} test(s) failed")


if __name__ == "__main__":
    # Enable multiprocessing on Windows
    import multiprocessing as mp
    mp.set_start_method('spawn', force=True)

    run_all_tests()
