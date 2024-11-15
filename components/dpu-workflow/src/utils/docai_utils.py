import re
from typing import Optional, Tuple


def is_valid_processor_id(processor_id: str) -> Optional[Tuple[str, str, str]]:
    """
    Validates a GCP DocumentAI processor ID.

    Args:
      processor_id: The processor ID string to validate.

    Returns:
      Tuple (project_id, location, processor_id) if the processor ID is valid, False otherwise.
    """
    pattern = r"^projects\/([a-z][a-z0-9\-]{4,28}[a-z0-9])\/locations\/(us|eu)\/processors\/([a-zA-Z0-9_-]+)$"
    match = re.match(pattern, processor_id)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)
