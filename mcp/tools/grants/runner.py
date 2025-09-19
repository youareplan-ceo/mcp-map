import os, sys, json, time, uuid, csv, duckdb

DB = os.getenv("SP_DB_PATH", "data/stock_signals.duckdb")

def _load_catalog_csv(path: str):
    rows=[]
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append({
                "grant_id": r.get("grant_id","").strip(),
                "title": r.get("title","").strip(),
                "amount_min": float(r.get("amount_min") or 0),
                "amount_max": float(r.get("amount_max") or 0),
                "region": (r.get("region") or "").strip(),
                "industry": (r.get("industry") or "").strip(),
                "requires_clean_tax": str(r.get("requires_clean_tax","")).strip().upper() in ("1","TRUE","YES","Y"),
            })
    return rows

def _upsert_applicant(con, a):
    con.execute("""
      INSERT OR REPLACE INTO applicants(applicant_id,name,region,industry,has_tax_arrears)
      VALUES (?,?,?,?,?)
    """, [a["applicant_id"], a["name"], a["region"], a["industry"], bool(a.get("has_tax_arrears", False))])

def _score_match(applicant, grant, desired_amount=None):
    # 규칙 기반 간단 점수(설명 포함)
    score = 0
    reasons = []

    # 필수 탈락 조건: 체납 + 청렴 요구
    if applicant.get("has_tax_arrears") and grant["requires_clean_tax"]:
        reasons.append("세금 체납 → 해당 사업은 청렴 요건 필수")
        return -999, "; ".join(reasons)  # hard fail

    # 지역 매칭 (KR/All 은 전국)
    ar = (applicant.get("region") or "").upper()
    gr = (grant["region"] or "").upper()
    if gr in ("", "ALL", "KR") or ar == gr:
        score += 40
        reasons.append("지역 적합")
    else:
        reasons.append("지역 불일치(감점 없음/검토 필요)")

    # 업종 매칭 (All 허용)
    ai = (applicant.get("industry") or "").upper()
    gi = (grant["industry"] or "").upper()
    if gi in ("", "ALL") or ai == gi:
        score += 40
        reasons.append("업종 적합")
    else:
        reasons.append("업종 불일치(감점 없음/검토 필요)")

    # 금액 범위 선호(선택값)
    if desired_amount is not None:
        if grant["amount_min"] <= desired_amount <= grant["amount_max"]:
            score += 20
            reasons.append("희망 금액 범위 적합")
        else:
            reasons.append("희망 금액 범위 벗어남(감점 없음/조건 검토)")

    return score, "; ".join(reasons)

def run(action, payload):
    con = duckdb.connect(DB)
    try:
        if action == "ingest.catalog":
            path = payload.get("path", "data/grants.sample.csv")
            rows = _load_catalog_csv(path)
            n = 0
            for r in rows:
                con.execute("""
                  INSERT OR REPLACE INTO grants(grant_id,title,amount_min,amount_max,region,industry,requires_clean_tax)
                  VALUES (?,?,?,?,?,?,?)
                """, [r["grant_id"], r["title"], r["amount_min"], r["amount_max"], r["region"], r["industry"], r["requires_clean_tax"]])
                n += 1
            return {"ok": True, "inserted": n, "source": path}

        if action == "applicant.upsert":
            a = {
                "applicant_id": payload.get("applicant_id") or f"app_{uuid.uuid4().hex[:8]}",
                "name": payload.get("name", ""),
                "region": payload.get("region", "KR"),
                "industry": payload.get("industry", "All"),
                "has_tax_arrears": bool(payload.get("has_tax_arrears", False)),
            }
            _upsert_applicant(con, a)
            return {"ok": True, "applicant": a}

        if action == "match.run":
            # 입력
            applicant_id = payload.get("applicant_id")
            if not applicant_id:
                return {"ok": False, "error": "applicant_id required"}
            limit = int(payload.get("limit", 50))
            desired_amount = payload.get("desired_amount")  # optional

            # 실행 기록
            run_id = f"gr_{int(time.time())}"
            con.execute("INSERT OR REPLACE INTO runs_grants(run_id, ts_epoch) VALUES (?,?)",
                        [run_id, int(time.time())])

            # 신청자 불러오기
            a = con.execute("SELECT applicant_id,name,region,industry,has_tax_arrears FROM applicants WHERE applicant_id=?",
                            [applicant_id]).fetchone()
            if not a:
                return {"ok": False, "error": f"applicant not found: {applicant_id}"}
            applicant = dict(zip(["applicant_id","name","region","industry","has_tax_arrears"], a))

            # 전체 그랜트 불러와 매칭/점수
            grants = con.execute("""
              SELECT grant_id,title,amount_min,amount_max,region,industry,requires_clean_tax
              FROM grants
            """).fetchall()
            cols = ["grant_id","title","amount_min","amount_max","region","industry","requires_clean_tax"]

            results = []
            for g in grants:
                grant = dict(zip(cols, g))
                score, reason = _score_match(applicant, grant, desired_amount=desired_amount)
                if score <= -999:
                    # 탈락(청렴 요건 미충족)
                    continue
                results.append({
                    "grant_id": grant["grant_id"],
                    "title": grant["title"],
                    "score": float(score),
                    "reason": reason
                })

            # 점수 순으로 정렬 후 상위 N개만 기록
            results.sort(key=lambda x: x["score"], reverse=True)
            chosen = results[:limit]

            for r in chosen:
                con.execute("""
                  INSERT INTO grant_matches(run_id, applicant_id, grant_id, score, reason)
                  VALUES (?,?,?,?,?)
                """, [run_id, applicant_id, r["grant_id"], r["score"], r["reason"]])

            return {"ok": True, "run_id": run_id, "applicant_id": applicant_id, "matches": chosen}

        return {"ok": False, "error": f"unknown action {action}"}
    finally:
        con.close()

# CLI entrypoint (python runner.py <action> '<json-payload>')
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: python runner.py <action> '<json-payload>'"}))
        sys.exit(1)
    action = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = run(action, payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))
