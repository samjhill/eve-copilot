"""
Enhanced error handling and recovery system for EVE Copilot
"""

import logging
import traceback
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Type
from enum import Enum
import functools
import asyncio

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ErrorCategory(Enum):
    """Error categories for better handling."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    PARSING = "parsing"
    TTS = "tts"
    MEMORY = "memory"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


class ErrorRecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    IGNORE = "ignore"
    SHUTDOWN = "shutdown"


class ErrorInfo:
    """Information about an error."""
    
    def __init__(self, error: Exception, severity: ErrorSeverity, 
                 category: ErrorCategory, context: Dict[str, Any] = None):
        self.error = error
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.timestamp = datetime.now()
        self.retry_count = 0
        self.recovery_strategy = self._determine_recovery_strategy()
    
    def _determine_recovery_strategy(self) -> ErrorRecoveryStrategy:
        """Determine recovery strategy based on error type and severity."""
        if self.severity == ErrorSeverity.CRITICAL:
            return ErrorRecoveryStrategy.SHUTDOWN
        
        if self.category == ErrorCategory.NETWORK:
            return ErrorRecoveryStrategy.RETRY
        
        if self.category == ErrorCategory.TTS:
            return ErrorRecoveryStrategy.FALLBACK
        
        if self.category == ErrorCategory.FILE_SYSTEM:
            return ErrorRecoveryStrategy.RETRY
        
        if self.severity == ErrorSeverity.HIGH:
            return ErrorRecoveryStrategy.RESTART
        
        return ErrorRecoveryStrategy.IGNORE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'error_type': type(self.error).__name__,
            'error_message': str(self.error),
            'severity': self.severity.name,
            'category': self.category.name,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'retry_count': self.retry_count,
            'recovery_strategy': self.recovery_strategy.name
        }


class ErrorHandler:
    """Enhanced error handling and recovery system."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize error handler.
        
        Args:
            max_retries: Maximum number of retries for retryable errors
            retry_delay: Base delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_history: List[ErrorInfo] = []
        self.recovery_callbacks: Dict[ErrorRecoveryStrategy, List[Callable]] = {
            strategy: [] for strategy in ErrorRecoveryStrategy
        }
        self.error_counters: Dict[str, int] = {}
        self.last_error_time: Optional[datetime] = None
        
        # Setup default recovery callbacks
        self._setup_default_recovery_callbacks()
    
    def _setup_default_recovery_callbacks(self):
        """Setup default recovery callbacks."""
        self.add_recovery_callback(ErrorRecoveryStrategy.RETRY, self._default_retry_handler)
        self.add_recovery_callback(ErrorRecoveryStrategy.FALLBACK, self._default_fallback_handler)
        self.add_recovery_callback(ErrorRecoveryStrategy.RESTART, self._default_restart_handler)
        self.add_recovery_callback(ErrorRecoveryStrategy.SHUTDOWN, self._default_shutdown_handler)
    
    def add_recovery_callback(self, strategy: ErrorRecoveryStrategy, callback: Callable):
        """Add a recovery callback for a specific strategy.
        
        Args:
            strategy: Recovery strategy
            callback: Callback function to execute
        """
        self.recovery_callbacks[strategy].append(callback)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    severity: ErrorSeverity = None, category: ErrorCategory = None) -> bool:
        """Handle an error with automatic recovery.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            severity: Error severity (auto-detected if None)
            category: Error category (auto-detected if None)
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            # Auto-detect severity and category if not provided
            if severity is None:
                severity = self._detect_severity(error)
            if category is None:
                category = self._detect_category(error)
            
            # Create error info
            error_info = ErrorInfo(error, severity, category, context)
            self.error_history.append(error_info)
            self.last_error_time = datetime.now()
            
            # Update error counters
            error_key = f"{type(error).__name__}_{category.name}"
            self.error_counters[error_key] = self.error_counters.get(error_key, 0) + 1
            
            # Log the error
            self._log_error(error_info)
            
            # Execute recovery strategy
            return self._execute_recovery_strategy(error_info)
            
        except Exception as e:
            logger.critical(f"Error in error handler: {e}")
            return False
    
    def _detect_severity(self, error: Exception) -> ErrorSeverity:
        """Auto-detect error severity based on error type."""
        error_type = type(error).__name__
        
        critical_errors = ['MemoryError', 'SystemExit', 'KeyboardInterrupt']
        high_errors = ['OSError', 'IOError', 'PermissionError', 'FileNotFoundError']
        medium_errors = ['ValueError', 'TypeError', 'AttributeError']
        
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _detect_category(self, error: Exception) -> ErrorCategory:
        """Auto-detect error category based on error type and message."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if error_type in ['ConnectionError', 'TimeoutError', 'URLError']:
            return ErrorCategory.NETWORK
        elif error_type in ['FileNotFoundError', 'PermissionError', 'OSError', 'IOError']:
            return ErrorCategory.FILE_SYSTEM
        elif 'config' in error_message or 'yaml' in error_message:
            return ErrorCategory.CONFIGURATION
        elif 'tts' in error_message or 'speech' in error_message:
            return ErrorCategory.TTS
        elif 'parse' in error_message or 'regex' in error_message:
            return ErrorCategory.PARSING
        elif error_type == 'MemoryError':
            return ErrorCategory.MEMORY
        else:
            return ErrorCategory.UNKNOWN
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level."""
        log_message = f"{error_info.category.name} error: {error_info.error}"
        
        if error_info.context:
            log_message += f" (Context: {error_info.context})"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=True)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _execute_recovery_strategy(self, error_info: ErrorInfo) -> bool:
        """Execute the appropriate recovery strategy."""
        try:
            strategy = error_info.recovery_strategy
            callbacks = self.recovery_callbacks.get(strategy, [])
            
            if not callbacks:
                logger.warning(f"No recovery callbacks for strategy: {strategy}")
                return False
            
            # Execute all callbacks for this strategy
            for callback in callbacks:
                try:
                    result = callback(error_info)
                    if result:
                        logger.info(f"Recovery successful using strategy: {strategy}")
                        return True
                except Exception as e:
                    logger.error(f"Recovery callback failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing recovery strategy: {e}")
            return False
    
    def _default_retry_handler(self, error_info: ErrorInfo) -> bool:
        """Default retry handler."""
        if error_info.retry_count >= self.max_retries:
            logger.warning(f"Max retries exceeded for {type(error_info.error).__name__}")
            return False
        
        error_info.retry_count += 1
        delay = self.retry_delay * (2 ** (error_info.retry_count - 1))  # Exponential backoff
        
        logger.info(f"Retrying in {delay:.1f}s (attempt {error_info.retry_count}/{self.max_retries})")
        time.sleep(delay)
        return True
    
    def _default_fallback_handler(self, error_info: ErrorInfo) -> bool:
        """Default fallback handler."""
        logger.info(f"Attempting fallback for {error_info.category.name} error")
        
        # For TTS errors, try switching to a different engine
        if error_info.category == ErrorCategory.TTS:
            logger.info("Switching to fallback TTS engine")
            # This would be implemented by the TTS system
            return True
        
        return False
    
    def _default_restart_handler(self, error_info: ErrorInfo) -> bool:
        """Default restart handler."""
        logger.warning(f"Restarting component due to {error_info.category.name} error")
        # This would be implemented by the component that needs restarting
        return True
    
    def _default_shutdown_handler(self, error_info: ErrorInfo) -> bool:
        """Default shutdown handler."""
        logger.critical(f"Shutting down due to critical {error_info.category.name} error")
        # This would trigger application shutdown
        return True
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        if not self.error_history:
            return {}
        
        # Count errors by category and severity
        category_counts = {}
        severity_counts = {}
        
        for error_info in self.error_history:
            category_counts[error_info.category.name] = category_counts.get(error_info.category.name, 0) + 1
            severity_counts[error_info.severity.name] = severity_counts.get(error_info.severity.name, 0) + 1
        
        # Recent errors (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_errors = [e for e in self.error_history if e.timestamp > recent_cutoff]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'category_counts': category_counts,
            'severity_counts': severity_counts,
            'error_counters': self.error_counters,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
        }
    
    def clear_old_errors(self, max_age_hours: int = 24):
        """Clear old errors from history."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        self.error_history = [e for e in self.error_history if e.timestamp > cutoff]
        logger.info(f"Cleared errors older than {max_age_hours} hours")


def error_handler(severity: ErrorSeverity = None, category: ErrorCategory = None, 
                 context: Dict[str, Any] = None):
    """Decorator for automatic error handling.
    
    Args:
        severity: Error severity level
        category: Error category
        context: Additional context
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler from the instance if available
                error_handler_instance = None
                if args and hasattr(args[0], 'error_handler'):
                    error_handler_instance = args[0].error_handler
                
                if error_handler_instance:
                    error_handler_instance.handle_error(e, context, severity, category)
                else:
                    logger.error(f"Unhandled error in {func.__name__}: {e}", exc_info=True)
                
                raise
        
        return wrapper
    return decorator


def async_error_handler(severity: ErrorSeverity = None, category: ErrorCategory = None,
                       context: Dict[str, Any] = None):
    """Decorator for automatic async error handling."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler from the instance if available
                error_handler_instance = None
                if args and hasattr(args[0], 'error_handler'):
                    error_handler_instance = args[0].error_handler
                
                if error_handler_instance:
                    error_handler_instance.handle_error(e, context, severity, category)
                else:
                    logger.error(f"Unhandled async error in {func.__name__}: {e}", exc_info=True)
                
                raise
        
        return wrapper
    return decorator
