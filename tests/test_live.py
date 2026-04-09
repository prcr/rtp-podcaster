"""Live integration testing interacting securely with RTP websites."""

import pytest

from rtp_podcaster.extractor import RTPPlayExtractor


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
    assert first_ep.pub_date is not None, f"Failed to parse date from string: '{first_ep.date_str}'"

    # Check structural audio resolutions manually mapped into real endpoints
    mp3_url = extractor.extract_mp3_url(first_ep.url)

    assert mp3_url is not None
    assert mp3_url.startswith("http")
    assert ".mp3" in mp3_url.lower()
