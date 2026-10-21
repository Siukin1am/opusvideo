from ..config import Settings
from .base import MediaProvider


def get_provider(settings: Settings) -> MediaProvider:
    if settings.media_provider == "mock":
        from .mock import MockProvider
        return MockProvider()
    if settings.media_provider == "replicate":
        from .replicate import ReplicateProvider
        return ReplicateProvider(settings)
    raise ValueError(f"Unknown media provider: {settings.media_provider!r}")


__all__ = ["MediaProvider", "get_provider"]
