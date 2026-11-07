from datetime import date

import pandas as pd
import pytest
import requests

import dately
from dately import _holiday as holiday_module
from dately._connect import http_client
from dately._holiday import HolidayLookupError, HolidayManager, parse_href_calendar
from dately.dt_nlp.string_similarity.spell_correction import LexicalFuzzer


@pytest.fixture
def manager():
    return HolidayManager()


@pytest.mark.parametrize("name", [
    "United States", "united states", "UNITED STATES", " US ", "usa", "U.S.A.",
    "United States of America", "  united   states  ",
])
def test_country_aliases_return_the_same_calendar(manager, name):
    assert manager.Holiday(name, 2026) == manager.Holiday("US", 2026)


@pytest.mark.parametrize("name, expected", [
    ("belgium", ("Belgium", "BE")), ("be", ("Belgium", "BE")),
    ("U.K.", ("United Kingdom", "GB")), ("GB", ("United Kingdom", "GB")),
    ("Côte d’Ivoire", ("Cote d'Ivoire", "CI")), ("Ivory Coast", ("Cote d'Ivoire", "CI")),
    ("Republic of the Congo", ("Congo", "CG")), ("Congo", ("Congo", "CG")),
    ("DR Congo", ("Congo Democratic Republic", "CD")), ("CD", ("Congo Democratic Republic", "CD")),
    ("Macao", ("Macau", "MO")), ("Timor-Leste", ("East Timor", "TL")),
])
def test_country_resolution_handles_codes_accents_and_canonical_precedence(manager, name, expected):
    assert manager._resolve_country(name) == expected


def test_all_legacy_country_names_are_resolvable(manager):
    for item in holiday_module.get_holiday_urls():
        assert manager._resolve_country(item["Country"])[0] == item["Country"]


def test_all_bundled_aliases_are_resolvable(manager):
    for alias in holiday_module.get_country_variants():
        assert manager._resolve_country(alias)[1]


def test_unknown_country_is_rejected_with_suggestion(manager):
    with pytest.raises(ValueError, match="Unknown country.*Did you mean 'Belgium'"):
        manager.Holiday("Belguim", 2026)
    with pytest.raises(ValueError, match="Unknown country"):
        manager.Holiday("Atlantis", 2026)
    with pytest.raises(TypeError, match="country_name"):
        manager.Holiday(None, 2026)


def test_lookup_does_not_modify_nlp_vocabulary(manager):
    original = LexicalFuzzer.vocabulary.copy()
    manager.Holiday("USA", 2026)
    with pytest.raises(ValueError):
        manager.Holiday("Atlantis", 2026)
    assert LexicalFuzzer.vocabulary == original


def test_public_api_formats_and_known_holidays():
    rows = dately.Holidate.Holiday("US", 2026)
    records = dately.Holidate.Holiday("USA", "2026", format="dict")
    frame = dately.Holidate.Holiday("united states", 2026, format="df")
    assert rows[0] == ["Date", "Name", "Type"]
    assert records == frame.to_dict("records")
    assert records == [dict(zip(rows[0], row)) for row in rows[1:]]
    assert rows[1:] == sorted(rows[1:])
    by_date = {record["Date"]: record for record in records}
    assert by_date["2026-01-01"]["Name"] == "New Year's Day"
    assert "Thanksgiving" in by_date["2026-11-26"]["Name"]
    assert all(record["Type"] == "Public holiday" for record in records)
    assert isinstance(frame, pd.DataFrame)
    assert dately.HolidayLookupError is HolidayLookupError


def test_default_holidays_work_without_network_or_http_state_changes(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network request")

    monkeypatch.setattr(requests.sessions.Session, "request", no_network)
    original_url, original_keys = http_client.base_url, http_client.api_keys.copy()
    manager = HolidayManager()
    assert "Belgium" in manager.ListCountries
    assert manager.Holiday("Belgium", 2026, "dict")[0]["Date"] == "2026-01-01"
    assert http_client.base_url == original_url
    assert http_client.api_keys == original_keys


def test_observed_days_subdivisions_and_year_filter(manager):
    actual = {row[0] for row in manager.Holiday("US", 2026)[1:]}
    unobserved = {row[0] for row in manager.Holiday("US", 2026, observed=False)[1:]}
    assert "2026-07-03" in actual
    assert "2026-07-03" not in unobserved
    assert "2026-07-04" in unobserved
    regional = {row[0] for row in manager.Holiday("US", 2026, subdiv="RI")[1:]}
    assert "2026-08-10" in regional  # Rhode Island Victory Day
    assert "2026-08-10" not in actual
    assert all(row[0].startswith("2026-") for row in manager.Holiday("US", 2026)[1:])
    with pytest.raises(ValueError, match="Invalid public holiday calendar"):
        manager.Holiday("US", 2026, subdiv="XX")


def test_default_year_is_evaluated_on_each_call(manager, monkeypatch):
    class NewYear(date):
        @classmethod
        def today(cls):
            return cls(2027, 1, 1)

    monkeypatch.setattr(holiday_module, "date", NewYear)
    assert manager.Holiday("US")[1][0] == "2027-01-01"


@pytest.mark.parametrize("kwargs", [
    {"year": "202x"}, {"year": 26}, {"year": 2026.0}, {"year": True}, {"year": 0},
    {"year": "0000"}, {"year": []}, {"format": "csv"}, {"format": []},
    {"source": "unknown"}, {"source": []}, {"observed": 1}, {"subdiv": ""},
    {"source": "timeanddate", "subdiv": "WI"}, {"source": "timeanddate", "observed": False},
])
def test_invalid_arguments_are_explicit(manager, kwargs):
    with pytest.raises((TypeError, ValueError)):
        manager.Holiday("US", **kwargs)


def test_supported_country_list_matches_the_installed_provider(manager, monkeypatch):
    monkeypatch.setattr(holiday_module._holiday_library(), "list_supported_countries", lambda **kwargs: {"US": []})
    assert manager.ListCountries == ["United States"]
    with pytest.raises(ValueError, match="not supported by holidays"):
        manager.Holiday("Belgium", 2026)


def test_empty_calendar_is_not_silently_returned(manager, monkeypatch):
    monkeypatch.setattr(holiday_module._holiday_library(), "country_holidays", lambda *args, **kwargs: {})
    with pytest.raises(HolidayLookupError, match="No public holiday dates"):
        manager.Holiday("US", 2026)


def test_missing_dependency_has_an_actionable_error(manager, monkeypatch):
    import builtins

    original_import = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "holidays":
            raise ImportError("holidays not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(HolidayLookupError, match="Reinstall or upgrade dately"):
        manager.Holiday("US", 2026)


class WebHTTP:
    def __init__(self, payload=None, error=None):
        self.base_url = "https://example.test/original"
        self.payload = payload
        self.error = error
        self.urls = []

    def update_base_url(self, value):
        self.base_url = value

    def make_request(self, params):
        self.urls.append(self.base_url)
        if self.error:
            raise self.error
        return [{self.base_url: self.payload}]


WEB_HTML = """
<html><title>Holidays 2026</title>
<table id="holidays-table">
 <tr><th colspan="2">Date</th><th>Name</th><th>Type</th><th>Details</th></tr>
 <tr><td>Jan&nbsp;1</td><td>Thursday</td>
     <td><a>New Year's <strong>Day</strong></a></td><td>National holiday</td><td>Extra</td></tr>
 <tr><td>25 Dec</td><td>Friday</td><td>Christmas Day</td><td>National holiday</td></tr>
</table></html>
"""


def test_web_source_preserves_labels_columns_and_formats():
    fake = WebHTTP({"response": WEB_HTML})
    manager = HolidayManager(fake)
    records = manager.Holiday("BE", 2026, "dict", source="timeanddate")
    assert records == [
        {"Date": "2026-01-01", "Name": "New Year's Day", "Type": "National holiday"},
        {"Date": "2026-12-25", "Name": "Christmas Day", "Type": "National holiday"},
    ]
    assert manager.Holiday("BE", 2026, "df", source="timeanddate").to_dict("records") == records
    assert fake.base_url == "https://example.test/original"
    assert fake.urls[0] == "https://www.timeanddate.com/holidays/belgium/2026"


@pytest.mark.parametrize("payload, match", [
    ({"error": "HTTP Error 403: Forbidden"}, "403"),
    ({"message": "Rate limit exceeded"}, "Rate limit"),
    ({}, "missing response"),
    ({"response": None}, "non-HTML"),
    ({"response": "<html>Access denied</html>"}, "table is missing"),
    ({"response": "<table id='holidays-table'></table>"}, "no dated holiday rows"),
    ({"response": WEB_HTML.replace("2026", "2027")}, "year does not match"),
    # Python 3.14 changed datetime's wording; assert our wrapper and the
    # invalid day rather than depending on a particular interpreter message.
    ({"response": WEB_HTML.replace("Jan&nbsp;1", "Feb 30")}, "Invalid holiday data.*day"),
    ({"response": "<table id='holidays-table'><tr><td>Jan 1</td></tr></table>"}, "incomplete row"),
])
def test_web_failures_raise_useful_errors_and_restore_state(payload, match):
    fake = WebHTTP(payload)
    with pytest.raises(HolidayLookupError, match=match):
        HolidayManager(fake).Holiday("US", 2026, source="timeanddate")
    assert fake.base_url == "https://example.test/original"


def test_http_exceptions_restore_state():
    fake = WebHTTP(error=requests.Timeout("Request timed out"))
    with pytest.raises(HolidayLookupError, match="timed out"):
        HolidayManager(fake).Holiday("US", 2026, source="timeanddate")
    assert fake.base_url == "https://example.test/original"


@pytest.mark.parametrize("response", [None, [], [{}], [{"other-url": {"response": WEB_HTML}}]])
def test_malformed_response_envelopes_fail_explicitly(response):
    class MalformedHTTP(WebHTTP):
        def make_request(self, params):
            return response

    fake = MalformedHTTP()
    with pytest.raises(HolidayLookupError):
        HolidayManager(fake).Holiday("US", 2026, source="timeanddate")
    assert fake.base_url == "https://example.test/original"


def test_web_source_requires_an_http_client(manager):
    with pytest.raises(HolidayLookupError, match="requires an HTTP client"):
        manager.Holiday("US", 2026, source="timeanddate")


def test_headerless_web_table_does_not_drop_the_first_holiday():
    parser = parse_href_calendar(year=2027)
    parser.set_html_content("<table id='holidays-table'><tr><td>Jan 1</td><td>New Year</td><td>Public</td></tr></table>")
    expected = [["Date", "Name", "Type"], ["2027-01-01", "New Year", "Public"]]
    assert parser.get_cleaned_data() == expected
    assert parser.get_cleaned_data() == expected  # repeated reads preserve the data


def test_holidays_feed_business_calendar():
    dates = {date.fromisoformat(row["Date"]) for row in dately.Holidate.Holiday("US", 2026, "dict")}
    calendar = dately.BusinessCalendar(holidays=dates)
    assert dately.parse("1 business day after 2026-11-25", business_calendar=calendar) == date(2026, 11, 27)
