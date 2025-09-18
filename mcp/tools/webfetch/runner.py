import re, requests
from bs4 import BeautifulSoup

def run(action: str, payload: dict):
    if action != "fetch":
        return {"error":"unknown action"}
    url = (payload or {}).get("url","").strip()
    if not url.startswith("http"):
        return {"error":"invalid url"}
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent":"mcp-map/1.0"})
        html = resp.text or ""
        title = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
        title = title.group(1).strip() if title else ""
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = " ".join(soup.get_text(" ", strip=True).split())
            snippet = text[:500]
        except Exception:
            snippet = html[:500]
        return {"title": title, "snippet": snippet, "status": resp.status_code}
    except Exception as e:
        return {"error": f"request_failed: {e}"}
