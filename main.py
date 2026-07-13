"""
fuel-map-mcp: 출발지-목적지 경로 찾기 및 주유소 검색 MCP 서버

제공 도구:
  - get_route: 출발지/목적지 텍스트를 받아 Kakao Mobility로 경로를 반환합니다.
  - find_cheapest_gas_stations_nearby: 특정 좌표 근처의 최저가 주유소를 찾습니다.
  - find_cheapest_gas_stations_on_route: 경로상의 최저가 주유소를 찾습니다.
"""

import os
from mcp.server.fastmcp import FastMCP
from src.kakao_client import address_to_coords, get_directions
from src.opinet_client import get_nearby_gas_stations
from src.utils import filter_coordinates_by_interval

mcp = FastMCP("fuel-map-mcp")


@mcp.tool(
    annotations={
        "title": "Get Route Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
async def get_route(
    origin: str,
    destination: str,
    priority: str = "RECOMMEND",
) -> dict:
    """
    Retrieves route information between origin and destination using Fuel Map MCP(연료지도).

    This tool queries Kakao Mobility API to get detailed route information including distance, duration, tolls, and route coordinates.

    Args:
        origin: Starting location address or place name (e.g., "Gangnam Station", "Seoul Gangnam-gu Teheran-ro 212")
        destination: Destination address or place name (e.g., "Pangyo Station")
        priority: Route priority - RECOMMEND | TIME | DISTANCE (default: RECOMMEND)

    Returns:
        distance_km: Total distance in kilometers (1 decimal place)
        duration_min: Estimated travel time in minutes
        toll_fare: Toll fees in KRW
        taxi_fare: Estimated taxi fare in KRW
        origin_coords: Origin coordinates {"x": float, "y": float, "name": str}
        destination_coords: Destination coordinates {"x": float, "y": float, "name": str}
        route_vertexes: Route coordinate list [x1, y1, x2, y2, ...] (WGS84)
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


@mcp.tool(
    annotations={
        "title": "Find Cheapest Gas Stations Nearby",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
async def find_cheapest_gas_stations_nearby(
    location: str,
    fuel_type: str = "B027",
    radius: int = 1000,
) -> dict:
    """
    Finds the 5 cheapest gas stations near a specific location using Fuel Map MCP(연료지도).

    This tool searches for gas stations within the specified radius using Opinet API and returns the top 5 cheapest options sorted by price.

    Args:
        location: Location address or place name (e.g., "Gangnam Station", "Seoul Gangnam-gu Teheran-ro 212")
        fuel_type: Fuel type code - B027: Gasoline(default), D047: Diesel, K015: Kerosene, C004: LPG
        radius: Search radius in meters (max 5000, default: 1000)

    Returns:
        location: Search location info (name, coordinates)
        gas_stations: Top 5 cheapest gas stations [
            {
                "name": Station name,
                "brand": Brand name,
                "price": Price in KRW,
                "distance": Distance from search location in meters,
                "x": Longitude,
                "y": Latitude
            },
            ...
        ]
        total_found: Total number of gas stations found
    """
    # 1) 위치 문자열 → 좌표 변환
    location_coords = await address_to_coords(location)

    # 2) 주유소 검색
    stations = await get_nearby_gas_stations(
        x=location_coords["x"],
        y=location_coords["y"],
        radius=min(radius, 5000),
        fuel_type=fuel_type,
        sort=1,
    )

    # 3) 가격 기준 정렬 (이미 sort=1로 정렬되지만 명시적으로)
    stations.sort(key=lambda s: s["price"])

    # 4) 최저가 5곳 선택
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
        "location": location_coords,
        "gas_stations": cheapest_stations,
        "total_found": len(stations),
    }


@mcp.tool(
    annotations={
        "title": "Find Cheapest Gas Stations on Route",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
async def find_cheapest_gas_stations_on_route(
    origin: str,
    destination: str,
    fuel_type: str = "B027",
    priority: str = "RECOMMEND",
) -> dict:
    """
    Finds the 5 cheapest gas stations along a route using Fuel Map MCP(연료지도).

    Samples the route and searches for gas stations within 1km radius at each point, returning the top 5 cheapest options.

    Args:
        origin: Starting location (e.g., "Gangnam Station")
        destination: Destination (e.g., "Pangyo Station")
        fuel_type: B027(Gasoline), D047(Diesel), K015(Kerosene), C004(LPG)
        priority: RECOMMEND | TIME | DISTANCE (default: RECOMMEND)

    Returns:
        route_info: Route details (distance_km, duration_min, coordinates)
        gas_stations: Top 5 cheapest stations with name, brand, price, distance, coordinates
        sampled_points_count: Number of sampled points
        total_stations_found: Total stations found
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
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)  # type: ignore
