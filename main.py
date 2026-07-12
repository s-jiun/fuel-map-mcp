"""
fuel-map-mcp: 출발지-목적지 경로 찾기 MCP 서버

제공 도구:
  - get_route: 출발지/목적지 텍스트를 받아 Kakao Mobility로 경로를 반환합니다.
"""

from mcp.server.fastmcp import FastMCP
from kakao_client import address_to_coords, get_directions

mcp = FastMCP("fuel-map-mcp")


@mcp.tool()
async def get_route(
    origin: str,
    destination: str,
    priority: str = "RECOMMEND",
) -> dict:
    """
    출발지와 목적지를 입력받아 경로 정보를 반환합니다.

    Args:
        origin: 출발지 주소 또는 장소명 (예: "강남역", "서울시 강남구 테헤란로 212")
        destination: 목적지 주소 또는 장소명 (예: "판교역")
        priority: 경로 우선순위 — RECOMMEND | TIME | DISTANCE (기본: RECOMMEND)

    Returns:
        distance_km: 총 거리 (km, 소수점 1자리)
        duration_min: 예상 소요시간 (분)
        toll_fare: 통행료 (원)
        taxi_fare: 택시 예상 요금 (원)
        origin_coords: 출발지 좌표 {"x": float, "y": float, "name": str}
        destination_coords: 목적지 좌표 {"x": float, "y": float, "name": str}
        route_vertexes: 경로 좌표 목록 [x1, y1, x2, y2, ...] (WGS84)
    """
    # 1) 주소 → 좌표 변환
    origin_coords = await address_to_coords(origin)
    destination_coords = await address_to_coords(destination)

    # 2) 경로 조회
    directions = await get_directions(
        origin_x=origin_coords["x"],
        origin_y=origin_coords["y"],
        destination_x=destination_coords["x"],
        destination_y=destination_coords["y"],
        priority=priority,
    )

    fare = directions["fare"]

    return {
        "distance_km": round(directions["distance"] / 1000, 1),
        "duration_min": round(directions["duration"] / 60),
        "toll_fare": fare.get("toll", 0),
        "taxi_fare": fare.get("taxi", 0),
        "origin_coords": origin_coords,
        "destination_coords": destination_coords,
        "route_vertexes": directions["route_vertexes"],
    }


if __name__ == "__main__":
    mcp.run()
