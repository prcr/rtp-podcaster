"""Generator module for standard RSS 2.0 podcast feeds."""

import os
from datetime import datetime, timezone
from typing import Optional

import feedparser
from feedgen.feed import FeedGenerator

from rtp_podcaster.extractor import Episode


class RSSGenerator:
    """Generates an RSS 2.0 valid podcast XML stream natively applying podcast tags."""

    SHOW_NAME = "Alta Tensão"

    def __init__(self, program_id: int):
        """Initialize the generator with a specific RTP program catalog ID."""
        self.program_id = program_id
        self.show_url = f"https://www.rtp.pt/play/p{self.program_id}/alta-tensao"

    def get_existing_guids(self, feed_path: str) -> set[str]:
        """Return a set of episode GUIDs originally present inside the existing feed."""
        if not os.path.exists(feed_path):
            return set()

        guids = set()
        try:
            parsed = feedparser.parse(feed_path)
            for entry in parsed.entries:
                if "id" in entry:
                    guids.add(entry.id)
                elif "guid" in entry:
                    guids.add(entry.guid)
        except Exception as e:
            print(f"Warning: could not gracefully parse existing feed {feed_path}: {e}")

        return guids

    def create_or_update_feed(
        self,
        new_episodes: list[Episode],
        existing_feed_path: str,
        max_episodes: int = 20,
        force_refresh: bool = False,
        image_url: Optional[str] = None,
    ) -> None:
        """Parse external file, merge new elements natively, and securely dump to targets."""
        fg = FeedGenerator()
        fg.load_extension("podcast")

        fg.id(self.show_url)
        fg.title(self.SHOW_NAME)
        fg.link(href=self.show_url, rel="alternate")
        fg.description(f"Podcast feed for {self.SHOW_NAME} automatically generated from RTP Play.")
        fg.language("pt")

        if image_url:
            fg.image(image_url)

        all_entries_data = []

        # Read historical episodes first
        if not force_refresh and os.path.exists(existing_feed_path):
            try:
                parsed = feedparser.parse(existing_feed_path)
                for entry in parsed.entries:
                    enc_url = None
                    if hasattr(entry, "enclosures") and entry.enclosures:
                        enc_url = entry.enclosures[0].get("href")

                    all_entries_data.append(
                        {
                            "title": entry.get("title", "Unknown Title"),
                            "description": entry.get("description", ""),
                            "link": entry.get("link", ""),
                            "guid": entry.get("id", ""),
                            "enclosure_url": enc_url,
                            "pubDate": entry.get("published", None),
                        }
                    )
            except Exception as e:
                print(
                    f"Warning: failed building historical block map from {existing_feed_path}: {e}"
                )

        # Add new episodes sequentially
        for idx, ep in enumerate(new_episodes):
            if ep.mp3_url:
                all_entries_data.insert(
                    idx,
                    {
                        "title": ep.title,
                        "description": f"{ep.title} ({ep.date_str})",
                        "link": ep.url,
                        "guid": ep.guid,
                        "enclosure_url": ep.mp3_url,
                        "pubDate": ep.pub_date or datetime.now(timezone.utc),
                    },
                )

        # Apply maximum historic limitation logic natively
        all_entries_data = all_entries_data[:max_episodes]

        # Pipe combined datasets securely backward tracking mapping values gracefully
        for edata in reversed(all_entries_data):
            if not edata.get("enclosure_url"):
                continue

            fe = fg.add_entry()
            fe.id(str(edata["guid"]))
            fe.title(str(edata["title"]))
            fe.description(str(edata["description"]))
            fe.link(href=str(edata["link"]))

            # Explicit extension tag integrations
            fe.enclosure(edata["enclosure_url"], "0", "audio/mpeg")

            if edata.get("pubDate"):
                try:
                    fe.published(edata["pubDate"])
                except Exception:
                    pass

        # Make sure directory exists securely
        os.makedirs(os.path.dirname(os.path.abspath(existing_feed_path)), exist_ok=True)

        # Export mapping natively bypassing ET trees entirely
        fg.rss_file(existing_feed_path, pretty=True)
