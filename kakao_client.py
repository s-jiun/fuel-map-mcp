"""
Kakao API 클라이언트 모듈

- address_to_coords: 주소/장소명 → (x, y) 좌표 변환
- get_directions: Kakao Mobility Directions API로 경로 조회
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

KAKAO_REST_API_KEY = os.environ["KAKAO_REST_API_KEY"]

_LOCAL_BASE = "https://dapi.kakao.com/v2/local"
_NAVI_BASE = "https://apis-navi.kakaomobility.com/v1"

_HEADERS_LOCAL = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
_HEADERS_NAVI = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}


async def address_to_coords(query: str) -> dict[str, float]:
    """
    주소 또는 장소명 문자열을 Kakao Local API로 좌표(x, y)로 변환합니다.

    먼저 주소 검색을 시도하고, 결과가 없으면 키워드 검색으로 폴백합니다.

    Returns:
        {"x": float(경도), "y": float(위도), "name": str}

    Raises:
        ValueError: 좌표를 찾을 수 없는 경우
    """
    async with httpx.AsyncClient() as client:
        # 1) 주소 검색
        resp = await client.get(
            f"{_LOCAL_BASE}/search/address.json",
            headers=_HEADERS_LOCAL,
            params={"query": query},
        )
        resp.raise_for_status()
        data = resp.json()
        documents = data.get("documents", [])

        if documents:
            doc = documents[0]
            return {
                "x": float(doc["x"]),
                "y": float(doc["y"]),
                "name": doc.get("address_name", query),
            }

        # 2) 키워드(장소명) 검색으로 폴백
        resp = await client.get(
            f"{_LOCAL_BASE}/search/keyword.json",
            headers=_HEADERS_LOCAL,
            params={"query": query},
        )
        resp.raise_for_status()
        data = resp.json()
        documents = data.get("documents", [])

        if documents:
            doc = documents[0]
            return {
                "x": float(doc["x"]),
                "y": float(doc["y"]),
                "name": doc.get("place_name", query),
            }

    raise ValueError(f"좌표를 찾을 수 없습니다: '{query}'")


async def get_directions(
    origin_x: float,
    origin_y: float,
    destination_x: float,
    destination_y: float,
    priority: str = "RECOMMEND",
) -> dict:
    """
    Kakao Mobility Directions API로 경로를 조회합니다.

    Args:
        origin_x: 출발지 경도 (WGS84)
        origin_y: 출발지 위도 (WGS84)
        destination_x: 목적지 경도
        destination_y: 목적지 위도
        priority: RECOMMEND | TIME | DISTANCE (기본: RECOMMEND)

    Returns:
        {
            "distance": int (m),
            "duration": int (초),
            "fare": {"taxi": int, "toll": int},
            "route_vertexes": list[float],  # [x1, y1, x2, y2, ...]
        }

    Raises:
        httpx.HTTPStatusError: API 호출 실패
        ValueError: 경로를 찾을 수 없는 경우
    """
    params = {
        "origin": f"{origin_x},{origin_y}",
        "destination": f"{destination_x},{destination_y}",
        "priority": priority,
        "summary": "false",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_NAVI_BASE}/directions",
            headers=_HEADERS_NAVI,
            params=params,
        )
        resp.raise_for_status()

    data = resp.json()
    routes = data.get("routes", [])

    if not routes:
        raise ValueError("경로 데이터가 없습니다.")

    route = routes[0]
    result_code = route.get("result_code", -1)
    if result_code != 0:
        raise ValueError(
            f"경로 찾기 실패 (result_code={result_code}): {route.get('result_msg', '')}"
        )

    summary = route["summary"]

    # sections 내 모든 roads의 vertexes를 합쳐서 반환
    vertexes: list[float] = []
    for section in route.get("sections", []):
        for road in section.get("roads", []):
            vertexes.extend(road.get("vertexes", []))

    return {
        "distance": summary["distance"],
        "duration": summary["duration"],
        "fare": summary.get("fare", {"taxi": 0, "toll": 0}),
        "route_vertexes": vertexes,
    }
