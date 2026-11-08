"""
Application configuration models.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceDirectories(BaseModel):
    """Define workspace directory names."""

    model_config = ConfigDict(extra="forbid")

    evidence: str = Field(default="evidence", min_length=1)
    assessments: str = Field(default="assessments", min_length=1)
    reports: str = Field(default="reports", min_length=1)
    logs: str = Field(default="logs", min_length=1)

    @field_validator("evidence", "assessments", "reports", "logs")
    @classmethod
    def validate_directory_name(cls, value: str) -> str:
        """Ensure directory names cannot escape the workspace."""

        invalid_conditions = (
            value in {".", ".."},
            "/" in value,
            "\\" in value,
            ":" in value,
            "\x00" in value,
            value != value.strip(),
            value.endswith("."),
        )

        if any(invalid_conditions):
            raise ValueError(
                "Directory names must be simple names, not filesystem paths."
            )

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }

        if value.split(".", maxsplit=1)[0].upper() in reserved_names:
            raise ValueError("Directory name is reserved by the operating system.")

        return value


class WorkspaceConfig(BaseModel):
    """Define workspace configuration."""

    model_config = ConfigDict(extra="forbid")

    directories: WorkspaceDirectories = WorkspaceDirectories()
