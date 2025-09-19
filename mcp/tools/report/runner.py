import os, json, duckdb

DB = os.getenv("SP_DB_PATH", "data/stock_signals.duckdb")

def _latest_grants_run(con, applicant_id=None):
    if applicant_id:
        row = con.execute("""
          SELECT gm.run_id
          FROM grant_matches gm
          WHERE gm.applicant_id=?
          ORDER BY gm.run_id DESC
          LIMIT 1
        """, [applicant_id]).fetchone()
    else:
        row = con.execute("""
          SELECT run_id
          FROM runs_grants
          ORDER BY ts_epoch DESC
          LIMIT 1
        """).fetchone()
    return row[0] if row else None

def run(action, payload):
    con = duckdb.connect(DB, read_only=True)
    try:
        if action == "grants.summary":
            applicant_id = payload.get("applicant_id")
            limit = int(payload.get("limit", 10))
            run_id = payload.get("run_id") or _latest_grants_run(con, applicant_id)
            if not run_id:
                return {"ok": False, "error": "no grants run found"}

            rows = con.execute("""
              SELECT gm.grant_id, g.title, gm.score, gm.reason
              FROM grant_matches gm
              LEFT JOIN grants g ON g.grant_id = gm.grant_id
              WHERE gm.run_id = ?
              ORDER BY gm.score DESC, gm.grant_id
              LIMIT ?
            """, [run_id, limit]).fetchall()

            items = [f"{r[0]} {r[1]} — 점수 {int(r[2])} / {r[3]}" for r in rows]
            title = payload.get("title") or f"Grants — 매칭 결과 요약 (run {run_id})"
            note = payload.get("note", "")

            return {
              "ok": True,
              "title": title,
              "items": items,
              "note": note,
              "run_id": run_id,
              "count": len(items)
            }

        return {"ok": False, "error": f"unknown action {action}"}
    finally:
        con.close()

# CLI 사용: python runner.py grants.summary '{"applicant_id":"APP001","limit":5}'
if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else None
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = run(action, payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))
