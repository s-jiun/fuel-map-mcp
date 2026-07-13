"""
유틸리티 함수 모듈

- calculate_distance: 두 좌표 간 거리 계산 (Haversine 공식)
- filter_coordinates_by_interval: 경로 좌표에서 일정 간격으로 샘플링
- wgs84_to_katec: WGS84 좌표를 KATEC 좌표로 변환
- katec_to_wgs84: KATEC 좌표를 WGS84 좌표로 변환
"""

import math
from pyproj import Transformer


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Haversine 공식으로 두 WGS84 좌표 간 거리를 계산합니다.

    Args:
        x1: 첫 번째 지점 경도
        y1: 첫 번째 지점 위도
        x2: 두 번째 지점 경도
        y2: 두 번째 지점 위도

    Returns:
        거리 (미터)
    """
    # 지구 반지름 (미터)
    R = 6371000

    # 라디안 변환
    lat1 = math.radians(y1)
    lat2 = math.radians(y2)
    delta_lat = math.radians(y2 - y1)
    delta_lon = math.radians(x2 - x1)

    # Haversine 공식
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def filter_coordinates_by_interval(
    vertexes: list[float], interval_meters: float = 2000
) -> list[tuple[float, float]]:
    """
    경로 좌표 목록에서 100개당 1개씩 샘플링합니다.

    Args:
        vertexes: [x1, y1, x2, y2, ...] 형식의 좌표 배열
        interval_meters: 사용하지 않음 (하위 호환성을 위해 유지)

    Returns:
        [(x1, y1), (x2, y2), ...] 형식의 필터링된 좌표 목록
    """
    if not vertexes or len(vertexes) < 2:
        return []

    # 좌표 쌍으로 변환
    coords = [(vertexes[i], vertexes[i + 1]) for i in range(0, len(vertexes), 2)]

    if not coords:
        return []

    # 100개당 1개씩 샘플링 (첫 번째와 마지막은 항상 포함)
    filtered = [coords[0]]

    # 중간 좌표들을 100개 간격으로 샘플링
    for i in range(100, len(coords) - 1, 100):
        filtered.append(coords[i])

    # 마지막 좌표는 항상 포함 (이미 포함되어 있지 않다면)
    if len(coords) > 1 and coords[-1] != filtered[-1]:
        filtered.append(coords[-1])

    return filtered


# WGS84 -> KATEC 변환기 (성능 최적화를 위해 전역 변수로 생성)
_WGS84_TO_KATEC = Transformer.from_proj(
    "epsg:4326",  # WGS84
    "+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 +x_0=400000 +y_0=600000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43",  # KATEC
    always_xy=True,
)

# KATEC -> WGS84 변환기
_KATEC_TO_WGS84 = Transformer.from_proj(
    "+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 +x_0=400000 +y_0=600000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43",  # KATEC
    "epsg:4326",  # WGS84
    always_xy=True,
)


def wgs84_to_katec(lon: float, lat: float) -> tuple[float, float]:
    """
    WGS84 좌표(경도, 위도)를 KATEC 좌표로 변환합니다.

    Args:
        lon: 경도 (WGS84)
        lat: 위도 (WGS84)

    Returns:
        (x, y) KATEC 좌표 (미터 단위)
    """
    x, y = _WGS84_TO_KATEC.transform(lon, lat)
    return x, y


def katec_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """
    KATEC 좌표를 WGS84 좌표(경도, 위도)로 변환합니다.

    Args:
        x: KATEC X 좌표 (미터)
        y: KATEC Y 좌표 (미터)

    Returns:
        (lon, lat) WGS84 좌표
    """
    lon, lat = _KATEC_TO_WGS84.transform(x, y)
    return lon, lat