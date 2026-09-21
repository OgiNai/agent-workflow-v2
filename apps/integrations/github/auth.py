"""GitHub authentication configuration and request headers."""

from __future__ import annotations

# from dataclasses import dataclass

# from pydantic import SecretStr

# from apps.core.settings import get_auth_settings

GITHUB_API_VERSION = "2026-03-10"
GITHUB_ACCEPT_HEADER = "application/vnd.github+json"

'''
@dataclass(frozen=True)
class GitHubAuth:
    """Authentication data required for GitHub API requests."""

    token: SecretStr

    @classmethod
    def from_settings(cls) -> "GitHubAuth":
        """Create GitHub authentication from application settings."""
        return cls(token=get_auth_settings().github_token)

    def build_headers(self) -> dict[str, str]:
        """Build authenticated GitHub API request headers."""
        return {
            "Accept": GITHUB_ACCEPT_HEADER,
            "Authorization": f"Bearer {self.token.get_secret_value()}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
'''
