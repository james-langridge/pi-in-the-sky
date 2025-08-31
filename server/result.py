"""Result type for functional error handling."""

from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable, Union

T = TypeVar('T')
E = TypeVar('E')


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    Immutable Result type for handling success/failure without exceptions.
    
    Follows functional programming pattern to define errors out of existence.
    """
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        """Create a successful result."""
        return Result(_value=value, _error=None)
    
    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        """Create a failed result."""
        return Result(_value=None, _error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self._error is None
    
    @property
    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return self._error is not None
    
    @property
    def value(self) -> T:
        """
        Get the success value.
        Raises ValueError if result is a failure.
        """
        if self.is_failure:
            raise ValueError(f"Cannot get value from failed result: {self._error}")
        return self._value
    
    @property
    def error(self) -> E:
        """
        Get the error value.
        Raises ValueError if result is successful.
        """
        if self.is_success:
            raise ValueError("Cannot get error from successful result")
        return self._error
    
    def value_or(self, default: T) -> T:
        """Get value or return default if failure."""
        return self._value if self.is_success else default
    
    def map(self, func: Callable[[T], T]) -> 'Result[T, E]':
        """
        Apply function to success value, pass through failures.
        Pure functional transformation.
        """
        if self.is_success:
            return Result.success(func(self._value))
        return self
    
    def flat_map(self, func: Callable[[T], 'Result[T, E]']) -> 'Result[T, E]':
        """
        Apply function that returns Result, flattening the result.
        Useful for chaining operations that might fail.
        """
        if self.is_success:
            return func(self._value)
        return self
    
    def map_error(self, func: Callable[[E], E]) -> 'Result[T, E]':
        """Transform error value if present."""
        if self.is_failure:
            return Result.failure(func(self._error))
        return self
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.
        Useful for API responses.
        """
        if self.is_success:
            return {
                "success": True,
                "value": self._value
            }
        return {
            "success": False,
            "error": str(self._error)
        }


# Convenience type aliases for common error types
StringResult = Result[T, str]