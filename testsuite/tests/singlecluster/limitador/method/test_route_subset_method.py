"""Tests that RLP for a HTTPRouteRule doesn't affect the HTTPRoute with same path but different method"""

import pytest

from testsuite.gateway import RouteMatch, PathMatch, MatchType, HTTPMethod
from testsuite.kuadrant.policy.authorization import Pattern
from testsuite.kuadrant.policy.rate_limit import Limit


pytestmark = [pytest.mark.kuadrant_only, pytest.mark.limitador]


@pytest.fixture(scope="module")
def route(route, backend):
    """Add new rule to the route"""
    route.remove_all_rules()
    route.add_rule(
        backend,
        RouteMatch(path=PathMatch(value="/anything", type=MatchType.PATH_PREFIX), method=HTTPMethod.GET),
    )
    route.add_rule(
        backend,
        RouteMatch(path=PathMatch(value="/anything", type=MatchType.PATH_PREFIX), method=HTTPMethod.POST),
    )
    return route


@pytest.fixture(scope="module")
def rate_limit(rate_limit):
    """Add limit to the policy"""
    when = [Pattern("request.path", "eq", "/anything"), Pattern("request.method", "eq", "GET")]
    rate_limit.add_limit("anything", [Limit(5, "10s")], when=when)
    return rate_limit


@pytest.mark.issue("https://github.com/Kuadrant/testsuite/issues/561")
def test_route_subset_method(client):
    """Tests that RLP for a HTTPRouteRule doesn't apply to separate HTTPRouteRule with different method"""
    responses = client.get_many("/anything", 5)
    assert all(
        r.status_code == 200 for r in responses
    ), f"Rate Limited resource unexpectedly rejected requests {responses}"
    assert client.get("/anything").status_code == 429
    assert client.post("/anything").status_code == 200
