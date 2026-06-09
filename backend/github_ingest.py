"""GitHub Ingestor — Clones public repositories for code indexing."""

import os
import shutil
import stat
import tempfile
from typing import List

# pyrefly: ignore [missing-import]
from git import Repo


def _handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to remove read-only files on Windows."""
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


class GitHubIngestor:
    """Clones public GitHub repos into temporary directories for processing."""

    def __init__(self) -> None:
        self.cloned_dirs: List[str] = []

    def clone_repo(self, repo_url: str) -> str:
        """Clone a GitHub repository (shallow) and return the temp directory path."""
        temp_dir = tempfile.mkdtemp(prefix="codesense_")
        self.cloned_dirs.append(temp_dir)

        print(f"Cloning {repo_url} into {temp_dir}...")
        try:
            Repo.clone_from(repo_url, temp_dir, depth=1)

            # Remove .git folder to save space and avoid indexing git internals
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                self.cleanup_dir(git_dir)

            return temp_dir
        except Exception as e:
            self.cleanup_dir(temp_dir)
            error_msg = str(e).lower()

            if any(kw in error_msg for kw in ("not found", "authentication", "could not read", "fatal: repository")):
                raise RuntimeError(
                    "Cannot access repository. Ensure the URL is correct "
                    "and the repository is public (private repos are not supported)."
                )
            raise RuntimeError(f"Failed to clone repository: {e}")

    def cleanup_dir(self, dir_path: str) -> None:
        """Safely delete a directory, handling read-only files on Windows."""
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, onerror=_handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to cleanup {dir_path}: {e}")

    def __del__(self) -> None:
        """Clean up all cloned directories on garbage collection."""
        for directory in self.cloned_dirs:
            self.cleanup_dir(directory)
