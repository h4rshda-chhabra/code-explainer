"""GitHub Ingestor — Downloads public repositories via GitHub API zipball for fast indexing."""

import io
import os
import re
import shutil
import stat
import tempfile
import zipfile
from typing import List

import requests


def _handle_remove_readonly(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def _parse_github_url(url: str):
    """Extract (owner, repo) from a GitHub URL."""
    url = url.rstrip("/").removesuffix(".git")
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError(f"Could not parse GitHub URL: {url}")
    return match.group(1), match.group(2)


class GitHubIngestor:
    """Downloads public GitHub repos as zip archives for fast code indexing."""

    def __init__(self) -> None:
        self.cloned_dirs: List[str] = []

    def clone_repo(self, repo_url: str) -> str:
        """Download a GitHub repository as a zip and extract to a temp directory."""
        try:
            owner, repo = _parse_github_url(repo_url)
        except ValueError as e:
            raise RuntimeError(str(e))

        token = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token and token != "placeholder":
            headers["Authorization"] = f"Bearer {token}"

        zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        print(f"Downloading {owner}/{repo} via GitHub API...")

        try:
            resp = requests.get(zip_url, headers=headers, timeout=60, stream=True)
        except requests.exceptions.Timeout:
            raise RuntimeError("Download timed out. The repository may be too large.")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Network error: {e}")

        if resp.status_code == 404:
            raise RuntimeError("Repository not found. Check the URL or ensure it is public.")
        if resp.status_code == 401:
            raise RuntimeError("Authentication failed. Set a valid GITHUB_TOKEN for private repos.")
        if resp.status_code != 200:
            raise RuntimeError(f"GitHub API error {resp.status_code}.")

        # Stream zip into memory then extract
        zip_bytes = io.BytesIO(resp.content)
        temp_dir = tempfile.mkdtemp(prefix="codesense_")
        self.cloned_dirs.append(temp_dir)

        try:
            with zipfile.ZipFile(zip_bytes) as zf:
                # GitHub zips wrap everything in a top-level dir like owner-repo-sha/
                names = zf.namelist()
                prefix = names[0].split("/")[0] + "/" if names else ""
                for member in names:
                    # Strip the top-level prefix so files land directly in temp_dir
                    rel = member[len(prefix):]
                    if not rel:
                        continue
                    dest = os.path.join(temp_dir, rel)
                    if member.endswith("/"):
                        os.makedirs(dest, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with zf.open(member) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
        except zipfile.BadZipFile:
            self.cleanup_dir(temp_dir)
            raise RuntimeError("Downloaded file is not a valid zip archive.")

        return temp_dir

    def cleanup_dir(self, dir_path: str) -> None:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, onerror=_handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to cleanup {dir_path}: {e}")

    def __del__(self) -> None:
        for directory in self.cloned_dirs:
            self.cleanup_dir(directory)
