"""GitHub integration exceptions."""

from __future__ import annotations


class GitHubIntegrationError(Exception):
    """Base exception for GitHub integration failures."""


class GitHubAuthenticationError(GitHubIntegrationError):
    """Raised when GitHub authentication is invalid or unavailable."""


class GitHubAuthorizationError(GitHubIntegrationError):
    """Raised when GitHub access is authenticated but insufficient."""


class GitHubAPIError(GitHubIntegrationError):
    """Raised when GitHub returns an unexpected API failure."""
