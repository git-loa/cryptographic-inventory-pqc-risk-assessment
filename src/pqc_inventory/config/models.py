"""Application configuration models."""

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceDirectories(BaseModel):
    """Define workspace directory names."""

    model_config = ConfigDict(extra="forbid")

    evidence: str = Field(default="evidence", min_length=1)
    assessments: str = Field(default="assessments", min_length=1)
    reports: str = Field(default="reports", min_length=1)
    logs: str = Field(default="logs", min_length=1)


class WorkspaceConfig(BaseModel):
    """Define workspace configuration."""

    model_config = ConfigDict(extra="forbid")

    directories: WorkspaceDirectories = WorkspaceDirectories()
