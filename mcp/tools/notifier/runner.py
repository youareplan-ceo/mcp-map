import json, sys

def run(action, payload):
    if action == "notify.summary":
        title = payload.get("title", "Notification")
        items = payload.get("items", [])
        note = payload.get("note", "")
        # 실제로는 Slack/Webhook/메일 전송 코드가 들어갈 자리
        return {
            "ok": True,
            "sent": {
                "title": title,
                "items": items,
                "note": note
            }
        }
    return {"ok": False, "error": f"unknown action {action}"}

if __name__ == "__main__":
    action = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = run(action, payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))
