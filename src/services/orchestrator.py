"""
Service Orchestrator for Monica AI.
Manages service lifecycle, health monitoring, and inter-service communication.
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger("Monica.Orchestrator")


class ServiceState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RESTARTING = "restarting"


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service_class: Type
    config: Dict[str, Any]
    instance: Any = None
    thread: Optional[threading.Thread] = None
    state: ServiceState = ServiceState.STOPPED
    restart_count: int = 0
    max_restarts: int = 5
    last_error: Optional[str] = None
    ready_event: Optional[threading.Event] = None


class ServiceOrchestrator:
    """
    Manages Monica AI services with fault tolerance and auto-restart.
    
    Features:
    - Service registration and lifecycle management
    - Health monitoring
    - Auto-restart on failure
    - Inter-service message passing via shared state
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.services: Dict[str, ServiceInfo] = {}
        self.shared_state: Dict[str, Any] = {}
        self.handlers: Dict[str, List] = {}
        self.state_lock = threading.Lock()
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        logger.info("Service Orchestrator created")

    def register_service(self, service_class: Type, name: str, config: Dict[str, Any] = None):
        """Register a service to be managed."""
        self.services[name] = ServiceInfo(
            name=name,
            service_class=service_class,
            config=config or {},
            ready_event=threading.Event()
        )
        logger.info(f"Registered service: {name}")

    def start(self):
        """Start all registered services."""
        self.is_running = True
        
        for name, info in self.services.items():
            self._start_service(name)
        
        # Start health monitor
        self.monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Started {len(self.services)} services")

    def _start_service(self, name: str):
        """Start a single service in its own thread."""
        info = self.services.get(name)
        if not info:
            return
        
        info.state = ServiceState.STARTING
        
        def _run_service():
            try:
                # Create service instance
                instance = info.service_class(self, info.config)
                info.instance = instance
                
                # Initialize
                if hasattr(instance, 'initialize'):
                    instance.initialize()
                
                info.state = ServiceState.RUNNING
                info.ready_event.set()
                logger.info(f"Service '{name}' is ready")
                
                # Run main loop if service has one
                if hasattr(instance, 'run'):
                    instance.run()
                elif hasattr(instance, 'process'):
                    # Backward-compatible processing loop for services that expose
                    # process() instead of run().
                    while self.is_running and info.state == ServiceState.RUNNING:
                        instance.process()
                    
            except Exception as e:
                info.state = ServiceState.ERROR
                info.last_error = str(e)
                info.ready_event.set()  # Unblock waiters
                logger.error(f"Service '{name}' failed: {e}")
        
        info.thread = threading.Thread(target=_run_service, daemon=True, name=f"svc-{name}")
        info.thread.start()

    def stop(self):
        """Stop all services."""
        self.is_running = False
        
        for name, info in self.services.items():
            try:
                if info.instance and hasattr(info.instance, 'stop'):
                    info.instance.stop()
                info.state = ServiceState.STOPPED
                logger.info(f"Service '{name}' stopped")
            except Exception as e:
                logger.error(f"Error stopping service '{name}': {e}")

    def wait_for_all_ready(self, timeout: float = 30) -> bool:
        """Wait for all services to be ready."""
        deadline = time.time() + timeout
        
        for name, info in self.services.items():
            remaining = deadline - time.time()
            if remaining <= 0:
                return False
            if info.ready_event and not info.ready_event.wait(timeout=remaining):
                logger.warning(f"Service '{name}' did not become ready in time")
                return False
        
        return True

    def get_service(self, name: str) -> Optional[Any]:
        """Get a running service instance by name."""
        info = self.services.get(name)
        if info and info.instance:
            return info.instance
        return None

    def set_shared(self, key: str, value: Any):
        """Set a value in shared state (thread-safe)."""
        with self.state_lock:
            self.shared_state[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get a value from shared state (thread-safe)."""
        with self.state_lock:
            return self.shared_state.get(key, default)

    def get_service_status(self, name: Optional[str] = None):
        """Get status for one service or all services."""
        if name is not None:
            info = self.services.get(name)
            if not info:
                return ServiceState.STOPPED
            return info.state
        return {svc_name: info.state.value for svc_name, info in self.services.items()}

    def get_all_status(self) -> Dict[str, str]:
        """Compatibility alias for status retrieval."""
        return self.get_service_status()

    def register_handler(self, service_name: str, handler):
        """Register a callback for messages addressed to a service."""
        self.handlers.setdefault(service_name, []).append(handler)

    def send_message(self, destination: str, message_type: str, payload: Dict[str, Any], source: str = "orchestrator") -> bool:
        """
        Best-effort compatibility message dispatch.

        - Calls service.handle_request(payload) when available.
        - Notifies registered handlers with a lightweight message object.
        """
        info = self.services.get(destination)
        if not info or not info.instance:
            return False

        message = type(
            "ServiceMessage",
            (),
            {"source": source, "destination": destination, "message_type": message_type, "payload": payload},
        )()

        handled = False

        if hasattr(info.instance, 'handle_request'):
            try:
                info.instance.handle_request(payload)
                handled = True
            except Exception as e:
                logger.error(f"Error handling request for '{destination}': {e}")

        for handler in self.handlers.get(destination, []):
            try:
                handler(message)
                handled = True
            except Exception as e:
                logger.error(f"Error in handler for '{destination}': {e}")

        return handled

    def _health_monitor_loop(self):
        """Monitor service health and auto-restart failed services."""
        while self.is_running:
            time.sleep(5)
            
            for name, info in self.services.items():
                if not self.is_running:
                    break
                    
                # Check if service thread is alive
                if info.state == ServiceState.RUNNING and info.thread and not info.thread.is_alive():
                    logger.warning(f"Service '{name}' thread died unexpectedly")
                    info.state = ServiceState.ERROR
                
                # Auto-restart failed services
                if info.state == ServiceState.ERROR and info.restart_count < info.max_restarts:
                    info.restart_count += 1
                    info.state = ServiceState.RESTARTING
                    logger.info(f"Auto-restarting service '{name}' (attempt {info.restart_count}/{info.max_restarts})")
                    self._start_service(name)
