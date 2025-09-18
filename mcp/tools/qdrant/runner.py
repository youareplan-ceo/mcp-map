from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
import uuid

# Qdrant 클라이언트 (로컬 도커)
client = QdrantClient(url="http://localhost:6333")

def run(action: str, payload: dict):
    payload = payload or {}

    if action == "upsert":
        coll = payload["collection"]
        points = payload["points"]  # [{"vector":[...], "payload":{...}}, ...]

        # 벡터 차원 자동 판별
        dim = len(points[0]["vector"])

        # 컬렉션이 없으면 생성, 있으면 그대로 사용
        try:
            client.get_collection(coll)
        except Exception:
            client.recreate_collection(
                collection_name=coll,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )

        # 업서트
        qpoints = [
            qm.PointStruct(
                id=str(uuid.uuid4()),
                vector=p["vector"],
                payload=p.get("payload", {})
            )
            for p in points
        ]
        client.upsert(collection_name=coll, points=qpoints)
        return {"status": "ok"}

    elif action == "query":
        coll   = payload["collection"]
        vector = payload["vector"]
        limit  = int(payload.get("limit", 3))

        # 최신 SDK 시그니처: collection_name / query_vector
        hits = client.search(
            collection_name=coll,
            query_vector=vector,
            limit=limit,
            with_payload=True
        )
        return {
            "hits": [
                {
                    "id": str(h.id),
                    "score": float(h.score),
                    "payload": h.payload or {}
                } for h in hits
            ]
        }

    else:
        return {"error": "unknown action"}
