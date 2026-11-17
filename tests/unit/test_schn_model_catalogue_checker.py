from __future__ import annotations

from scripts.check_schn_model_catalogue import (
    Link,
    LinkParser,
    candidate_pdf_links,
    match_model,
    normalise,
)

SOURCE_PAGE = (
    "https://www.schn.health.nsw.gov.au/"
    "nsw-state-scope-clinical-practice-unit/model-scopes-paediatric"
)


def model_row(*, specialty: str, status: str, model_id: str) -> dict[str, str]:
    return {
        "model_id": model_id,
        "category": "Paediatric",
        "specialty": specialty,
        "status": status,
        "authoritative_listing_url": SOURCE_PAGE,
        "document_url": "",
        "verified": "2026-09-10",
    }


def test_candidate_links_are_pdf_model_links_and_are_deduplicated() -> None:
    parser = LinkParser()
    parser.feed(
        """
        <html><body>
          <a href="/files/Final%20Model%20SoCP%20for%20Clinical%20Genetics.pdf">
            Clinical Genetics
          </a>
          <a href="/files/Final%20Model%20SoCP%20for%20Clinical%20Genetics.pdf">
            duplicate link
          </a>
          <a href="/files/unrelated-guideline.pdf">Unrelated guideline</a>
          <a href="/model-page">General Paediatrics</a>
        </body></html>
        """
    )

    links = candidate_pdf_links(parser, SOURCE_PAGE)
    assert links == [
        Link(
            href=(
                "https://www.schn.health.nsw.gov.au/files/"
                "Final%20Model%20SoCP%20for%20Clinical%20Genetics.pdf"
            ),
            text="Clinical Genetics",
        )
    ]


def test_final_model_requires_one_conservative_link_match() -> None:
    row = model_row(
        specialty="Clinical Genetics (including Paediatric Clinical Genetics)",
        status="Final",
        model_id="SCHN-P-001",
    )
    links = [
        Link(
            href="https://www.schn.health.nsw.gov.au/files/clinical-genetics.pdf",
            text="Clinical Genetics including Paediatric Clinical Genetics",
        )
    ]

    result = match_model(row, SOURCE_PAGE, links, "Clinical Genetics")
    assert result.result == "matched-final"
    assert result.match_count == 1
    assert result.discovered_url == links[0].href


def test_under_review_title_is_not_treated_as_a_final_model() -> None:
    row = model_row(
        specialty="General Practice",
        status="Under review after consultation",
        model_id="SCHN-R-001",
    )

    result = match_model(
        row,
        SOURCE_PAGE,
        [],
        "Models under review after consultation: General Practice",
    )
    assert result.result == "under-review-present-without-final-link"
    assert result.discovered_url is None


def test_missing_and_ambiguous_final_links_fail_closed() -> None:
    row = model_row(
        specialty="General Paediatrics",
        status="Final",
        model_id="SCHN-P-003",
    )
    missing = match_model(row, SOURCE_PAGE, [], "General Paediatrics")
    ambiguous = match_model(
        row,
        SOURCE_PAGE,
        [
            Link(href="https://example.test/one.pdf", text="General Paediatrics"),
            Link(href="https://example.test/two.pdf", text="General Paediatrics"),
        ],
        "General Paediatrics",
    )

    assert missing.result == "missing-final-link"
    assert ambiguous.result == "ambiguous-final-link"
    assert ambiguous.discovered_url is None


def test_normalisation_removes_document_noise_without_erasing_specialty() -> None:
    value = "Final Model SoCP for Obstetrics & Gynaecology v1.2 - 26 Sep 2023.pdf"
    assert normalise(value) == "obstetrics and gynaecology 1 2 26 sep"
