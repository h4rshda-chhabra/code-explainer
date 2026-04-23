import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("devops-assistant")

def get_allowed_files(directory: str):
    allowed_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', 
        '.sh', '.yml', '.yaml', '.json', 
        '.html', '.css', '.md', '.txt', 
        '.java', '.cpp', '.c', '.go', '.rs', '.sql',
        '.jsonl', '.toml', '.xml', '.props', '.properties', 
        '.gradle', '.gradle.kts', '.pom', '.xml.config',
        '.svg', '.config', '.env.example', '.dockerignore', 
        '.gitignore', 'Dockerfile', 'dockerfile', 'Makefile', 'makefile'
    }
    
    # Exclude common large/build directories that shouldn't be indexed
    excluded_dirs = {
        'node_modules', '.git', 'dist', 'build', '__pycache__', 
        'venv', 'env', '.next', '.vscode'
    }
    
    files_to_process = []
    
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            file_lower = file.lower()
            is_allowed = any(file_lower.endswith(ext.lower()) for ext in allowed_extensions)
            
            if is_allowed:
                files_to_process.append(os.path.abspath(os.path.join(root, file)))
            else:
                logger.debug(f"Skipping file {file} - extension not allowed")
    
    return files_to_process
