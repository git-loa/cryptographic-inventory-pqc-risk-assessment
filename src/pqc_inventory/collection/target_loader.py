"""Load and validate domain names and IP addresses from a target file."""

from pathlib import Path

from pqc_inventory.collection.tls_utils import validate_target
from pqc_inventory.utils.logger import get_logger

logger = get_logger(__name__)


def load_targets(path: str | Path) -> list[str]:
    """
    Load, validate, and normalize targets from a text file.

    The file should contain one domain name or IP address per line.
    Blank lines and comments beginning with '#' are ignored.

    Args:
        path: Path to the target file.

    Returns:
        A list of validated, normalized target strings in file order.

    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If a target is invalid or the file contains no targets.
        OSError: If the file cannot be read.
    """
    file_path = Path(path)
    targets: list[str] = []

    try:
        with file_path.open(mode="r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                target = line.strip()

                # Ignore blank lines and comment
                if not target or target.startswith("#"):
                    continue

                try:
                    _, normalized_target = validate_target(target)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid target in '{file_path}' "
                        f"at line {line_number}: {target!r}. {exc}"
                    ) from exc
                targets.append(normalized_target)
    except OSError as exc:
        logger.error("Unable to read target file '%s': %s", file_path, exc)
        raise

    if not targets:
        raise ValueError(
            f"No valid targets found in '{file_path}'. "
            "Add at least one domain name or IP address."
        )

    logger.info("Loaded %d targets from '%s'.", len(targets), file_path)

    return targets
