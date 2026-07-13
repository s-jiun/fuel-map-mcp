"""
fuel-map-mcp: 출발지-목적지 경로 찾기 및 주유소 검색 MCP 서버

제공 도구:
  - get_route: 출발지/목적지 텍스트를 받아 Kakao Mobility로 경로를 반환합니다.
  - find_cheapest_gas_stations_nearby: 특정 좌표 근처의 최저가 주유소를 찾습니다.
  - find_cheapest_gas_stations_on_route: 경로상의 최저가 주유소를 찾습니다.
"""

from mcp.server.fastmcp import FastMCP
from src.kakao_client import address_to_coords, get_directions
from src.opinet_client import get_nearby_gas_stations
from src.utils import filter_coordinates_by_interval

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


@mcp.tool()
async def find_cheapest_gas_stations_nearby(
    x: float,
    y: float,
    fuel_type: str = "B027",
    radius: int = 1000,
) -> dict:
    """
    특정 좌표 근처의 최저가 주유소 5곳을 찾습니다.

    Args:
        x: 경도 (WGS84)
        y: 위도 (WGS84)
        fuel_type: 유종 코드 — B027: 휘발유(기본), D047: 경유, K015: 등유, C004: LPG
        radius: 검색 반경 (미터, 최대 5000, 기본: 1000)

    Returns:
        location: 검색 위치 좌표
        gas_stations: 최저가 주유소 5곳 [
            {
                "name": 주유소명,
                "brand": 브랜드,
                "price": 가격(원),
                "distance": 검색 위치로부터 거리(m),
                "x": 경도,
                "y": 위도
            },
            ...
        ]
        total_found: 발견된 총 주유소 수
    """
    # 1) 주유소 검색
    stations = await get_nearby_gas_stations(
        x=x, y=y, radius=min(radius, 5000), fuel_type=fuel_type, sort=1
    )

    # 2) 가격 기준 정렬 (이미 sort=1로 정렬되지만 명시적으로)
    stations.sort(key=lambda s: s["price"])

    # 3) 최저가 5곳 선택
    cheapest_stations = [
        {
            "name": station["name"],
            "brand": station["brand"],
            "price": station["price"],
            "distance": station["distance"],
            "x": station["x"],
            "y": station["y"],
        }
        for station in stations[:5]
    ]

    return {
        "location": {"x": x, "y": y},
        "gas_stations": cheapest_stations,
        "total_found": len(stations),
    }


@mcp.tool()
async def find_cheapest_gas_stations_on_route(
    origin: str,
    destination: str,
    fuel_type: str = "B027",
    priority: str = "RECOMMEND",
) -> dict:
    """
    경로상의 최저가 주유소 5곳을 찾습니다.

    경로를 2km 간격으로 샘플링하여 각 지점에서 1km 반경 내 주유소를 검색하고,
    전체 중 최저가 주유소 5곳을 반환합니다.

    Args:
        origin: 출발지 주소 또는 장소명 (예: "강남역")
        destination: 목적지 주소 또는 장소명 (예: "판교역")
        fuel_type: 유종 코드 — B027: 휘발유(기본), D047: 경유, K015: 등유, C004: LPG
        priority: 경로 우선순위 — RECOMMEND | TIME | DISTANCE (기본: RECOMMEND)

    Returns:
        route_info: 경로 정보 (distance_km, duration_min, 출발/도착지 좌표)
        gas_stations: 최저가 주유소 5곳 [
            {
                "name": 주유소명,
                "brand": 브랜드,
                "price": 가격(원),
                "distance_from_route_point": 경로 지점으로부터 거리(m),
                "x": 경도,
                "y": 위도
            },
            ...
        ]
        sampled_points_count: 샘플링된 경로 지점 수
    """
    # 1) 경로 조회
    route = await get_route(origin, destination, priority)

    # 2) 경로 좌표를 2km 간격으로 샘플링
    route_vertexes = route["route_vertexes"]
    sampled_coords = filter_coordinates_by_interval(route_vertexes, interval_meters=2000)

    # 3) 각 샘플링된 좌표에서 1km 반경 내 주유소 검색
    all_stations = []
    station_ids = set()

    for x, y in sampled_coords:
        try:
            stations = await get_nearby_gas_stations(
                x=x, y=y, radius=1000, fuel_type=fuel_type, sort=1
            )

            # 중복 제거 (같은 주유소가 여러 지점에서 검색될 수 있음)
            for station in stations:
                station_id = station["station_id"]
                if station_id not in station_ids:
                    station_ids.add(station_id)
                    all_stations.append(
                        {
                            "name": station["name"],
                            "brand": station["brand"],
                            "price": station["price"],
                            "distance_from_route_point": station["distance"],
                            "x": station["x"],
                            "y": station["y"],
                        }
                    )
        except Exception:
            # 개별 지점 검색 실패 시 무시하고 계속 진행
            continue

    # 4) 가격 기준으로 정렬하여 최저가 5곳 선택
    all_stations.sort(key=lambda s: s["price"])
    cheapest_stations = all_stations[:5]

    return {
        "route_info": {
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "origin": route["origin_coords"],
            "destination": route["destination_coords"],
        },
        "gas_stations": cheapest_stations,
        "sampled_points_count": len(sampled_coords),
        "total_stations_found": len(all_stations),
    }


if __name__ == "__main__":
    mcp.run()
