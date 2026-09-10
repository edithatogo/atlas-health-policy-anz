"""Check the public NSW/SCHN model-SoCP catalogue against its source pages.

The checker is read-only. It reports source health and candidate document URLs;
it does not overwrite the reviewed catalogue or promote a source into an
operative local authority.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Final, TypedDict, cast
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

ROOT: Final = Path(__file__).resolve().parents[1]
COLLECTION: Final = (
    ROOT / "data" / "source-intake" / "credentialing-socp-anz-20260910"
)
USER_AGENT: Final = "Australian-Health-Policy-Atlas/1.0 (+source-health-check)"
SOURCE_PAGES: Final = {
    "Medical and surgical": (
        "https://www.schn.health.nsw.gov.au/nsw-state-scope-clinical-practice-unit/"
        "model-scopes-surgical-and-medical",
        COLLECTION / "schn-medical-surgical-model-catalogue.csv",
    ),
    "Paediatric": (
        "https://www.schn.health.nsw.gov.au/nsw-state-scope-clinical-practice-unit/"
        "model-scopes-paediatric",
        COLLECTION / "schn-paediatric-model-catalogue.csv",
    ),
    "Dental": (
        "https://www.schn.health.nsw.gov.au/nsw-state-scope-clinical-practice-unit/"
        "model-scopes-dental",
        COLLECTION / "schn-dental-model-catalogue.csv",
    ),
}
IGNORED_WORDS: Final = {
    "final",
    "model",
    "models",
    "scope",
    "scopes",
    "clinical",
    "practice",
    "socp",
    "for",
    "updated",
    "version",
    "pdf",
}


class CatalogueRow(TypedDict):
    """Reviewed model-catalogue row."""

    model_id: str
    category: str
    specialty: str
    status: str
    authoritative_listing_url: str
    document_url: str
    verified: str


@dataclass(frozen=True)
class Link:
    """One link discovered on a source page."""

    href: str
    text: str


@dataclass(frozen=True)
class ModelCheck:
    """Source-health result for one expected model."""

    model_id: str
    category: str
    specialty: str
    expected_status: str
    source_page: str
    discovered_url: str | None
    match_count: int
    source_text_present: bool
    result: str


class LinkParser(HTMLParser):
    """Collect links and visible text without executing page scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[Link] = []
        self.visible_text: list[str] = []
        self._href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "a":
            return
        attributes = dict(attrs)
        self._href = attributes.get("href")
        self._anchor_text = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        self.visible_text.append(text)
        if self._href is not None:
            self._anchor_text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._href is None:
            return
        self.links.append(
            Link(
                href=self._href,
                text=" ".join(self._anchor_text),
            )
        )
        self._href = None
        self._anchor_text = []


def read_catalogue(path: Path) -> list[CatalogueRow]:
    """Read a reviewed catalogue with complete string cells."""
    rows: list[CatalogueRow] = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row_number, raw in enumerate(csv.DictReader(stream), start=2):
            if None in raw or any(value is None for value in raw.values()):
                message = f"Incomplete catalogue row {row_number}: {path}"
                raise ValueError(message)
            rows.append(cast("CatalogueRow", {str(key): str(value) for key, value in raw.items()}))
    return rows


def normalise(value: str) -> str:
    """Normalise a specialty or source-link label for conservative matching."""
    decoded = unquote(value).replace("&", " and ")
    decoded = re.sub(r"\b(?:19|20)\d{2}\b", " ", decoded)
    decoded = re.sub(r"\bv?\d+(?:[._-]\d+)+\b", " ", decoded, flags=re.IGNORECASE)
    tokens = re.findall(r"[a-z0-9]+", decoded.lower())
    retained = [token for token in tokens if token not in IGNORED_WORDS]
    return " ".join(retained)


def link_label(link: Link) -> str:
    """Return visible anchor text plus decoded filename for matching."""
    filename = Path(urlparse(link.href).path).name
    return f"{link.text} {filename}".strip()


def candidate_pdf_links(parser: LinkParser, page_url: str) -> list[Link]:
    """Return unique model-scope PDF candidates from a listing page."""
    seen: set[str] = set()
    links: list[Link] = []
    for link in parser.links:
        absolute = urljoin(page_url, link.href)
        label = normalise(link_label(link))
        path = urlparse(absolute).path.lower()
        if not path.endswith(".pdf"):
            continue
        if "socp" not in label and "scope" not in label:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(Link(href=absolute, text=link.text))
    return links


def fetch_html(url: str, timeout_seconds: int) -> str:
    """Fetch one public listing page with a bounded read-only request."""
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            message = f"Unexpected content type for {url}: {content_type}"
            raise ValueError(message)
        return response.read().decode(response.headers.get_content_charset() or "utf-8")


def load_html(
    *,
    category: str,
    page_url: str,
    html_directory: Path | None,
    timeout_seconds: int,
) -> str:
    """Load live or fixture HTML for one category."""
    if html_directory is None:
        return fetch_html(page_url, timeout_seconds)
    fixture_name = category.lower().replace(" and ", "-").replace(" ", "-") + ".html"
    return (html_directory / fixture_name).read_text(encoding="utf-8")


def match_model(
    row: CatalogueRow,
    page_url: str,
    links: list[Link],
    page_text: str,
) -> ModelCheck:
    """Match one reviewed model to conservative source-page evidence."""
    specialty = normalise(row["specialty"])
    matches = [
        link
        for link in links
        if specialty
        and (
            specialty in normalise(link_label(link))
            or normalise(link_label(link)) in specialty
        )
    ]
    source_text_present = specialty in normalise(page_text)
    expected_final = row["status"] == "Final"
    if expected_final and len(matches) == 1:
        result = "matched-final"
    elif expected_final and not matches:
        result = "missing-final-link"
    elif expected_final:
        result = "ambiguous-final-link"
    elif source_text_present and not matches:
        result = "under-review-present-without-final-link"
    elif matches:
        result = "under-review-has-unexpected-final-link"
    else:
        result = "under-review-title-not-found"
    return ModelCheck(
        model_id=row["model_id"],
        category=row["category"],
        specialty=row["specialty"],
        expected_status=row["status"],
        source_page=page_url,
        discovered_url=matches[0].href if len(matches) == 1 else None,
        match_count=len(matches),
        source_text_present=source_text_present,
        result=result,
    )


def check_catalogue(
    *,
    html_directory: Path | None = None,
    timeout_seconds: int = 30,
) -> dict[str, object]:
    """Build a complete, deterministic source-health report."""
    checks: list[ModelCheck] = []
    page_receipts: list[dict[str, object]] = []
    for category, (page_url, catalogue_path) in SOURCE_PAGES.items():
        html = load_html(
            category=category,
            page_url=page_url,
            html_directory=html_directory,
            timeout_seconds=timeout_seconds,
        )
        parser = LinkParser()
        parser.feed(html)
        links = candidate_pdf_links(parser, page_url)
        page_text = " ".join(parser.visible_text)
        rows = read_catalogue(catalogue_path)
        checks.extend(match_model(row, page_url, links, page_text) for row in rows)
        page_receipts.append(
            {
                "category": category,
                "page_url": page_url,
                "expected_entries": len(rows),
                "candidate_pdf_links": len(links),
            }
        )

    accepted_results = {
        "matched-final",
        "under-review-present-without-final-link",
    }
    failures = [check for check in checks if check.result not in accepted_results]
    return {
        "schema_version": 1,
        "observed_at": "runtime",
        "source_pages": page_receipts,
        "catalogue_entries": len(checks),
        "final_entries": sum(check.expected_status == "Final" for check in checks),
        "under_review_entries": sum(
            check.expected_status == "Under review after consultation" for check in checks
        ),
        "passed": not failures,
        "failure_count": len(failures),
        "checks": [asdict(check) for check in checks],
        "evidence_ceiling": (
            "Read-only listing-page and link-health evidence at the observation time. "
            "It does not establish document currency, local adoption, service capability, "
            "individual competence, scope or operating effectiveness."
        ),
    }


def parse_args() -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--html-directory", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the source-health check and write its report."""
    args = parse_args()
    report = check_catalogue(
        html_directory=args.html_directory,
        timeout_seconds=args.timeout_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "checks"}, indent=2))
    if args.strict and report["passed"] is not True:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
