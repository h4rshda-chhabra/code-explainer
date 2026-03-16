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
        '.html', '.css', '.md', '.java', 
        '.cpp', '.c', '.go', '.rs', '.Dockerfile', 'Dockerfile'
    }
    
    # Exclude common large/build directories that shouldn't be indexed to save time and token space
    excluded_dirs = {'node_modules', '.git', 'dist', 'build', '__pycache__', 'venv', '.next', '.vscode'}
    
    files_to_process = []
    
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            file_lower = file.lower()
            if any(file_lower.endswith(ext.lower()) for ext in allowed_extensions) or file_lower == 'dockerfile':
                files_to_process.append(os.path.join(root, file))
    
    return files_to_process
