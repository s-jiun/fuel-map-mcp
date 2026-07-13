"""
Opinet API 클라이언트 모듈

- get_nearby_gas_stations: 좌표 기반 반경 내 주유소 검색
"""

import os
import httpx
from dotenv import load_dotenv
from src.utils import wgs84_to_katec, katec_to_wgs84

load_dotenv()

OPINET_API_KEY = os.environ["OPINET_API_KEY"]

_OPINET_BASE = "https://www.opinet.co.kr/api"


async def get_nearby_gas_stations(
    x: float,
    y: float,
    radius: int = 1000,
    fuel_type: str = "B027",
    sort: int = 1,
) -> list[dict]:
    """
    Opinet API로 좌표 기반 반경 내 주유소 목록을 조회합니다.

    Args:
        x: 경도 (WGS84)
        y: 위도 (WGS84)
        radius: 검색 반경 (미터, 최대 5000)
        fuel_type: 유종 코드 (B027: 휘발유, D047: 경유, K015: 등유, C004: LPG)
        sort: 정렬 방법 (1: 가격순, 2: 거리순)

    Returns:
        [
            {
                "station_id": str,
                "brand": str,
                "name": str,
                "price": int,
                "distance": float,
                "x": float,
                "y": float,
            },
            ...
        ]

    Raises:
        httpx.HTTPStatusError: API 호출 실패
    """
    # WGS84 -> KATEC 변환
    katec_x, katec_y = wgs84_to_katec(x, y)

    params = {
        "code": OPINET_API_KEY,  # 'code' 파라미터 사용 (certkey 아님!)
        "out": "json",
        "x": str(katec_x),
        "y": str(katec_y),
        "radius": str(radius),
        "prodcd": fuel_type,
        "sort": str(sort),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_OPINET_BASE}/aroundAll.do",
            params=params,
        )
        resp.raise_for_status()

    data = resp.json()
    result = data.get("RESULT", {})
    oil_list = result.get("OIL", [])

    if not oil_list:
        return []

    stations = []
    for station in oil_list:
        try:
            price_str = station.get("PRICE")
            if not price_str or price_str == "-":
                continue

            # KATEC 좌표를 WGS84로 변환
            katec_x = float(station.get("GIS_X_COOR", 0))
            katec_y = float(station.get("GIS_Y_COOR", 0))
            wgs84_x, wgs84_y = katec_to_wgs84(katec_x, katec_y)

            stations.append(
                {
                    "station_id": station.get("UNI_ID", ""),
                    "brand": station.get("POLL_DIV_CD", ""),
                    "name": station.get("OS_NM", ""),
                    "price": int(price_str),
                    "distance": float(station.get("DISTANCE", 0)),
                    "x": wgs84_x,
                    "y": wgs84_y,
                }
            )
        except (ValueError, TypeError):
            continue

    return stations