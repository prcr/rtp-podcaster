"""Main entry point."""

import argparse
import sys

from rtp_podcaster.extractor import RTPPlayExtractor
from rtp_podcaster.generator import RSSGenerator


def parse_args() -> argparse.Namespace:
    """Prepare command line argument parser configurations."""
    parser = argparse.ArgumentParser(description="Generate RTP Play podcast feed.")
    parser.add_argument(
        "--output", type=str, default="public/feed.xml", help="Output path for the XML feed."
    )
    parser.add_argument(
        "--max-episodes", type=int, default=20, help="Maximum number of episodes to process."
    )
    return parser.parse_args()


def main() -> None:
    """Execute main generation procedure block."""
    args = parse_args()
    program_id = 254

    extractor = RTPPlayExtractor(program_id=program_id)
    generator = RSSGenerator(program_id=program_id)

    print(f"Checking existing feed at {args.output}...")
    guids = generator.get_existing_guids(args.output)
    print(f"Loaded {len(guids)} known episodes.")

    print("Fetching master list of recent episodes from RTP Play...")
    all_episodes = extractor.get_episode_list(max_episodes=args.max_episodes)
    print(f"Found {len(all_episodes)} recent entries.")

    new_episodes = []
    for ep in all_episodes:
        if ep.guid not in guids:
            new_episodes.append(ep)

    if not new_episodes:
        print("No new episodes found. Feed is up to date!")
        sys.exit(0)

    print(f"Processing {len(new_episodes)} new episodes...")
    for ep in new_episodes:
        mp3 = extractor.extract_mp3_url(ep.url)
        if mp3:
            ep.mp3_url = mp3
        else:
            print(f"WARN: Could not locate mp3 URL for '{ep.title}' at {ep.url}")

    # Build and write xml wrapper natively
    generator.create_or_update_feed(
        new_episodes, existing_feed_path=args.output, max_episodes=args.max_episodes
    )

    print(f"Successfully generated new feed payload into {args.output}!")


if __name__ == "__main__":
    main()
