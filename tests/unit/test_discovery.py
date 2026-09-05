from australian_health_policy_atlas.discovery import discover_links


def test_discovery_is_same_host_and_deduplicated() -> None:
    html = '<a href="/a.pdf">Policy</a><a href="/a.pdf">Again</a><a href="https://other.test/b.pdf">Other</a>'
    links = discover_links(html, base_url="https://health.test/root")
    assert [item.url for item in links] == ["https://health.test/a.pdf"]
    assert links[0].likely_document
