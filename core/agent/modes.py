from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModeConfig:
    slug: str
    name: str
    role_definition: str
    description: str


# Define available modes
MODES: List[ModeConfig] = [
    ModeConfig(
        slug="general",
        name="General",
        role_definition="You are ZIVA, an Elite Autonomous AI Assistant. "
                        "You are helpful, precise, and resourceful.",
        description="General purpose assistant for answering questions and "
                    "helping with various tasks."
    ),
    ModeConfig(
        slug="architect",
        name="Architect",
        role_definition="You are ZIVA (Architect Mode). You are an expert "
                        "Software Architect. Focus on high-level design, "
                        "system patterns, file structure, and creating clear "
                        "implementation plans. Do not write implementation code "
                        "unless necessary for specific examples.",
        description="Focuses on design, planning, and system architecture."
    ),
    ModeConfig(
        slug="coder",
        name="Coder",
        role_definition="You are ZIVA (Coder Mode). You are an expert Senior "
                        "Software Engineer. Focus on writing clean, efficient, "
                        "and bug-free code. You follow best practices, write "
                        "tests, and debug issues relentlessly.",
        description="Focuses on writing code, debugging, and implementation."
    )
]


def get_mode_by_slug(slug: str) -> Optional[ModeConfig]:
    """Retrieves a mode configuration by its slug."""
    for mode in MODES:
        if mode.slug == slug:
            return mode
    return None
