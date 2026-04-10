"""Main entry point."""

import argparse
import os
import sys

from rtp_podcaster.extractor import RTPPlayExtractor, extract_program_id
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


def main() -> None:
    """Execute main generation procedure block."""
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

    print("Fetching show metadata...")
    show_name, image_url = extractor.get_show_metadata()
    if show_name:
        print(f"Found show name: {show_name}")
    else:
        print("Warning: Could not find show name, using default.")
    if image_url:
        print(f"Found show image: {image_url}")
    else:
        print("Warning: Could not find show image URL.")

    generator = RSSGenerator(show_url=show_url, show_name=show_name)

    print(f"Checking existing feed at {args.output}...")
    if args.force_refresh:
        print("Flag --force-refresh active: Rebuilding entirely from scratch.")
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
        force_refresh=args.force_refresh,
        image_url=image_url,
    )

    print(f"Successfully generated new feed payload into {args.output}!")


if __name__ == "__main__":
    main()
