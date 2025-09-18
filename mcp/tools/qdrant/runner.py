from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
import uuid, json, re

client = QdrantClient(url="http://localhost:6333")

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")

def _coerce_id(v):
    # 정수면 통과
    if isinstance(v, int):
        return v
    # UUID 문자열이면 통과
    if isinstance(v, str) and UUID_RE.match(v):
        return v
    # URL/임의 문자열이면 UUID5로 안정 변환
    if isinstance(v, str):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, v))
    # 그 외엔 새 UUID
    return str(uuid.uuid4())

def _coerce_vector(v):
    # 이미 리스트면 그대로
    if isinstance(v, list):
        return v
    # 문자열 처리
    if isinstance(v, str):
        t = v.strip()
        # 템플릿 미평가 방지(개발 안전망)
        if t.startswith("{{") and t.endswith("}}"):
            return [0.0] * 384
        # JSON처럼 보이면 파싱
        if (t.startswith("[") and t.endswith("]")) or (t.startswith("{") and t.endswith("}")):
            try:
                return json.loads(t)
            except Exception:
                pass
        # 쉼표/공백 숫자열을 리스트로 강제 파싱 시도
        try:
            nums = [float(x) for x in re.split(r"[,\s]+", t.strip("[] ")) if x]
            if nums:
                return nums
        except Exception:
            pass
    # 마지막 안전망: 차원 384 더미(개발 모드)
    return [0.0] * 384

def _ensure_collection(coll: str, dim: int):
    try:
        client.get_collection(coll)
        return
    except Exception:
        pass
    client.recreate_collection(
        collection_name=coll,
        vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
    )

def _upsert_points(coll: str, points: list):
    qpoints = []
    for p in points:
        vec = _coerce_vector(p["vector"])
        pid = _coerce_id(p.get("id"))
        qpoints.append(qm.PointStruct(id=pid, vector=vec, payload=p.get("payload", {})))

    dim = len(qpoints[0].vector) if isinstance(qpoints[0].vector, list) else 1
    try:
        _ensure_collection(coll, dim)
        client.upsert(collection_name=coll, points=qpoints)
    except Exception:
        # 차원 불일치 시 재생성 후 재시도
        client.recreate_collection(
            collection_name=coll,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )
        client.upsert(collection_name=coll, points=qpoints)
    return {"status": "ok"}

def run(action: str, payload: dict):
    payload = (payload or {})
    if action == "upsert":
        coll = payload["collection"]
        points = payload.get("points")
        if points is None and "point" in payload:
            points = [payload["point"]]
        if not points:
            return {"error": "missing points"}
        return _upsert_points(coll, points)

    elif action == "query":
        coll   = payload["collection"]
        vector = _coerce_vector(payload["vector"])
        limit  = int(payload.get("limit", 3))
        hits = client.search(
            collection_name=coll,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )
        return {
            "hits": [
                {
                    "id": str(getattr(h, "id", "")),
                    "score": float(getattr(h, "score", 0.0)),
                    "payload": getattr(h, "payload", {}) or {},
                } for h in hits
            ]
        }
    return {"error": "unknown action"}
