"""Unit tests for the RTPPlayExtractor module."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from datetime import datetime, timezone

from rtp_podcaster.extractor import RTPPlayExtractor, parse_rtp_date, strip_query_string


def test_extractor_init():
    """Verify initialization parameters map securely."""
    extractor = RTPPlayExtractor(program_id=999)
    assert extractor.program_id == 999
    assert isinstance(extractor.session, requests.Session)
    assert extractor.session.headers["User-Agent"] == RTPPlayExtractor.HEADERS["User-Agent"]


@patch("requests.Session.get")
def test_fetch_success(mock_get):
    """Test fetch function successfully reads HTTP responses natively."""
    mock_response = MagicMock()
    mock_response.text = "<html>Success</html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    extractor = RTPPlayExtractor(program_id=1)
    result = extractor.fetch("http://test.url")

    mock_get.assert_called_once_with("http://test.url", timeout=15)
    mock_response.raise_for_status.assert_called_once()
    assert result == "<html>Success</html>"


@patch("requests.Session.get")
def test_fetch_failure(mock_get):
    """Test fetch correctly propogates HTTP status failures."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response

    extractor = RTPPlayExtractor(program_id=1)

    with pytest.raises(requests.exceptions.HTTPError, match="404 Not Found"):
        extractor.fetch("http://test.url")


@patch.object(RTPPlayExtractor, "fetch")
def test_get_episode_list(mock_fetch):
    """Mock standard BS4 parsing capabilities logic over predefined HTML payloads."""
    # Dummy HTML reflecting RTP Play structures
    raw_html = """
    <html>
        <body>
            <article>
                <a href="/play/p123/episode-test1">Link</a>
                <p class="episode-title">First Episode Title</p>
                <div class="episode-date">10 Abr. 2026</div>
            </article>
            <article>
                <a href="/play/p123/episode-test2">Link</a>
                <p class="episode-title">Second Episode Title</p>
                <div class="episode-date">11 Abr. 2026</div>
            </article>
            <article>
                <p class="episode-title">Orphaned Episode No Link</p>
            </article>
        </body>
    </html>
    """
    mock_fetch.return_value = raw_html

    extractor = RTPPlayExtractor(program_id=123)
    episodes = extractor.get_episode_list(max_episodes=2)

    assert mock_fetch.called
    assert len(episodes) == 2
    assert episodes[0].title == "First Episode Title"
    assert episodes[0].url == "https://www.rtp.pt/play/p123/episode-test1"
    assert episodes[0].date_str == "10 Abr. 2026"

    # Verify length limiter works successfully
    episodes_limited = extractor.get_episode_list(max_episodes=1)
    assert len(episodes_limited) == 1
    assert episodes_limited[0].title == "First Episode Title"


@patch.object(RTPPlayExtractor, "fetch")
def test_extract_mp3_url_primary_method(mock_fetch):
    """Try grabbing audio payloads off standard regex scripts mapping."""
    mock_html = '<html><script>var block; f = "https://cdn.rtp.pt/test.mp3"; </script></html>'
    mock_fetch.return_value = mock_html

    extractor = RTPPlayExtractor(program_id=1)
    url = extractor.extract_mp3_url("http://test.url")

    assert url == "https://cdn.rtp.pt/test.mp3"


@patch.object(RTPPlayExtractor, "fetch")
def test_extract_mp3_url_fallback_method(mock_fetch):
    """Test backup BS4 JSON block scraping fallback behavior."""
    mock_html = '<html><script>{"file": "https://streaming.rtp.pt/fallback.mp3"}</script></html>'
    mock_fetch.return_value = mock_html

    extractor = RTPPlayExtractor(program_id=1)
    url = extractor.extract_mp3_url("http://test.url")

    assert url == "https://streaming.rtp.pt/fallback.mp3"


@patch.object(RTPPlayExtractor, "fetch")
def test_extract_mp3_url_not_found(mock_fetch):
    """Test behavior if no mp3 string structure matches."""
    mock_html = "<html><body>No files here!</body></html>"
    mock_fetch.return_value = mock_html

    extractor = RTPPlayExtractor(program_id=1)
    url = extractor.extract_mp3_url("http://test.url")

    assert url is None


def test_parse_rtp_date():
    """Verify Portuguese date structure parsed correctly to UTC timestamp structures."""
    # Standard format validation parameters
    valid_date = parse_rtp_date("06 abr. 2026")
    assert valid_date is not None
    assert valid_date == datetime(2026, 4, 6, 0, 0, 0, tzinfo=timezone.utc)

    # Capitalized edgecase parameters gracefully handle correctly
    cap_date = parse_rtp_date("31 JAN 2025")
    assert cap_date is not None
    assert cap_date == datetime(2025, 1, 31, 0, 0, 0, tzinfo=timezone.utc)

    # Missing formatting variables safely fallback cleanly
    invalid = parse_rtp_date("Broken Date Value")
    assert invalid is None


def test_strip_query_string():
    """Verify query strings and fragments are removed from URLs correctly."""
    assert (
        strip_query_string("https://cdn.rtp.pt/image.jpg?w=100&h=100")
        == "https://cdn.rtp.pt/image.jpg"
    )
    assert strip_query_string("https://cdn.rtp.pt/image.jpg") == "https://cdn.rtp.pt/image.jpg"
    assert (
        strip_query_string("https://cdn.rtp.pt/image.jpg#anchor") == "https://cdn.rtp.pt/image.jpg"
    )


@patch.object(RTPPlayExtractor, "fetch")
def test_get_show_metadata(mock_fetch):
    """Verify og:title and og:image meta tags are extracted and transformed correctly."""
    mock_fetch.return_value = """
    <html>
        <head>
            <meta property="og:title" content="Alta Tensão - RTP Play" />
            <meta property="og:image" content="https://cdn-images.rtp.pt/EPG/radio/imagens/1068_12880_9537.jpg?w=200" />
        </head>
    </html>
    """
    extractor = RTPPlayExtractor(program_id=254)
    show_name, image_url = extractor.get_show_metadata(program_id=254)
    assert show_name == "Alta Tensão"
    assert image_url == "https://cdn-images.rtp.pt/EPG/radio/imagens/1068_12880_9537.jpg"


@patch.object(RTPPlayExtractor, "fetch")
def test_get_show_metadata_missing(mock_fetch):
    """Verify (None, None) is returned when og meta tags are absent."""
    mock_fetch.return_value = "<html><head></head></html>"
    extractor = RTPPlayExtractor(program_id=254)
    show_name, image_url = extractor.get_show_metadata(program_id=254)
    assert show_name is None
    assert image_url is None
