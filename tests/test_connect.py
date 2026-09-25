# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# The `dately` module is a deterministic engine for parsing, resolving, and normalizing
# temporal expressions across both natural and symbolic language contexts — built for NLP
# workflows, cross-platform date handling, and fine-grained temporal reasoning.
#
# Designed with formal grammatical rigor, `dately` interprets phrases like “first five days of next month,”
# “Q3 of last year,” and “April 3” — handling cardinal/ordinal resolution, anchored structures, and
# ambiguous or implicit references with linguistic sensitivity.
#
# The engine combines structured tokenization, symbolic transformation, and rule-based semantic
# composition to support precision across tasks such as entity recognition, information extraction,
# and temporal normalization in noisy or informal text.
#
# It guarantees invertibility, transparency, and cross-platform consistency, resolving platform-specific
# formatting differences (e.g. Windows vs. Unix) while maintaining NLP-grade flexibility for English-language
# temporal constructions.
#
# Whether embedded in intelligent agents, ETL pipelines, or legal/medical NLP systems, `dately` brings
# clarity and structure to temporal meaning — bridging symbolic logic with real-world language.
#
# Copyright (c) 2024 by doydl technologies. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import requests

from dately._connect import http_client
from dately._holiday import HolidayManager
from dately._timezone import ZoneInfoManager
from dately._webutils import UserAgentRandomizer


def test_http_client_uses_requests_encoding_negotiation():
    assert (
        http_client.get_headers("Accept-Encoding")
        == requests.utils.default_headers()["Accept-Encoding"]
    )


def test_api_keys_are_scoped_to_their_own_service():
    original_url = http_client.base_url
    original_key_type = http_client.current_key_type
    try:
        http_client.current_key_type = "FullVersion"
        http_client.update_base_url("https://api.timezonedb.com/v2.1/list-time-zone")
        assert http_client._api_key_allowed_for_current_host()

        http_client.update_base_url("https://worldtimeapi.org/api/timezone/Europe/London")
        assert not http_client._api_key_allowed_for_current_host()

        http_client.update_base_url("https://www.timeanddate.com/holidays/us/2026")
        assert not http_client._api_key_allowed_for_current_host()

        http_client.current_key_type = "DependentVersion"
        http_client.update_base_url("https://api.ipgeolocation.io/timezone")
        assert http_client._api_key_allowed_for_current_host()
    finally:
        http_client.current_key_type = original_key_type
        http_client.update_base_url(original_url)


def test_key_bootstrap_remains_lazy():
    assert http_client.api_keys == {}


def test_user_agents_come_from_the_vendored_profile():
    assert UserAgentRandomizer._generator.__class__.__module__.startswith(
        "dately._vendor.agent_profile"
    )
    assert UserAgentRandomizer.get().startswith("Mozilla/5.0")


class FakeHTTP:
    def __init__(self, response):
        self.base_url = "https://example.test/original"
        self.host = "example.test"
        self.current_key_type = "FullVersion"
        self.response = response
        self.request_urls = []

    def update_base_url(self, value):
        self.base_url = value
        self.host = value

    def set_key_type(self, value):
        self.current_key_type = value

    def make_request(self, params, **kwargs):
        self.request_urls.append(self.base_url)
        return [{self.base_url: {"response": self.response}}]


def test_timezoner_network_methods_use_explicit_endpoints_and_restore_state():
    response = {
        "zones": [
            {"zoneName": "Europe/London"},
            {"zoneName": "America/New_York"},
        ]
    }
    fake = FakeHTTP(response)
    manager = ZoneInfoManager({}, fake)

    result = manager.ConvertTimeZone(
        "Europe/London",
        "America/New_York",
        year=2026,
        month=1,
        day=1,
    )

    assert [item["zoneName"] for item in result] == ["Europe/London", "America/New_York"]
    assert fake.request_urls == ["https://api.timezonedb.com/v2.1/convert-time-zone"]
    assert fake.base_url == "https://example.test/original"


def test_holidate_restores_http_state_after_fixture_backed_request():
    html = """
    <html><head><title>Holidays 2026</title></head><body>
    <table id="holidays-table">
      <tr><th>Date</th><th>Name</th><th>Type</th></tr>
      <tr><td>Jan 1</td><td>New Year's Day</td><td>National holiday</td></tr>
    </table>
    </body></html>
    """
    fake = FakeHTTP(html)
    manager = HolidayManager(fake)

    result = manager.Holiday("Belgium", year=2026)

    assert result == [
        ["Date", "Name", "Type"],
        ["2026-01-01", "New Year's Day", "National holiday"],
    ]
    assert fake.request_urls[0].startswith("https://www.timeanddate.com/holidays/belgium/")
    assert fake.base_url == "https://example.test/original"
