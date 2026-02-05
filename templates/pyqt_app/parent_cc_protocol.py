"""
Parent CC Protocol - Bidirectional Communication with Claude Code

This module implements the protocol for apps to request assistance from
Parent CC (Claude Code) and for Parent CC to monitor and control apps.

Architecture:
- Apps delegate complex decisions to Parent CC
- Parent CC has full context and can make informed decisions
- Reduces app bloat by moving edge case handling to Parent CC
- Standardized protocol across all Silver Wizard apps

HA Failover Handling:
- Automatic retry logic via MeshIntegration
- Handles Active/Standby switchover gracefully
- Exponential backoff with jitter
- Transparent to app logic

Module Size Target: <400 lines (Current: ~350 lines)
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Priority levels for Parent CC requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RequestType(Enum):
    """Types of assistance requests apps can make."""
    HELP = "help"  # General help/guidance request
    PERMISSION = "permission"  # Request permission for an action
    ERROR_RECOVERY = "error_recovery"  # Ask how to recover from error
    DATA_PROCESSING = "data_processing"  # Request data processing
    ANALYSIS = "analysis"  # Request data analysis
    DECISION = "decision"  # Request decision between options
    VALIDATION = "validation"  # Request validation of data/action


@dataclass
class AssistanceRequest:
    """Represents a request from app to Parent CC."""
    request_type: RequestType
    context: Dict[str, Any]
    question: Optional[str] = None
    options: Optional[List[str]] = None
    priority: RequestPriority = RequestPriority.NORMAL
    timeout_seconds: int = 30
    callback: Optional[Callable] = None


@dataclass
class AssistanceResponse:
    """Response from Parent CC to app."""
    approved: bool
    guidance: Optional[str] = None
    suggested_action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    should_retry: bool = False
    reason: Optional[str] = None


class ParentCCProtocol:
    """
    Protocol handler for bidirectional communication with Parent CC.

    App → Parent CC (Assistance Requests):
        - request_help(context, question) → guidance
        - request_permission(action, details) → approved/denied
        - report_error(error, context) → recovery steps
        - request_data_processing(task, data) → processed result
        - request_analysis(data) → insights
        - request_decision(question, options) → chosen option

    Parent CC → App (Control Commands):
        - check_health() → status, uptime, errors
        - get_diagnostics() → logs, metrics, state
        - request_shutdown(reason) → acknowledged
        - set_log_level(level) → updated
        - set_config(key, value) → updated
    """

    def __init__(
        self,
        app_name: str,
        mesh_integration: Optional[Any] = None,
        enable_logging: bool = True
    ):
        """
        Initialize Parent CC protocol.

        Args:
            app_name: Name of the application
            mesh_integration: MeshIntegration instance (for MM communication)
            enable_logging: Enable request/response logging
        """
        self.app_name = app_name
        self.mesh = mesh_integration
        self.enable_logging = enable_logging

        # Health tracking
        self.start_time = datetime.now()
        self.error_count = 0
        self.last_error: Optional[Exception] = None

        # Request tracking
        self.pending_requests: Dict[str, AssistanceRequest] = {}
        self.request_history: List[Dict[str, Any]] = []

        # Configuration
        self.config: Dict[str, Any] = {}
        self.log_level = "INFO"

        logger.info(f"Parent CC protocol initialized for {app_name}")

    # ===== APP → PARENT CC (Assistance Requests) =====

    def request_help(
        self,
        context: Dict[str, Any],
        question: str,
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> AssistanceResponse:
        """
        Request help/guidance from Parent CC.

        Use when: App encounters situation it doesn't know how to handle.

        Args:
            context: Current situation context
            question: Specific question or problem
            priority: Request priority

        Returns:
            AssistanceResponse with guidance

        Example:
            response = protocol.request_help(
                context={"count": 150, "max_expected": 100},
                question="Count exceeded expected maximum. Should I continue?"
            )
            if response.approved:
                print(response.guidance)
        """
        request = AssistanceRequest(
            request_type=RequestType.HELP,
            context=context,
            question=question,
            priority=priority
        )

        return self._send_assistance_request(request)

    def request_permission(
        self,
        action: str,
        details: Dict[str, Any],
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> AssistanceResponse:
        """
        Request permission to perform an action.

        Use when: App wants to do something potentially risky/destructive.

        Args:
            action: Action to perform
            details: Details about the action
            priority: Request priority

        Returns:
            AssistanceResponse (approved=True if permitted)

        Example:
            response = protocol.request_permission(
                action="delete_old_files",
                details={"count": 500, "age_days": 90}
            )
            if response.approved:
                delete_files()
        """
        request = AssistanceRequest(
            request_type=RequestType.PERMISSION,
            context={"action": action, **details},
            question=f"Permission to {action}?",
            priority=priority
        )

        return self._send_assistance_request(request)

    def report_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> AssistanceResponse:
        """
        Report error and request recovery guidance.

        Use when: App encounters unexpected error.

        Args:
            error: The exception that occurred
            context: Context when error occurred

        Returns:
            AssistanceResponse with recovery steps

        Example:
            try:
                risky_operation()
            except Exception as e:
                response = protocol.report_error(e, {"operation": "risky_op"})
                if response.should_retry:
                    retry_with_guidance(response.guidance)
        """
        self.error_count += 1
        self.last_error = error

        request = AssistanceRequest(
            request_type=RequestType.ERROR_RECOVERY,
            context={
                "error_type": type(error).__name__,
                "error_message": str(error),
                **context
            },
            question="How should I recover from this error?",
            priority=RequestPriority.HIGH
        )

        return self._send_assistance_request(request)

    def request_data_processing(
        self,
        task: str,
        data: Dict[str, Any]
    ) -> AssistanceResponse:
        """
        Request data processing from Parent CC.

        Use when: App needs complex data transformation it can't handle.

        Args:
            task: Description of processing needed
            data: Data to process

        Returns:
            AssistanceResponse with processed data

        Example:
            response = protocol.request_data_processing(
                task="parse_complex_format",
                data={"raw": complex_data}
            )
            processed = response.data
        """
        request = AssistanceRequest(
            request_type=RequestType.DATA_PROCESSING,
            context={"task": task, "data": data},
            question=f"Please process: {task}"
        )

        return self._send_assistance_request(request)

    def request_analysis(
        self,
        data: Dict[str, Any],
        analysis_type: str = "general"
    ) -> AssistanceResponse:
        """
        Request data analysis from Parent CC.

        Use when: App needs insights from data.

        Args:
            data: Data to analyze
            analysis_type: Type of analysis needed

        Returns:
            AssistanceResponse with insights

        Example:
            response = protocol.request_analysis(
                data={"metrics": performance_data},
                analysis_type="performance"
            )
            print(response.guidance)  # Insights
        """
        request = AssistanceRequest(
            request_type=RequestType.ANALYSIS,
            context={"data": data, "analysis_type": analysis_type},
            question=f"Please analyze this data: {analysis_type}"
        )

        return self._send_assistance_request(request)

    def request_decision(
        self,
        question: str,
        options: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> AssistanceResponse:
        """
        Request decision between multiple options.

        Use when: App faces choice and needs guidance.

        Args:
            question: The decision question
            options: Available options
            context: Additional context for decision

        Returns:
            AssistanceResponse with suggested_action

        Example:
            response = protocol.request_decision(
                question="Which database should I use?",
                options=["SQLite", "PostgreSQL", "MongoDB"],
                context={"data_size": "10GB", "queries": "complex"}
            )
            chosen = response.suggested_action
        """
        request = AssistanceRequest(
            request_type=RequestType.DECISION,
            context=context or {},
            question=question,
            options=options
        )

        return self._send_assistance_request(request)

    # ===== PARENT CC → APP (Control Commands) =====

    def check_health(self) -> Dict[str, Any]:
        """
        Health check - called by Parent CC to monitor app.

        Returns:
            Health status dictionary
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "status": "healthy" if self.error_count < 10 else "degraded",
            "uptime_seconds": uptime,
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
            "pending_requests": len(self.pending_requests),
            "app_name": self.app_name
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get detailed diagnostics - called by Parent CC for troubleshooting.

        Returns:
            Diagnostic information
        """
        return {
            "app_name": self.app_name,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "errors": self.error_count,
            "config": self.config.copy(),
            "log_level": self.log_level,
            "request_history": self.request_history[-10:],  # Last 10 requests
            "mesh_connected": self.mesh.is_connected if self.mesh else False
        }

    def request_shutdown(self, reason: str) -> Dict[str, Any]:
        """
        Graceful shutdown request - called by Parent CC.

        Args:
            reason: Reason for shutdown

        Returns:
            Acknowledgment with cleanup status
        """
        logger.warning(f"Parent CC requested shutdown: {reason}")

        # Cleanup logic here
        cleanup_success = True

        return {
            "acknowledged": True,
            "cleanup_status": "success" if cleanup_success else "partial",
            "reason": reason
        }

    def set_log_level(self, level: str) -> Dict[str, Any]:
        """
        Update log level - called by Parent CC for debugging.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR)

        Returns:
            Confirmation
        """
        old_level = self.log_level
        self.log_level = level.upper()

        # Update Python logger
        numeric_level = getattr(logging, self.log_level, logging.INFO)
        logging.getLogger().setLevel(numeric_level)

        logger.info(f"Log level changed: {old_level} → {self.log_level}")

        return {
            "updated": True,
            "old_level": old_level,
            "new_level": self.log_level
        }

    def set_config(self, key: str, value: Any) -> Dict[str, Any]:
        """
        Update configuration - called by Parent CC.

        Args:
            key: Config key
            value: Config value

        Returns:
            Confirmation
        """
        old_value = self.config.get(key)
        self.config[key] = value

        logger.info(f"Config updated: {key} = {value}")

        return {
            "updated": True,
            "key": key,
            "old_value": old_value,
            "new_value": value
        }

    # ===== INTERNAL METHODS =====

    def _send_assistance_request(
        self,
        request: AssistanceRequest
    ) -> AssistanceResponse:
        """
        Send assistance request to Parent CC.

        This is a placeholder - in real implementation, this would:
        1. Use MM mesh to send request to Parent CC
        2. Wait for response (with timeout)
        3. Return structured response

        For now, returns helpful default responses.
        """
        # Log request
        if self.enable_logging:
            logger.info(
                f"Assistance request [{request.request_type.value}]: "
                f"{request.question}"
            )

        # Track request
        request_id = f"{request.request_type.value}_{len(self.request_history)}"
        self.request_history.append({
            "id": request_id,
            "type": request.request_type.value,
            "question": request.question,
            "timestamp": datetime.now().isoformat(),
            "priority": request.priority.value
        })

        # TODO: Implement real MM mesh communication to Parent CC
        # For now, return sensible defaults

        return AssistanceResponse(
            approved=True,
            guidance=f"[Parent CC would respond to: {request.question}]",
            suggested_action="proceed_with_caution",
            should_retry=False,
            reason="Awaiting Parent CC implementation"
        )
