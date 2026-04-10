"""Main entry point."""

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from rtp_podcaster.extractor import Episode, RTPPlayExtractor, extract_program_id
from rtp_podcaster.generator import RSSGenerator


def parse_args() -> argparse.Namespace:
    """Prepare command line argument parser configurations."""
    parser = argparse.ArgumentParser(description="Generate RTP Play podcast feed.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output filename for the XML feed. Defaults to p<program_id>_feed.xml (always placed in public/rtp-podcaster/)",
    )
    parser.add_argument(
        "--show-url",
        type=str,
        default="https://www.rtp.pt/play/p254/alta-tensao",
        help="Full URL of the RTP Play show page.",
    )
    parser.add_argument(
        "--max-episodes", type=int, default=128, help="Maximum number of episodes to process."
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Disregard the historical feed metadata and seamlessly rebuild the entire feed natively.",
    )
    return parser.parse_args()


def process_episode_metadata(
    ep: Episode, extractor: RTPPlayExtractor, logger: logging.Logger
) -> None:
    """Worker function to fetch metadata for a single episode."""
    mp3, desc = extractor.extract_episode_metadata(ep.url)
    if mp3:
        ep.mp3_url = mp3
    else:
        logger.warning("Could not locate mp3 URL for '%s' at %s", ep.title, ep.url)

    if desc:
        ep.description = desc


def main() -> None:
    """Execute main generation procedure block."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    args = parse_args()
    show_url = args.show_url
    program_id = extract_program_id(show_url)

    # Calculate output path from the program ID derived from the show URL
    # All feeds are consistently created under the project subdirectory
    out_dir = "public/rtp-podcaster"
    out_file = args.output or f"p{program_id}_feed.xml"

    # Enforce a flat filename structure inside the target directory
    args.output = os.path.join(out_dir, os.path.basename(out_file))

    extractor = RTPPlayExtractor(show_url=show_url)

    logger.info("Fetching show metadata...")
    show_name, image_url = extractor.get_show_metadata()
    if show_name:
        logger.info("Found show name: %s", show_name)
    else:
        logger.warning("Could not find show name, using default.")
    if image_url:
        logger.info("Found show image: %s", image_url)
    else:
        logger.warning("Could not find show image URL.")

    generator = RSSGenerator(show_url=show_url, show_name=show_name)

    logger.info("Checking existing feed at %s...", args.output)
    if args.force_refresh:
        logger.info("Flag --force-refresh active: Rebuilding entirely from scratch.")
        guids = set()
    else:
        guids = generator.get_existing_guids(args.output)

    logger.info("Loaded %d known episodes.", len(guids))

    logger.info("Fetching master list of recent episodes from RTP Play...")
    all_episodes = extractor.get_episode_list(max_episodes=args.max_episodes)
    logger.info("Found %d recent entries.", len(all_episodes))

    new_episodes = []
    for ep in all_episodes:
        if ep.guid not in guids:
            new_episodes.append(ep)

    if not new_episodes:
        logger.info("No new episodes found. Feed is up to date!")
        sys.exit(0)

    logger.info("Processing %d new episodes...", len(new_episodes))

    # Process episodes in parallel to speed up metadata extraction
    # Using 4 workers to balance speed and server respect
    with ThreadPoolExecutor(max_workers=4) as executor:
        for ep in new_episodes:
            executor.submit(process_episode_metadata, ep, extractor, logger)

    # Build and write xml wrapper natively
    generator.create_or_update_feed(
        new_episodes,
        existing_feed_path=args.output,
        max_episodes=args.max_episodes,
        force_refresh=args.force_refresh,
        image_url=image_url,
    )

    logger.info("Successfully generated new feed payload into %s!", args.output)


if __name__ == "__main__":
    main()
