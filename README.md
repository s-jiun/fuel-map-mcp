# fuel-map-mcp

국내 여행 경로 상에서 가장 저렴한 주유소를 찾아주는 MCP 서버입니다.

> **아이디어**: "서울에서 부산까지 가는 길에 기름이 떨어져가는데, 어디서 주유하는 게 가장 쌀까?"

카카오 내비게이션 API로 경로를 받아오고, 오피넷 API로 수집한 전국 주유소 가격 데이터와 PostGIS 공간 쿼리를 결합하여 **경로에서 가장 가깝고 저렴한 주유소**를 찾아줍니다.

## 아키텍처

```
[사용자 검색: "서울→부산 최저가 주유소"]
                │
                ▼
    ┌─────────────────────────┐
    │   카카오 내비게이션 API    │
    │   출발지 → 도착지 경로     │
    │   polyline + waypoint    │
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │      PostGIS DB          │
    │                          │
    │  매일 새벽 배치:           │
    │  오피넷 API → 전국 주유소   │
    │  가격 + 위치 적재          │
    │                          │
    │  공간 쿼리:               │
    │  ST_DWithin(             │
    │    경로 polyline,         │
    │    주유소 좌표,            │
    │    500m                  │
    │  )                       │
    │  → 최저가 상위 N개         │
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │        응답 (MCP)         │
    │                          │
    │  • 주유소명 / 브랜드        │
    │  • 휘발유 / 경유 가격        │
    │  • 경로 이탈 거리 (m)       │
    │  • 카카오맵 재탐색 딥링크     │
    └─────────────────────────┘
```

## License

This project is proprietary software.

**Copyright (c) 2026 서지운 and 정보성**

All rights reserved.

Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of the copyright holders.

For licensing inquiries, please contact the copyright holders.
