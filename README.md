# fuel-map-mcp

국내 여행 경로 상에서 가장 저렴한 주유소를 찾아주는 MCP 서버입니다.

> **아이디어**: "서울에서 부산까지 가는 길에 기름이 떨어져가는데, 어디서 주유하는 게 가장 쌀까?"

카카오 내비게이션 API로 경로를 받아오고, 오피넷 API를 실시간으로 조회하여 **경로상에서 가장 저렴한 주유소 5곳**을 찾아줍니다.

## 주요 기능

- **경로 조회**: 출발지와 목적지를 입력하면 Kakao Mobility API로 최적 경로 계산
- **최저가 주유소 검색**: 경로를 2km 간격으로 샘플링하여 각 지점에서 1km 반경 내 주유소를 검색하고 최저가 5곳 반환
- **좌표계 변환**: WGS84 ↔ KATEC 자동 변환으로 정확한 위치 검색
- **다양한 유종 지원**: 휘발유, 경유, 등유, LPG

## 아키텍처

```
[사용자: "강남역→판교역 최저가 주유소"]
                │
                ▼
    ┌─────────────────────────────┐
    │  카카오 Local API             │
    │  주소/장소명 → WGS84 좌표 변환  │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  카카오 Mobility API          │
    │  경로 조회 (거리, 시간, 좌표)    │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  경로 샘플링                   │
    │  2km 간격으로 좌표 추출         │
    │  (Haversine 거리 계산)         │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  Opinet API (실시간)          │
    │                              │
    │  각 샘플링 지점마다:            │
    │  • WGS84 → KATEC 변환         │
    │  • 1km 반경 내 주유소 검색      │
    │  • 가격순 정렬                 │
    │  • 중복 제거                  │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │  응답 (MCP Tool)              │
    │                              │
    │  • 경로 정보 (거리, 시간)        │
    │  • 최저가 주유소 5곳:           │
    │    - 주유소명 / 브랜드          │
    │    - 가격 (원)                │
    │    - 경로 지점으로부터 거리 (m)  │
    │    - 좌표 (WGS84)             │
    └─────────────────────────────┘
```

## 설치 및 실행

### 환경 변수 설정

`.env` 파일에 API 키를 설정합니다:

```bash
KAKAO_REST_API_KEY=your_kakao_api_key
OPINET_API_KEY=your_opinet_api_key
```

### 로컬 실행

```bash
# 의존성 설치
uv sync

# MCP 서버 실행
python main.py
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t fuel-map-mcp .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env fuel-map-mcp
```

## MCP Tools

### 1. get_route

출발지와 목적지를 입력받아 경로 정보를 반환합니다.

**Parameters:**
- `origin` (str): 출발지 주소 또는 장소명
- `destination` (str): 목적지 주소 또는 장소명
- `priority` (str, optional): 경로 우선순위 (RECOMMEND, TIME, DISTANCE)

**Returns:**
- 거리 (km)
- 소요시간 (분)
- 통행료, 택시 요금
- 출발지/목적지 좌표
- 경로 좌표 목록

### 2. find_cheapest_gas_stations_on_route

경로상의 최저가 주유소 5곳을 찾습니다.

**Parameters:**
- `origin` (str): 출발지 주소 또는 장소명
- `destination` (str): 목적지 주소 또는 장소명
- `fuel_type` (str, optional): 유종 코드
  - `B027`: 휘발유 (기본값)
  - `D047`: 경유
  - `K015`: 등유
  - `C004`: LPG
- `priority` (str, optional): 경로 우선순위

**Returns:**
- 경로 정보 (거리, 시간, 출발/도착지)
- 최저가 주유소 5곳 (이름, 브랜드, 가격, 거리, 좌표)
- 샘플링된 지점 수
- 발견된 총 주유소 수

## 기술 스택

- **Python 3.13+**
- **FastMCP**: MCP 서버 프레임워크
- **httpx**: 비동기 HTTP 클라이언트
- **pyproj**: 좌표계 변환 (WGS84 ↔ KATEC)
- **python-dotenv**: 환경 변수 관리

## API 출처

- [Kakao Maps API](https://developers.kakao.com/)
- [Kakao Mobility API](https://developers.kakaomobility.com/)
- [Opinet API](https://www.opinet.co.kr/)

## License

This project is proprietary software.

**Copyright (c) 2026 서지운 and 정보성**

All rights reserved.

Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of the copyright holders.

For licensing inquiries, please contact the copyright holders.
