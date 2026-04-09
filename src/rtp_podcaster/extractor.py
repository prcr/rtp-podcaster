"""Extractor module for RTP Play episodes."""

import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class Episode:
    """Represents a single parsed RTP episode."""

    url: str
    title: str
    date_str: str
    guid: str
    mp3_url: Optional[str] = None


class RTPPlayExtractor:
    """Extracts podcast episodes from RTP Play."""

    BASE_URL = "https://www.rtp.pt"
    # User headers to impersonate regular browser activity
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Cookie": "rtp_cookie_parental=0; rtp_privacy=666; rtp_cookie_privacy=permit 1,2,3,4;",
    }

    def __init__(self, program_id: int):
        """Initialize the extractor with a specific RTP program catalog ID."""
        self.program_id = program_id
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        # Force HTTPAdapter standard networking config to prevent ipv6 environment hangs
        self.session.mount("https://", requests.adapters.HTTPAdapter())

    def fetch(self, url: str) -> str:
        """Fetch contents via internal session with robust timeout bindings."""
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text

    def get_episode_list(self, max_episodes: int = 20) -> list[Episode]:
        """Fetch the episode listing up to the maximum indicated count."""
        list_url = f"{self.BASE_URL}/play/bg_l_ep/?listProgram={self.program_id}&page=1"
        html = self.fetch(list_url)
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article")

        episodes: list[Episode] = []
        for article in articles:
            if len(episodes) >= max_episodes:
                break

            link = article.find("a")
            if not link:
                continue

            episode_url = self.BASE_URL + str(link["href"])
            title_el = article.find("p", class_="episode-title")
            date_el = article.find("div", class_="episode-date")

            title = title_el.get_text(strip=True) if title_el else "Unknown Title"
            date_str = date_el.get_text(strip=True) if date_el else ""

            episodes.append(
                Episode(url=episode_url, title=title, date_str=date_str, guid=episode_url)
            )

        return episodes

    def extract_mp3_url(self, episode_url: str) -> Optional[str]:
        """Parse an episode web page explicitly searching for the embedded MP3 payload."""
        html = self.fetch(episode_url)
        # Attempt standard JS player variable initialization match
        match = re.search(r'f\s*=\s*"(https?://[^"]+\.mp3[^"]*)"', html)
        if match:
            return str(match.group(1))

        # Fallback dictionary block parse strategy
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script"):
            text = script.string or ""
            candidate = re.search(
                r'"(?:file|src|url)"\s*:\s*"(https?://(?:cdn|streaming)[^"]+\.mp3)"',
                text,
                re.IGNORECASE,
            )
            if candidate:
                return str(candidate.group(1))

        return None
