import pytest
from datetime import datetime
from uuid import uuid4

from app.models.sources import Source, SourceType
from app.services.citation_service import (
    append_source_list,
    extract_citations,
    limit_citations_per_paragraph,
    validate_citations,
)


@pytest.fixture
def sample_sources():
    return [
        Source(
            source_id=uuid4(),
            session_id=uuid4(),
            url="https://example.com/1",
            title="Example One",
            snippet="First source snippet",
            source_type=SourceType.WEB,
            search_query="test",
            retrieved_at=datetime.utcnow(),
        ),
        Source(
            source_id=uuid4(),
            session_id=uuid4(),
            url="https://example.com/2",
            title="Example Two",
            snippet="Second source snippet",
            source_type=SourceType.WEB,
            search_query="test",
            retrieved_at=datetime.utcnow(),
        ),
    ]


def test_extract_citations_returns_only_valid_entries(sample_sources):
    text = "Alpha [1]. Beta [2]. Gamma [9]."

    citations = extract_citations(text, sample_sources)

    assert len(citations) == 2
    assert citations[0]["citation_index"] == 1
    assert citations[1]["citation_index"] == 2
    assert citations[0]["source_id"] == sample_sources[0].source_id
    assert citations[1]["source_id"] == sample_sources[1].source_id
    assert citations[0]["claim_text"].startswith("Alpha")


def test_validate_citations_reports_invalid_indexes(sample_sources):
    text = "One [1]. Two [3]. Three [9]."

    invalid_indexes = validate_citations(text, sample_sources)

    assert invalid_indexes == [3, 9]


def test_append_source_list_formats_sources(sample_sources):
    response = "Here is the answer."

    rendered = append_source_list(response, sample_sources)

    assert rendered.startswith("Here is the answer.")
    assert "Sources:" in rendered
    assert "[1] Example One - https://example.com/1" in rendered
    assert "[2] Example Two - https://example.com/2" in rendered


def test_extract_citations_deduplicates_repeated_reference(sample_sources):
    text = "Same claim [1]. Same claim [1]."

    citations = extract_citations(text, sample_sources)

    assert len(citations) == 1
    assert citations[0]["citation_index"] == 1


def test_limit_citations_per_paragraph_keeps_three_most_relevant():
    session_id = uuid4()
    sources = [
        Source(
            source_id=uuid4(),
            session_id=session_id,
            url=f"https://example.com/{index}",
            title=title,
            snippet=snippet,
            source_type=SourceType.WEB,
            search_query="fluid mechanics",
            retrieved_at=datetime.utcnow(),
        )
        for index, (title, snippet) in enumerate(
            [
                ("Thin note", "Short."),
                (
                    "Fluid mechanics equations",
                    "Fluid mechanics uses continuity, Navier Stokes, pressure, viscosity, and flow analysis.",
                ),
                (
                    "Boundary layers",
                    "Boundary layer flow explains viscosity, drag, turbulence, and engineering fluid behavior.",
                ),
                (
                    "Fluid applications",
                    "Engineering applications of fluid mechanics include pumps, pipes, aerodynamics, and CFD.",
                ),
            ],
            start=1,
        )
    ]
    text = (
        "Fluid mechanics studies pressure, viscosity, flow, boundary layers, "
        "and engineering applications [1][2][3][4]."
    )

    limited = limit_citations_per_paragraph(text, sources)

    assert "[1]" not in limited
    assert "[2]" in limited
    assert "[3]" in limited
    assert "[4]" in limited
    assert limited.count("[") == 3
