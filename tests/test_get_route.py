"""
테스트: main.py (MCP get_route 도구)
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestGetRouteTool:
    """get_route MCP 도구 — kakao_client를 모킹해서 테스트"""

    @pytest.mark.asyncio
    async def test_get_route_success(self):
        """정상적인 출발지/목적지 입력 시 올바른 결과를 반환해야 한다."""
        from main import get_route

        mock_coords_gangnam = {"x": 127.0276368, "y": 37.4979502, "name": "강남역"}
        mock_coords_pangyo = {"x": 127.1119569, "y": 37.3946083, "name": "판교역"}
        mock_directions = {
            "distance": 20000,
            "duration": 2400,
            "fare": {"taxi": 22000, "toll": 0},
            "route_vertexes": [127.03, 37.49, 127.11, 37.39],
        }

        with (
            patch("main.address_to_coords", new=AsyncMock(
                side_effect=[mock_coords_gangnam, mock_coords_pangyo]
            )),
            patch("main.get_directions", new=AsyncMock(return_value=mock_directions)),
        ):
            result = await get_route("강남역", "판교역")

        assert result["distance_km"] == 20.0
        assert result["duration_min"] == 40
        assert result["toll_fare"] == 0
        assert result["taxi_fare"] == 22000
        assert result["origin_coords"]["name"] == "강남역"
        assert result["destination_coords"]["name"] == "판교역"
        assert result["route_vertexes"] == [127.03, 37.49, 127.11, 37.39]

    @pytest.mark.asyncio
    async def test_get_route_invalid_origin_raises(self):
        """존재하지 않는 출발지 입력 시 ValueError가 전파되어야 한다."""
        from main import get_route

        with patch("main.address_to_coords", new=AsyncMock(
            side_effect=ValueError("좌표를 찾을 수 없습니다: '없는장소'")
        )):
            with pytest.raises(ValueError, match="좌표를 찾을 수 없습니다"):
                await get_route("없는장소", "판교역")

    @pytest.mark.asyncio
    async def test_get_route_priority_passed_through(self):
        """priority 파라미터가 get_directions에 올바르게 전달되어야 한다."""
        from main import get_route

        mock_coords = {"x": 127.0, "y": 37.0, "name": "A"}
        mock_directions = {
            "distance": 5000,
            "duration": 600,
            "fare": {"taxi": 8000, "toll": 0},
            "route_vertexes": [],
        }

        with (
            patch("main.address_to_coords", new=AsyncMock(return_value=mock_coords)),
            patch("main.get_directions", new=AsyncMock(return_value=mock_directions)) as mock_dir,
        ):
            await get_route("A", "B", priority="TIME")

        call_kwargs = mock_dir.call_args.kwargs
        assert call_kwargs["priority"] == "TIME"
