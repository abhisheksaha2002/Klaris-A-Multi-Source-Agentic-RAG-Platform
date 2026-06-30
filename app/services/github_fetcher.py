from github import Github
from typing import List, Dict
from app.config import settings

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".html", ".css",
    ".java", ".go", ".rs", ".cpp", ".c", ".h", ".sh", ".env.example"
}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv"}


def fetch_github_repo(repo_url: str) -> List[Dict[str, str]]:
    repo_path = _extract_repo_path(repo_url)
    g = Github(settings.github_token) if settings.github_token else Github()
    repo = g.get_repo(repo_path)

    documents = []
    contents_queue = list(repo.get_contents(""))

    while contents_queue:
        item = contents_queue.pop(0)
        if item.type == "dir":
            if item.name not in SKIP_DIRS:
                contents_queue.extend(repo.get_contents(item.path))
            continue
        if not _is_text_file(item.path):
            continue
        try:
            text = item.decoded_content.decode("utf-8")
            if text.strip():
                documents.append({"content": text, "path": item.path})
        except Exception:
            pass

    return documents


def _extract_repo_path(url: str) -> str:
    path = url.rstrip("/").split("github.com/")[-1]
    parts = path.split("/")
    return f"{parts[0]}/{parts[1]}"


def _is_text_file(file_path: str) -> bool:
    return any(file_path.endswith(ext) for ext in TEXT_EXTENSIONS)
