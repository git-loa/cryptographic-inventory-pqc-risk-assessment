"""
Test domain loader functionality.
"""


def test_all_domains_fixture(all_domains):
    """
    Test that the all_domains fixture correctly combines
    built-in and test file domains.
    """
    assert isinstance(all_domains, list)
    assert len(all_domains) >= 2
    assert "example.com" in all_domains
    assert "google.com" in all_domains
