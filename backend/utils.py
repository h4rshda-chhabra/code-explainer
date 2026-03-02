import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("devops-assistant")

def get_allowed_files(directory: str):
    allowed_extensions = {'.py', '.js', '.sh', '.yml', '.yaml', '.Dockerfile', 'Dockerfile'}
    files_to_process = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in allowed_extensions) or file == 'Dockerfile':
                files_to_process.append(os.path.join(root, file))
    
    return files_to_process
