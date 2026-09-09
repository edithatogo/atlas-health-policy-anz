"""Verify both committed intake histories without downloading or interpreting PDFs."""

from pathlib import Path

from scripts import source_packets

from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas.packet_holdings import summarize_holdings
from australian_health_policy_atlas.packet_ingestion import (
    inspect_packet,
    load_packet_registry,
    packet_metadata_paths,
)


def test_actual_split_intake_and_cross_packet_byte_holdings() -> None:
    specs = load_packet_registry(Path())
    assert len(specs) == 2
    observations = [inspect_packet(Path(spec.directory), spec) for spec in specs]
    legacy, intake = observations
    assert (
        legacy["sha256"]
        == "cdec4980f6eb44dd98a9aeaab3c9c3cde694e7e0b9449d5f3d1f7198ddbdb5f7"
    )
    assert intake["source_count"] == 18
    assert intake["captured_count"] == intake["unique_object_count"] == 10
    assert intake["failed_count"] == 8
    assert intake["total_unique_bytes"] == 18318626
    assert not intake["acquisition_complete"]
    holdings = summarize_holdings(observations)
    assert holdings["unique_original_count"] == 10
    assert holdings["unique_original_bytes"] == 18318626
    assert holdings["captured_original_occurrences"] == 18
    assert holdings["requested_source_record_count"] == 33
    assert holdings["failed_capture_record_count"] == 15
    assert holdings["repeated_original_occurrences"] == 8
    assert not holdings["historical_failures_resolved"]
    for spec in specs:
        request, capture = packet_metadata_paths(Path(spec.directory), spec, "original")
        assert sha256_file(request) == spec.request_sha256
        assert sha256_file(capture) == spec.capture_sha256
    summary = source_packets.render_summary({
        "status": "verified",
        "holdings": holdings,
    })
    assert "**10** distinct original byte objects" in summary
    assert "**15** historical failed" in summary
