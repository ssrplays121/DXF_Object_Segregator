# utils/error_handling.py
# Structured exception hierarchy with recovery points
# Implements robust error handling strategy (Decision #20)
# Reference: https://docs.python.org/3/library/exceptions.html
from typing import Dict, Any, Optional, List
import logging
from utils.logging import get_logger
import time
import json
from datetime import datetime

logger = get_logger(__name__)


class ApplicationError(Exception):
    """
    Base class for all application-specific exceptions
    Implements structured exception hierarchy (Decision #20)
    """
    def __init__(self, message: str, error_code: str = None,
                 recovery_suggestion: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or "APP_ERROR"
        self.recovery_suggestion = recovery_suggestion or "Contact support for assistance"
        self.context = context or {}
        self.timestamp = datetime.now()

    def __str__(self):
        return f"{self.error_code}: {super().__str__()}"

    def log_error(self):
        """Log error with full context"""
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        logger.error(
            f"{self.error_code}: {str(self)} | Context: {context_str} | "
            f"Suggestion: {self.recovery_suggestion}"
        )


# Backward compatibility alias
DXFObjectSegregatorError = ApplicationError


class FileError(ApplicationError):
    """Base class for file-related errors"""
    pass


class DXFProcessingError(FileError):
    """Error during DXF file processing"""
    def __init__(self, message: str, file_path: str = None,
                 line_number: int = None, recovery_suggestion: str = None):
        context = {}
        if file_path:
            context['file_path'] = file_path
        if line_number:
            context['line_number'] = line_number
        if recovery_suggestion is None:
            recovery_suggestion = (
                "Try opening the file in a DXF editor to check for corruption, "
                "or use a different DXF file"
            )
        super().__init__(
            message=message,
            error_code="DXF_PROCESSING_ERROR",
            recovery_suggestion=recovery_suggestion,
            context=context
        )


class DXFVersionError(DXFProcessingError):
    """Error for unsupported DXF versions"""
    def __init__(self, file_path: str, version: str, supported_versions: List[str]):
        message = f"Unsupported DXF version: {version}"
        recovery_suggestion = (
            f"This application supports versions: {', '.join(supported_versions)}. "
            f"Convert your file to a supported version using a DXF converter."
        )
        context = {
            'file_path': file_path,
            'version': version,
            'supported_versions': supported_versions
        }
        super().__init__(
            message=message,
            file_path=file_path,
            recovery_suggestion=recovery_suggestion,
        )
        self.context = context


class GeometricError(ApplicationError):
    """Base class for geometric algorithm errors"""
    pass


class VertexSharingError(GeometricError):
    """Error during vertex sharing detection"""
    def __init__(self, message: str, entity_count: int = None,
                 algorithm_mode: int = None, recovery_suggestion: str = None):
        context = {}
        if entity_count:
            context['entity_count'] = entity_count
        if algorithm_mode:
            context['algorithm_mode'] = algorithm_mode
        if recovery_suggestion is None:
            recovery_suggestion = (
                "Try reducing the tolerance percentage or switching to a different "
                "algorithm mode. Check for degenerate geometry in your DXF file."
            )
        super().__init__(
            message=message,
            error_code="VERTEX_SHARING_ERROR",
            recovery_suggestion=recovery_suggestion,
            context=context
        )


class IntersectionError(GeometricError):
    """Error during geometric intersection detection"""
    pass


class ContainmentError(GeometricError):
    """Error during spatial containment testing"""
    pass


class AlgorithmTimeoutError(ApplicationError):
    """Error when algorithm exceeds time limit"""
    def __init__(self, algorithm_name: str, timeout_seconds: float,
                 actual_time: float = None, entity_count: int = None):
        message = f"Algorithm '{algorithm_name}' timed out after {timeout_seconds} seconds"
        context = {
            'algorithm_name': algorithm_name,
            'timeout_seconds': timeout_seconds
        }
        if actual_time:
            context['actual_time'] = actual_time
        if entity_count:
            context['entity_count'] = entity_count
        recovery_suggestion = (
            f"Try reducing the number of entities, increasing the timeout limit, "
            f"or switching to a more efficient algorithm mode for '{algorithm_name}'"
        )
        super().__init__(
            message=message,
            error_code="ALGORITHM_TIMEOUT",
            recovery_suggestion=recovery_suggestion,
            context=context
        )


class TreeConstructionError(ApplicationError):
    """Error during object tree construction"""
    def __init__(self, message: str, node_count: int = None,
                 edge_count: int = None, recovery_suggestion: str = None):
        context = {}
        if node_count:
            context['node_count'] = node_count
        if edge_count:
            context['edge_count'] = edge_count
        if recovery_suggestion is None:
            recovery_suggestion = (
                "Check for circular references in your object hierarchy. "
                "Try simplifying the geometry or using a different tree construction mode."
            )
        super().__init__(
            message=message,
            error_code="TREE_CONSTRUCTION_ERROR",
            recovery_suggestion=recovery_suggestion,
            context=context
        )


class UIError(ApplicationError):
    """Base class for UI-related errors"""
    pass


class VisualizationError(UIError):
    """Error during visualization rendering"""
    pass


# Backward compatibility aliases
ProcessingError = ApplicationError
ValidationError = ApplicationError


class RecoveryPoint:
    """
    Context manager for error recovery points
    Allows partial results to be preserved after errors (Decision #20)
    """
    def __init__(self, operation_name: str, recovery_data: Dict[str, Any] = None):
        self.operation_name = operation_name
        self.recovery_data = recovery_data or {}
        self.success = False
        self.error = None

    def __enter__(self):
        logger.debug(f"Starting recovery point: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            logger.debug(f"Recovery point succeeded: {self.operation_name}")
            return False

        # Handle the exception
        self.error = exc_val
        self.success = False
        if isinstance(exc_val, ApplicationError):
            # Structured application error
            exc_val.log_error()
        else:
            # Unexpected exception
            error = ApplicationError(
                message=f"Unexpected error in {self.operation_name}: {str(exc_val)}",
                error_code="UNEXPECTED_ERROR",
                recovery_suggestion="This appears to be a bug. Please report this issue.",
                context={
                    'operation': self.operation_name,
                    'exception_type': exc_type.__name__,
                    'exception_message': str(exc_val)
                }
            )
            error.log_error()

        # Attempt recovery if possible
        self.attempt_recovery()

        # Don't suppress the exception - let it propagate
        return False

    def attempt_recovery(self):
        """Attempt to recover from error using stored recovery data"""
        if not self.recovery_data:
            logger.info(f"No recovery data available for {self.operation_name}")
            return

        logger.info(f"Attempting recovery for {self.operation_name}...")
        try:
            # Different recovery strategies based on operation type
            if self.operation_name == "dxf_processing":
                self._recover_dxf_processing()
            elif self.operation_name == "vertex_sharing":
                self._recover_geometric_operation()
            elif self.operation_name == "tree_construction":
                self._recover_tree_operation()
            else:
                self._generic_recovery()

            logger.info(f"Recovery successful for {self.operation_name}")
            return True

        except Exception as recovery_error:
            logger.error(f"Recovery failed for {self.operation_name}: {str(recovery_error)}")
            return False

    def _recover_dxf_processing(self):
        """Recovery strategy for DXF processing failures"""
        if 'entities' in self.recovery_data:
            # Save partially processed entities
            partial_entities = self.recovery_data['entities']
            recovery_file = f"recovery_{self.operation_name}_{int(time.time())}.json"

            with open(recovery_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'operation': self.operation_name,
                    'partial_entities': partial_entities,
                    'error_context': self.error.context if hasattr(self.error, 'context') else {}
                }, f, indent=2)

            logger.info(f"Partial results saved to {recovery_file}")

            # Suggest fallback processing
            if hasattr(self.error, 'algorithm_mode'):
                fallback_mode = (self.error.algorithm_mode % 3) + 1
                logger.info(f"Suggested fallback: Try algorithm mode {fallback_mode}")

    def _recover_geometric_operation(self):
        """Recovery strategy for geometric algorithm failures"""
        if 'intermediate_results' in self.recovery_data:
            # Save intermediate results that were successfully processed
            results = self.recovery_data['intermediate_results']

            # Reduce problem size for retry
            if 'entity_count' in self.recovery_data:
                original_count = self.recovery_data['entity_count']
                if original_count > 1000:
                    # Suggest processing in chunks
                    logger.info(f"Processing {original_count} entities - consider splitting into smaller chunks")

        # Suggest algorithm mode change
        if hasattr(self.error, 'algorithm_mode'):
            current_mode = self.error.algorithm_mode
            fallback_modes = [m for m in [1, 2, 3] if m != current_mode]
            logger.info(f"Suggested fallback modes: {fallback_modes}")

    def _recover_tree_operation(self):
        """Recovery strategy for tree construction failures"""
        if 'partial_tree' in self.recovery_data:
            # Save partial tree structure
            partial_tree = self.recovery_data['partial_tree']
            recovery_file = f"tree_recovery_{int(time.time())}.json"

            with open(recovery_file, 'w') as f:
                json.dump(partial_tree, f, indent=2)

            logger.info(f"Partial tree structure saved to {recovery_file}")

        # Suggest simplification
        if hasattr(self.error, 'node_count') and self.error.node_count > 10000:
            logger.warning("Large tree detected - consider simplifying geometry or increasing memory limits")

    def _generic_recovery(self):
        """Generic recovery strategy"""
        # Save recovery context
        recovery_context = {
            'operation': self.operation_name,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(self.error).__name__ if self.error else 'Unknown',
            'recovery_data_keys': list(self.recovery_data.keys())
        }

        recovery_file = f"generic_recovery_{int(time.time())}.json"
        with open(recovery_file, 'w') as f:
            json.dump(recovery_context, f, indent=2)

        logger.info(f"Generic recovery context saved to {recovery_file}")

    def get_recovery_data(self) -> Dict[str, Any]:
        """Get recovery data after operation"""
        return self.recovery_data.copy()

    def is_successful(self) -> bool:
        """Check if operation was successful"""
        return self.success
