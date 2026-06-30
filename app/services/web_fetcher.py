import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def fetch_web_page(url: str) -> List[Dict[str, str]]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; KlarisBot/1.0; +https://github.com/klaris)"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for unwanted_tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        unwanted_tag.decompose()

    raw_text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in raw_text.splitlines() if line]
    clean_text = "\n".join(lines)

    return [{"content": clean_text, "path": url}]
