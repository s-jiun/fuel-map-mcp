"""
테스트: kakao_client.py

실제 Kakao API를 호출하는 통합 테스트와,
API 응답을 모킹하는 단위 테스트로 구성됩니다.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from kakao_client import address_to_coords, get_directions


# ---------------------------------------------------------------------------
# 단위 테스트 (Mock 사용)
# ---------------------------------------------------------------------------

class TestAddressToCoords:
    """address_to_coords — Kakao Local API 모킹 테스트"""

    @pytest.mark.asyncio
    async def test_address_search_success(self):
        """주소 검색이 성공하면 첫 번째 결과의 좌표를 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documents": [
                {"x": "127.1119569", "y": "37.3946083", "address_name": "경기도 성남시 분당구 판교역로 160"}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            result = await address_to_coords("판교역")

        assert result["x"] == pytest.approx(127.1119569)
        assert result["y"] == pytest.approx(37.3946083)

    @pytest.mark.asyncio
    async def test_address_search_fallback_to_keyword(self):
        """주소 검색 결과가 없으면 키워드 검색으로 폴백해야 한다."""
        # 첫 번째 호출(주소 검색) → 빈 결과
        # 두 번째 호출(키워드 검색) → 결과 있음
        empty_response = MagicMock()
        empty_response.json.return_value = {"documents": []}
        empty_response.raise_for_status = MagicMock()

        keyword_response = MagicMock()
        keyword_response.json.return_value = {
            "documents": [
                {"x": "127.0276368", "y": "37.4979502", "place_name": "강남역"}
            ]
        }
        keyword_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = [empty_response, keyword_response]

            result = await address_to_coords("강남역")

        assert result["x"] == pytest.approx(127.0276368)
        assert result["name"] == "강남역"

    @pytest.mark.asyncio
    async def test_address_not_found_raises(self):
        """주소/키워드 모두 결과 없으면 ValueError를 발생시켜야 한다."""
        empty_response = MagicMock()
        empty_response.json.return_value = {"documents": []}
        empty_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = empty_response

            with pytest.raises(ValueError, match="좌표를 찾을 수 없습니다"):
                await address_to_coords("존재하지않는장소XYZ")


class TestGetDirections:
    """get_directions — Kakao Mobility Directions API 모킹 테스트"""

    @pytest.mark.asyncio
    async def test_directions_success(self):
        """정상 응답 시 거리/시간/요금/vertexes를 반환해야 한다."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "routes": [
                {
                    "result_code": 0,
                    "result_msg": "길찾기 성공",
                    "summary": {
                        "distance": 12500,
                        "duration": 1800,
                        "fare": {"taxi": 15000, "toll": 900},
                    },
                    "sections": [
                        {
                            "roads": [
                                {"name": "테헤란로", "vertexes": [127.03, 37.49, 127.04, 37.50]},
                                {"name": "판교로", "vertexes": [127.04, 37.50, 127.11, 37.39]},
                            ]
                        }
                    ],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            result = await get_directions(127.0276, 37.4979, 127.1119, 37.3946)

        assert result["distance"] == 12500
        assert result["duration"] == 1800
        assert result["fare"]["toll"] == 900
        assert result["route_vertexes"] == [127.03, 37.49, 127.04, 37.50, 127.04, 37.50, 127.11, 37.39]

    @pytest.mark.asyncio
    async def test_directions_no_route_raises(self):
        """경로가 없으면 ValueError를 발생시켜야 한다."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"routes": []}
        mock_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            with pytest.raises(ValueError, match="경로 데이터가 없습니다"):
                await get_directions(0.0, 0.0, 0.0, 0.0)

    @pytest.mark.asyncio
    async def test_directions_error_code_raises(self):
        """result_code != 0이면 ValueError를 발생시켜야 한다."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "routes": [
                {"result_code": 104, "result_msg": "출발, 도착지가 설정되지 않았습니다."}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("kakao_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            with pytest.raises(ValueError, match="경로 찾기 실패"):
                await get_directions(0.0, 0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# 통합 테스트 (실제 API 호출) — `pytest -m integration` 으로 실행
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestIntegration:
    """실제 Kakao API를 호출하는 통합 테스트. 네트워크 필요."""

    @pytest.mark.asyncio
    async def test_address_to_coords_gangnam(self):
        result = await address_to_coords("강남역")
        assert "x" in result and "y" in result
        # 강남역은 서울 (경도 126~128, 위도 37~38 범위)
        assert 126 < result["x"] < 128
        assert 37 < result["y"] < 38

    @pytest.mark.asyncio
    async def test_address_to_coords_pangyo(self):
        result = await address_to_coords("판교역")
        assert "x" in result and "y" in result

    @pytest.mark.asyncio
    async def test_full_route_gangnam_to_pangyo(self):
        origin = await address_to_coords("강남역")
        dest = await address_to_coords("판교역")
        route = await get_directions(origin["x"], origin["y"], dest["x"], dest["y"])

        assert route["distance"] > 0
        assert route["duration"] > 0
        assert isinstance(route["route_vertexes"], list)
        assert len(route["route_vertexes"]) > 0
