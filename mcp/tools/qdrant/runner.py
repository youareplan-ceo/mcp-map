import os, json, uuid
import requests

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()

def _headers():
    h = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        h["api-key"] = QDRANT_API_KEY
    return h

def _coerce_id(val):
    """URL 같은 문자열을 UUID로 변환"""
    if isinstance(val, str):
        try:
            return str(uuid.UUID(val))
        except Exception:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, val))
    return str(val)

def run(tool, action, args):
    if tool != "qdrant":
        return {"error": f"unsupported tool {tool}"}

    collection = args.get("collection", "mcp_docs")

    # upsert
    if action == "upsert":
        point = args.get("point") or args.get("points")
        if not point:
            return {"error": "missing point/points"}
        # 단일 포인트를 리스트로 감쌈
        if "id" in point and "vector" in point:
            pts = [point]
        else:
            pts = point

        # id 보정
        for p in pts:
            if "id" in p:
                p["id"] = _coerce_id(p["id"])
        data = {"points": pts}
        r = requests.put(f"{QDRANT_URL}/collections/{collection}/points", headers=_headers(), data=json.dumps(data))
        return r.json()

    # query
    if action == "query":
        vector = args.get("vector")
        if not vector:
            return {"error": "missing vector"}
        payload = {
            "vector": vector,
            "limit": args.get("limit", 3),
            "with_payload": True
        }
        r = requests.post(f"{QDRANT_URL}/collections/{collection}/points/search", headers=_headers(), data=json.dumps(payload))
        return {"hits": r.json().get("result", [])}

    # 기본 응답
    return {"status": "ok"}from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
<<<<<<< Updated upstream
import uuid, json, re

client = QdrantClient(url="http://localhost:6333")

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
=======
import uuid, json

client = QdrantClient(url="http://localhost:6333")

def _coerce_vector(v):
    """문자열로 넘어온 벡터를 안전하게 리스트로 변환.
       - JSON 문자열([0.1, ...])이면 json.loads
       - 템플릿 미평가('{{ ... }}')면 더미 벡터 반환(스캐폴딩용)
    """
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        t = v.strip()
        # 템플릿이 그대로 들어온 경우: 더미 벡터
        if t.startswith("{{") and t.endswith("}}"):
            return [0.0]*384  # DEV dummy to match model dim
        # JSON으로 보이면 파싱
        if (t.startswith("[") and t.endswith("]")) or (t.startswith("{") and t.endswith("}")):
            try:
                return json.loads(t)
            except Exception:
                pass
    return v

def run(action: str, payload: dict):
    payload = payload or {}
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        points = payload.get("points")
        if points is None and "point" in payload:
            points = [payload["point"]]
        if not points:
            return {"error": "missing points"}
        return _upsert_points(coll, points)
=======
        points = payload["points"]  # [{"vector":[...]/"json-string"/"{{...}}", "payload":{...}}, ...]

        # 벡터 차원 확인(첫 포인트 기준, 필요시 새 컬렉션 생성/재생성)
        vec0 = _coerce_vector(points[0]["vector"])
        dim = len(vec0) if isinstance(vec0, list) else 1

        # 컬렉션 없으면 생성, 있으면 그대로 사용
        try:
            client.get_collection(coll)
        except Exception:
            client.recreate_collection(
                collection_name=coll,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )

        qpoints = [
            qm.PointStruct(
                id=str(uuid.uuid4()),
                vector=_coerce_vector(p["vector"]),
                payload=p.get("payload", {})
            )
            for p in points
        ]
        client.upsert(collection_name=coll, points=qpoints)
        return {"status": "ok"}
>>>>>>> Stashed changes

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
