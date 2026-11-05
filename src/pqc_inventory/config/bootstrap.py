"""Application workspace initialization."""

from pathlib import Path

from pqc_inventory.config.loader import load_config, validate_config
from pqc_inventory.config.models import WorkspaceConfig
from pqc_inventory.config.paths import BASE_DIR
from pqc_inventory.config.workspace import Workspace


def initialize_workspace(base_dir: Path = BASE_DIR) -> Workspace:
    """Initialize and return a configured application workspace."""

    # Install default configuration files.
    initial_workspace = Workspace(base_dir=base_dir)
    initial_workspace.install_default_configs()

    # Load application configuration.
    config_path = initial_workspace.config_dir / "config.yaml"
    configuration = load_config(config_path)

    # Validate workspace configuration.
    workspace_config = validate_config(
        configuration.get("workspace", {}),
        WorkspaceConfig,
    )

    # Construct and create the configured workspace.
    workspace = Workspace.from_config(
        workspace_config,
        base_dir=base_dir,
    )

    workspace.create()

    return workspace
