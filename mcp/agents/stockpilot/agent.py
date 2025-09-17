def run(task: str, payload: dict | None = None):
    if task=="research":
        return {
            "title":"Daily Market Research",
            "points":["Top movers (demo)","Earnings today (demo)","Macro highlights (demo)"]
        }
    elif task=="signal":
        return {"signal":"HOLD","rationale":"Insufficient edge (demo)"}
    return {"error":"unknown task"}
