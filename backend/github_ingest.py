import os
import tempfile
import shutil
from git import Repo

class GitHubIngestor:
    def __init__(self):
        # We will use the system's temp directory
        self.cloned_dirs = []

    def clone_repo(self, repo_url: str) -> str:
        """Clones a GitHub repository to a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="codesense_")
        self.cloned_dirs.append(temp_dir)
        
        print(f"Cloning {repo_url} into {temp_dir}...")
        try:
            # depth=1 performs a shallow clone, which is significantly faster 
            Repo.clone_from(repo_url, temp_dir, depth=1)
            
            # Immediately delete the .git folder to save space and indexing time
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                self.cleanup_dir(git_dir)
                
            return temp_dir
        except Exception as e:
            # Clean up immediately if clone fails
            self.cleanup_dir(temp_dir)
            raise RuntimeError(f"Failed to clone repository: {str(e)}")

    def cleanup_dir(self, dir_path: str):
        """Deletes the temporary directory."""
        try:
            if os.path.exists(dir_path):
                # On Windows, sometimes .git files are read-only and shutil.rmtree fails
                # Using an error handler helper
                def onerror(func, path, exc_info):
                    import stat
                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                    else:
                        raise
                        
                shutil.rmtree(dir_path, onerror=onerror)
        except Exception as e:
            print(f"Warning: Failed to cleanup {dir_path}: {e}")

    def __del__(self):
        # Try to clean up stored directories when destroyed
        for d in self.cloned_dirs:
            self.cleanup_dir(d)
