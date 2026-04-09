"""Main entry point."""

import argparse
import sys

from rtp_podcaster.extractor import RTPPlayExtractor
from rtp_podcaster.generator import RSSGenerator


def parse_args() -> argparse.Namespace:
    """Prepare command line argument parser configurations."""
    parser = argparse.ArgumentParser(description="Generate RTP Play podcast feed.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for the XML feed. Defaults to public/p<program_id>_feed.xml",
    )
    parser.add_argument(
        "--program-id", type=int, default=254, help="Target RTP Play program ID configuration."
    )
    parser.add_argument(
        "--max-episodes", type=int, default=20, help="Maximum number of episodes to process."
    )
    parser.add_argument(
        "--ignore-existing",
        action="store_true",
        help="Disregard the historical feed metadata and seamlessly rebuild the entire feed natively.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute main generation procedure block."""
    args = parse_args()
    program_id = args.program_id

    # Calculate output string dynamically securely
    if not args.output:
        args.output = f"public/p{program_id}_feed.xml"

    extractor = RTPPlayExtractor(program_id=program_id)
    generator = RSSGenerator(program_id=program_id)

    print(f"Checking existing feed at {args.output}...")
    if args.ignore_existing:
        print("Flag --ignore-existing active: Rebuilding entirely from scratch.")
        guids = set()
    else:
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
        new_episodes,
        existing_feed_path=args.output,
        max_episodes=args.max_episodes,
        ignore_existing=args.ignore_existing,
    )

    print(f"Successfully generated new feed payload into {args.output}!")


if __name__ == "__main__":
    main()
