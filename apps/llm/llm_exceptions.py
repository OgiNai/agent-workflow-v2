class LLMError(RuntimeError):
    """Base exception for LLM-related errors."""


class LLMGenerationError(LLMError):
    """Raised when an LLM provider fails to generate a response."""


class LLMResponseValidationError(LLMError):
    """Raised when an LLM response cannot be validated against the expected schema."""


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is invalid."""
