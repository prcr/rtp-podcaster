"""Generator module for standard RSS 2.0 podcast feeds."""

import os
import xml.etree.ElementTree as ET
from email.utils import formatdate

from rtp_podcaster.extractor import Episode


class RSSGenerator:
    """Generates an RSS 2.0 valid podcast XML stream."""

    SHOW_NAME = "Alta Tensão"

    def __init__(self, program_id: int):
        """Initialize the generator with a specific RTP program catalog ID."""
        self.program_id = program_id
        self.show_url = f"https://www.rtp.pt/play/p{self.program_id}/alta-tensao"

    def get_existing_guids(self, feed_path: str) -> set[str]:
        """Return a set of episode GUIDs already present in the local feed instance."""
        if not os.path.exists(feed_path):
            return set()
        try:
            tree = ET.parse(feed_path)
            root = tree.getroot()
            guids = set()
            for item in root.findall("./channel/item"):
                guid_el = item.find("guid")
                if guid_el is not None and guid_el.text:
                    guids.add(guid_el.text.strip())
            return guids
        except Exception as e:
            print(f"Warning: could not parse existing feed {feed_path}: {e}")
            return set()

    def create_new_feed_root(self) -> tuple[ET.Element, ET.Element]:
        """Bootstrap completely clean standard XML headers and structure."""
        rss = ET.Element("rss", version="2.0")
        rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")

        channel = ET.SubElement(rss, "channel")
        title = ET.SubElement(channel, "title")
        title.text = self.SHOW_NAME

        link = ET.SubElement(channel, "link")
        link.text = self.show_url

        desc = ET.SubElement(channel, "description")
        desc.text = f"Podcast feed for {self.SHOW_NAME} automatically generated from RTP Play."

        lang = ET.SubElement(channel, "language")
        lang.text = "pt"

        return rss, channel

    def create_or_update_feed(
        self, episodes: list[Episode], existing_feed_path: str, max_episodes: int = 20
    ) -> None:
        """Update or create the RSS feed file containing validated episode wrappers."""
        if os.path.exists(existing_feed_path):
            try:
                tree = ET.parse(existing_feed_path)
                root = tree.getroot()
                channel = root.find("channel")
            except Exception:
                root, channel = self.create_new_feed_root()
                tree = ET.ElementTree(root)
        else:
            root, channel = self.create_new_feed_root()
            tree = ET.ElementTree(root)

        if channel is None:
            raise RuntimeError("Invalid feed format: no channel element.")

        # Find insertion position (beneath header metadata)
        insert_idx = len(channel)
        for i, child in enumerate(list(channel)):
            if child.tag == "item":
                insert_idx = i
                break

        # Append backwardly to keep newest targets actively at the top pointer
        for ep in reversed(episodes):
            if not ep.mp3_url:
                continue

            item = ET.Element("item")

            title = ET.SubElement(item, "title")
            title.text = ep.title

            desc = ET.SubElement(item, "description")
            desc.text = f"{ep.title} ({ep.date_str})"

            link = ET.SubElement(item, "link")
            link.text = ep.url

            guid = ET.SubElement(item, "guid")
            guid.text = ep.guid

            enclosure = ET.SubElement(item, "enclosure")
            enclosure.set("url", ep.mp3_url)
            enclosure.set("type", "audio/mpeg")

            pubDate = ET.SubElement(item, "pubDate")
            pubDate.text = formatdate(timeval=None, localtime=False, usegmt=True)

            channel.insert(insert_idx, item)

        # Enforce history limit parameter
        items = channel.findall("item")
        if len(items) > max_episodes:
            for old_item in items[max_episodes:]:
                channel.remove(old_item)

        ET.indent(tree, space="  ", level=0)

        # Ensure directory path is initialized before XML compilation
        os.makedirs(os.path.dirname(os.path.abspath(existing_feed_path)), exist_ok=True)

        tree.write(existing_feed_path, encoding="UTF-8", xml_declaration=True)
