"""Utility functions for file filtering and logging."""

import logging
import os
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("codesense")

# File extensions considered indexable code/config
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".sh", ".yml", ".yaml", ".json",
    ".html", ".css", ".md", ".txt",
    ".java", ".cpp", ".c", ".go", ".rs", ".sql",
    ".jsonl", ".toml", ".xml", ".props", ".properties",
    ".gradle", ".gradle.kts", ".pom", ".xml.config",
    ".svg", ".config", ".env.example", ".dockerignore",
    ".gitignore", "Dockerfile", "dockerfile", "Makefile", "makefile",
}

# Directories to skip during recursive file discovery
EXCLUDED_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    "venv", "env", ".next", ".vscode",
}


def get_allowed_files(
    directory: str, allowed_extensions: Optional[List[str]] = None
) -> List[str]:
    """Walk a directory tree and return paths to files with allowed extensions."""
    extensions = (
        {ext.lower() for ext in allowed_extensions}
        if allowed_extensions
        else ALLOWED_EXTENSIONS
    )

    files_to_process = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                files_to_process.append(os.path.abspath(os.path.join(root, file)))
            else:
                logger.debug(f"Skipping file {file} — extension not allowed")

    return files_to_process
