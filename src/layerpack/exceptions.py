class LambdaBundlerError(Exception):
    """Base exception for all lambda-bundler errors."""

    pass


class PackageNotFoundError(LambdaBundlerError):
    """Raised when a package cannot be found in PyPI."""

    pass


class IncompatibleRuntimeError(LambdaBundlerError):
    """Raised when a package is incompatible with the Lambda runtime."""

    pass


class LayerSizeLimitError(LambdaBundlerError):
    """Raised when the layer exceeds the size limit."""

    pass


class DependencyConflictError(LambdaBundlerError):
    """Raised when there are conflicting package dependencies."""

    pass


class ConfigurationError(LambdaBundlerError):
    """Raised when there's an invalid configuration setting."""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.message = message
        self.config_key = config_key
