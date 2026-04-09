"""Tests for the main module and CLI endpoints."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from rtp_podcaster.__main__ import main, parse_args


def test_parse_args():
    """Verify that argparse binds to CLI parameters natively."""
    test_args = ["rtp-podcaster", "--output", "custom.xml", "--max-episodes", "5"]
    with patch.object(sys, "argv", test_args):
        parsed = parse_args()
        assert parsed.output == "custom.xml"
        assert parsed.max_episodes == 5


def test_parse_args_defaults():
    """Verify that argparse defaults map securely."""
    test_args = ["rtp-podcaster"]
    with patch.object(sys, "argv", test_args):
        parsed = parse_args()
        assert parsed.output is None
        assert parsed.show_url == "https://www.rtp.pt/play/p254/alta-tensao"
        assert parsed.max_episodes == 20
        assert parsed.force_refresh is False


@patch("rtp_podcaster.__main__.RSSGenerator")
@patch("rtp_podcaster.__main__.RTPPlayExtractor")
def test_main_no_new_episodes(mock_extractor_class, mock_generator_class):
    """Verify application exits securely on no new targets."""
    test_args = ["rtp-podcaster"]
    with patch.object(sys, "argv", test_args):
        mock_ext_instance = MagicMock()
        mock_gen_instance = MagicMock()

        mock_extractor_class.return_value = mock_ext_instance
        mock_generator_class.return_value = mock_gen_instance

        # Return empty master payload array
        mock_ext_instance.get_show_metadata.return_value = (
            "Alta Tensão",
            "https://example.com/image.jpg",
        )
        mock_ext_instance.get_episode_list.return_value = []
        mock_gen_instance.get_existing_guids.return_value = set()

        # Execute
        with pytest.raises(SystemExit) as exc:
            main()

        # Verification metrics
        assert exc.value.code == 0
        mock_ext_instance.get_episode_list.assert_called_once_with(max_episodes=20)
        # Verify execution terminates gracefully before executing structural maps
        mock_gen_instance.create_or_update_feed.assert_not_called()
        mock_ext_instance.extract_mp3_url.assert_not_called()
