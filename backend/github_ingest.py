import os
import shutil
import stat
import tempfile
from typing import List

from git import Repo

def handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to safely remove read-only files on Windows."""
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

class GitHubIngestor:
    def __init__(self) -> None:
        """Initialize the GitHub ingestor to track temporary cloned directories."""
        self.cloned_dirs: List[str] = []

    def clone_repo(self, repo_url: str) -> str:
        """Clones a GitHub repository to a temporary directory for processing."""
        temp_dir = tempfile.mkdtemp(prefix="codesense_")
        self.cloned_dirs.append(temp_dir)
        
        print(f"Cloning {repo_url} into {temp_dir}...")
        try:
            # depth=1 performs a shallow clone, which is significantly faster and saves local disk space
            Repo.clone_from(repo_url, temp_dir, depth=1)
            
            # Immediately delete the .git folder to save space and skip indexing unnecessary git histories
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                self.cleanup_dir(git_dir)
                
            return temp_dir
        except Exception as e:
            self.cleanup_dir(temp_dir)
            raise RuntimeError(f"Failed to clone repository: {str(e)}")

    def cleanup_dir(self, dir_path: str) -> None:
        """Safely deletes a temporary directory."""
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, onerror=handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to cleanup {dir_path}: {e}")

    def __del__(self) -> None:
        """Ensure all stored cloned repositories are deleted when object is garbage collected."""
        for directory in self.cloned_dirs:
            self.cleanup_dir(directory)
