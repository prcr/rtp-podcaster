"""Live integration testing interacting securely with RTP websites."""

import pytest

from rtp_podcaster.extractor import RTPPlayExtractor, parse_rtp_date


@pytest.mark.live
def test_live_episode_extraction():
    """Verify live extraction successfully navigates RTP ecosystem natively."""
    extractor = RTPPlayExtractor(program_id=254)
    # Target heavily minimized page bounds limiting remote requests securely
    episodes = extractor.get_episode_list(max_episodes=2)

    assert len(episodes) > 0
    assert len(episodes) <= 2

    # Map generic properties validating DOM boundaries don't drift away
    first_ep = episodes[0]
    assert first_ep.title is not None
    assert first_ep.title != "Unknown Title"
    assert "https://www.rtp.pt/play" in first_ep.url
    assert parse_rtp_date(first_ep.date_str) is not None, (
        f"Failed to parse date from string: '{first_ep.date_str}'"
    )

    # Check structural audio resolutions manually mapped into real endpoints
    mp3_url = extractor.extract_mp3_url(first_ep.url)

    assert mp3_url is not None
    assert mp3_url.startswith("http")
    assert ".mp3" in mp3_url.lower()

    # Check show image URL is fetched cleanly without query strings
    image_url = extractor.get_show_image_url(program_id=254)
    assert image_url is not None, "Could not find show image URL in og:image meta tag."
    assert image_url.startswith("http")
    assert "?" not in image_url, f"Image URL still contains a query string: '{image_url}'"
