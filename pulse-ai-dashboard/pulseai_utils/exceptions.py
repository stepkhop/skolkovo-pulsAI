from __future__ import annotations

class PulseAIError(Exception):
    pass

class ConfigurationError(PulseAIError):
    pass

class DataCollectionError(PulseAIError):
    pass

class APIError(DataCollectionError):
    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url

class ValidationError(PulseAIError):
    pass

class StorageError(PulseAIError):
    pass