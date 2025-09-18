import os, sys, json, datetime, textwrap

try:
    import requests  # 슬랙 웹훅용 (없으면 콘솔로만 동작)
except Exception:
    requests = None

LOG_PATH = os.path.join("logs", "notifier.log")
WEBHOOK  = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

def _log(line: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _post_slack(text: str):
    if not WEBHOOK or not requests:
        return False
    try:
        resp = requests.post(WEBHOOK, json={"text": text}, timeout=5)
        return (200 <= resp.status_code < 300)
    except Exception:
        return False

def _format_summary(payload: dict) -> str:
    title = payload.get("title") or "알림"
    items = payload.get("items")
    note  = payload.get("note")
    lines = [f"*{title}*  ({_now()})"]
    if isinstance(items, list) and items:
        for it in items[:50]:
            lines.append(f"• {it}")
        if len(items) > 50:
            lines.append(f"… (+{len(items)-50} more)")
    if note:
        lines.append("")
        lines.append(textwrap.dedent(str(note)).strip())
    return "\n".join(lines)

def run(action: str, payload: dict):
    """
    actions:
      - notify.summary {title, items[list[str]], note}
      - notify.signal  {ticker, signal, price, rsi, atr}
    """
    if action == "notify.summary":
        msg = _format_summary(payload or {})
    elif action == "notify.signal":
        t = payload.get("ticker","-")
        sig = payload.get("signal","-")
        price = payload.get("price")
        rsi = payload.get("rsi")
        atr = payload.get("atr")
        msg = f"[{_now()}] {t} | signal={sig} | price={price} | rsi={rsi} | atr%={atr}"
    else:
        return {"ok": False, "error": f"unknown action: {action}"}

    # 콘솔 + 파일
    print(msg, flush=True)
    _log(msg)

    # 슬랙(있으면)
    sent = _post_slack(msg)
    return {"ok": True, "sent_to_slack": bool(sent), "logged": True}

if __name__ == "__main__":
    action = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(json.dumps(run(action, payload), ensure_ascii=False))
