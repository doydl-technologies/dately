#
# DOYDL's Temporal Parsing & Normalization Engine — dately
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
# Copyright (c) 2024 by DOYDL Technologies. All rights reserved.
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

import re
import unicodedata
from datetime import date
from difflib import get_close_matches
from html.parser import HTMLParser

import pandas as pd

from ._connect import http_client
from ._sysutils import DataImport
from ._webutils import absolute_url

_COLUMNS = ["Date", "Name", "Type"]
# Names absent from, or different from, the bundled timezone country data.
_COUNTRY_CODE_OVERRIDES = {
    "Congo": "CG",
    "Congo Democratic Republic": "CD",
    "Cote d'Ivoire": "CI",
    "East Timor": "TL",
    "Kosovo": "XK",
    "Macau": "MO",
    "St. Barts": "BL",
    "The Bahamas": "BS",
    "US Virgin Islands": "VI",
    "Vatican City (Holy See)": "VA",
    "Bouvet Island": "BV",
    "Western Sahara": "EH",
    "Heard Island and McDonald Islands": "HM",
}


class HolidayLookupError(RuntimeError):
    """Holiday dates could not be obtained or the source returned invalid data."""


def get_holiday_urls():
    return DataImport.load_holiday_urls()


def get_country_variants():
    return DataImport.load_country_variants()


def _country_key(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    words = re.sub(r"[^a-z0-9]+", " ", value).split()
    # Dotted abbreviations such as U.S.A. and U.K.
    return "".join(words) if all(len(word) == 1 for word in words) else " ".join(words)


def _holiday_library():
    try:
        import holidays
    except ImportError as exc:
        raise HolidayLookupError(
            "Public holiday calendars require the 'holidays' dependency. "
            "Reinstall or upgrade dately to install its dependencies."
        ) from exc
    return holidays


class parse_href_calendar(HTMLParser):
    """Parse the legacy holiday table, treating each HTML cell as one value."""

    def __init__(self, year=None):
        super().__init__()
        self.requested_year = year
        self.current_year_found = year
        self.in_table = False
        self.found_table = False
        self.cell = None
        self.row = []
        self.data = []

    def set_html_content(self, html_content):
        title = re.search(r"<title\b[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
        title_year = re.search(r"\b\d{4}\b", title[1]) if title else None
        if title_year:
            detected_year = int(title_year[0])
            if self.requested_year is not None and detected_year != self.requested_year:
                raise ValueError("Holiday page year does not match the requested year")
            self.current_year_found = detected_year
        if self.current_year_found is None:
            self.current_year_found = date.today().year
        self.feed(html_content)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == "holidays-table":
            self.in_table = self.found_table = True
        if self.in_table:
            if tag == "tr":
                self.row = []
            elif tag in {"td", "th"}:
                self.cell = []
            elif tag == "br" and self.cell is not None:
                self.cell.append(" ")

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr":
            if self.row:
                self.data.append(self.row)
        elif tag == "table":
            self.in_table = False

    def handle_data(self, data):
        if self.in_table and self.cell is not None:
            self.cell.append(data)

    def get_cleaned_data(self):
        if not self.found_table:
            raise ValueError("Holiday table is missing from the response")
        months = {
            name: index
            for index, name in enumerate(
                ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1
            )
        }
        weekdays = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        rows = []
        for raw_row in self.data:
            row = [value for value in raw_row if value and value.casefold() not in weekdays]
            if not row:
                continue
            match = re.fullmatch(r"([a-z]{3})\.? (\d{1,2})", row[0], re.IGNORECASE)
            reverse = re.fullmatch(r"(\d{1,2}) ([a-z]{3})\.?", row[0], re.IGNORECASE)
            if not match and not reverse:
                continue  # table headings and month separators
            month, day = (match[1], match[2]) if match else (reverse[2], reverse[1])
            if len(row) < 3:
                raise ValueError("Holiday table contains an incomplete row")
            holiday_date = date(self.current_year_found, months[month.casefold()], int(day))
            rows.append([holiday_date.isoformat(), row[1], row[2]])
        if not rows:
            raise ValueError("Holiday table contains no dated holiday rows")
        return [list(_COLUMNS)] + sorted(rows)


class HolidayManager:
    """Public holiday calendars by default; opt into the legacy web source.

    Public calendars are computed locally by python-holidays. They include
    observed dates, but not the full set of cultural/religious observances in
    the web feed. Country aliases are exact and case/accent insensitive;
    unknown names are rejected with a suggestion rather than guessed.
    """

    def __init__(self, instance_http=None):
        self.__HTTP = instance_http
        self.__links = {entry["Country"]: entry["Link"] for entry in get_holiday_urls()}
        codes = DataImport.load_country_codes()
        codes.update(_COUNTRY_CODE_OVERRIDES)
        self.__codes = codes
        # Prefer existing public names where both sources name a country.
        display_by_code = {code: name for name, code in codes.items()}
        for name in self.__links:
            display_by_code[codes[name]] = name
        self.__display_by_code = display_by_code
        aliases = {_country_key(name): display_by_code[code] for name, code in codes.items()}
        for alias, name in get_country_variants().items():
            if name in codes:
                aliases.setdefault(_country_key(alias), display_by_code[codes[name]])
        for code, name in display_by_code.items():
            aliases[_country_key(code)] = name
        self.__aliases = aliases

    def __dir__(self):
        return ["Holiday", "ListCountries"]

    def _resolve_country(self, country_name):
        if not isinstance(country_name, str):
            raise TypeError("country_name must be a country name or ISO alpha-2 code")
        key = _country_key(country_name)
        if key in self.__aliases:
            name = self.__aliases[key]
            return name, self.__codes[name]
        suggestion = get_close_matches(key, self.__aliases, n=1, cutoff=0.8)
        hint = f" Did you mean '{self.__aliases[suggestion[0]]}'?" if suggestion else ""
        raise ValueError(f"Unknown country '{country_name}'.{hint}")

    @property
    def ListCountries(self):
        """Names supported by the installed public-holiday calendar version."""
        supported = _holiday_library().list_supported_countries(include_aliases=False)
        return sorted(self.__display_by_code[code] for code in supported if code in self.__display_by_code)

    def _public_calendar(self, name, code, year, subdiv, observed):
        """Validate options and build provider rules; year=None generates no dates."""
        library = _holiday_library()
        if code not in library.list_supported_countries(include_aliases=False):
            raise ValueError(
                f"Public holidays for '{name}' are not supported by holidays {library.__version__}. "
                "Upgrade holidays or explicitly use source='timeanddate'."
            )
        try:
            return library.country_holidays(
                code,
                years=year,
                subdiv=subdiv,
                observed=observed,
                language="en_US",
                expand=False,
            )
        except (ValueError, NotImplementedError) as exc:
            raise ValueError(f"Invalid public holiday calendar for '{name}': {exc}") from exc
        except Exception as exc:
            raise HolidayLookupError(f"Could not calculate public holidays for '{name}' in {year}: {exc}") from exc

    def _public_rows(self, name, code, year, subdiv, observed):
        calendar = self._public_calendar(name, code, year, subdiv, observed)
        rows = [
            [day.isoformat(), label, "Public holiday"] for day, label in sorted(calendar.items()) if day.year == year
        ]
        if not rows:
            raise HolidayLookupError(
                f"No public holiday dates are available for '{name}' in {year}. "
                "The installed calendar may not cover this country/year."
            )
        return [list(_COLUMNS)] + rows

    def _web_rows(self, name, year):
        if name not in self.__links:
            raise ValueError(f"The timeanddate source does not list '{name}'")
        if self.__HTTP is None:
            raise HolidayLookupError("The timeanddate source requires an HTTP client")
        url = absolute_url(self.__links[name], str(year))
        original_url = self.__HTTP.base_url
        try:
            self.__HTTP.update_base_url(url)
            result = self.__HTTP.make_request(params={"format": "html"})
        except Exception as exc:
            raise HolidayLookupError(f"Holiday request failed for '{name}' in {year}: {exc}") from exc
        finally:
            self.__HTTP.update_base_url(original_url)
        if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
            raise HolidayLookupError("Holiday source returned an invalid response envelope")
        payload = result[0].get(url)
        if not isinstance(payload, dict) or "response" not in payload:
            detail = (payload.get("error") or payload.get("message")) if isinstance(payload, dict) else None
            raise HolidayLookupError(
                f"Holiday source failed for '{name}' in {year}: {detail or 'missing response'}. "
                "Use source='public' for offline public holidays."
            )
        html = payload["response"]
        if not isinstance(html, str):
            raise HolidayLookupError("Holiday source returned non-HTML content")
        try:
            parser = parse_href_calendar(year=year)
            parser.set_html_content(html)
            return parser.get_cleaned_data()
        except (ValueError, KeyError) as exc:
            raise HolidayLookupError(f"Invalid holiday data for '{name}' in {year}: {exc}") from exc

    def Holiday(self, country_name, year=None, format="list", *, source="public", subdiv=None, observed=True):
        """Return Date/Name/Type rows, records, or a DataFrame.

        source='public' uses offline public-holiday rules (including observed
        dates by default). source='timeanddate' explicitly requests the broader
        web feed and raises HolidayLookupError on transport or parsing failure.
        Invalid arguments raise TypeError/ValueError; no failure returns None.
        """
        if not isinstance(source, str) or source not in {"public", "timeanddate"}:
            raise ValueError("source must be 'public' or 'timeanddate'")
        if not isinstance(format, str) or format not in {"list", "dict", "df"}:
            raise ValueError("format must be 'list', 'dict', or 'df'")
        if year is None:
            year = date.today().year
        if isinstance(year, str) and re.fullmatch(r"[0-9]{4}", year.strip()):
            year = int(year.strip())
        if type(year) is not int or not 1000 <= year <= 9999:
            raise ValueError("year must be a four-digit integer or string (1000-9999)")
        if type(observed) is not bool:
            raise TypeError("observed must be a boolean")
        if subdiv is not None and (not isinstance(subdiv, str) or not subdiv.strip()):
            raise ValueError("subdiv must be a non-empty subdivision code or None")
        if source == "timeanddate" and (subdiv is not None or observed is not True):
            raise ValueError("subdiv and observed options apply only to source='public'")
        name, code = self._resolve_country(country_name)
        data = (
            self._public_rows(name, code, year, subdiv, observed) if source == "public" else self._web_rows(name, year)
        )
        if format == "dict":
            return [dict(zip(_COLUMNS, row)) for row in data[1:]]
        if format == "df":
            return pd.DataFrame(data[1:], columns=_COLUMNS)
        return data


def get_Holidate():
    return HolidayManager(http_client)


__all__ = ["HolidayLookupError", "HolidayManager", "get_Holidate"]
