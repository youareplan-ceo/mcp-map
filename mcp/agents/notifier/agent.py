def run(task: str, payload: dict | None = None):
    if task=="summary_to_slack":
        print("🔔 [Notifier] Summary payload:", payload)
        return {"status":"sent"}
    return {"error":"unknown task"}
