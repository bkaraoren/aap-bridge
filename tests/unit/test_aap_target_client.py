"""Unit tests for AAPTargetClient."""

from unittest.mock import AsyncMock, patch

import pytest

from aap_migration.client.aap_target_client import AAPTargetClient
from aap_migration.config import AAPInstanceConfig


@pytest.fixture
def target_client():
    """Create an AAPTargetClient with a resolved token."""
    config = AAPInstanceConfig(
        url="https://target.example.com",
        token="test-token",
        verify_ssl=False,
    )
    return AAPTargetClient(config)


class TestListResourcesPagination:
    """Tests for list_resources() pagination behavior."""

    @pytest.mark.asyncio
    async def test_follows_next_url_query_params(self, target_client):
        """Next page requests must preserve query params from the next URL."""
        page1 = {
            "count": 2,
            "results": [{"id": 1, "name": "host-a"}],
            "next": (
                "https://target.example.com/api/controller/v2/hosts/"
                "?page=2&page_size=1&name__in=host-a,host-b"
            ),
        }
        page2 = {
            "count": 2,
            "results": [{"id": 2, "name": "host-b"}],
            "next": None,
        }
        target_client.get = AsyncMock(side_effect=[page1, page2])

        results = await target_client.list_resources(
            "hosts",
            filters={"name__in": "host-a,host-b"},
            page_size=1,
        )

        assert len(results) == 2
        assert target_client.get.await_count == 2
        second_call = target_client.get.call_args_list[1]
        assert second_call.args[0] == "hosts/"
        assert second_call.kwargs["params"] == {
            "page": "2",
            "page_size": "1",
            "name__in": "host-a,host-b",
        }

    @pytest.mark.asyncio
    async def test_stops_when_pagination_makes_no_progress(self, target_client):
        """Identical next requests should not loop indefinitely."""
        stuck_page = {
            "count": 200,
            "results": [{"id": 1, "name": "group-a"}],
            "next": (
                "https://target.example.com/api/controller/v2/groups/"
                "?page_size=100&name__in=group-a"
            ),
        }
        target_client.get = AsyncMock(return_value=stuck_page)

        with patch("aap_migration.client.aap_target_client.logger") as mock_logger:
            results = await target_client.list_resources(
                "inventory_groups",
                filters={"name__in": "group-a"},
            )

        assert len(results) == 1
        assert target_client.get.await_count == 1
        mock_logger.warning.assert_called_once()
        assert mock_logger.warning.call_args[0][0] == "pagination_no_progress"
