import requests
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import os
import io
import subprocess
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich import print as rprint
import platform
from fuzzywuzzy import fuzz
from collections import defaultdict
import logging
from urllib.parse import urlparse
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='iptv_browser.log'
)


@dataclass
class IPTVChannel:
    name: str
    group: str
    url: str
    logo: Optional[str] = None
    epg_id: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None


class URLValidationError(Exception):
    pass


class VLCNotFoundError(Exception):
    pass


class PlaylistParsingError(Exception):
    pass


class IPTVBrowser:
    def __init__(self):
        self.playlist_url = None
        self.channels: List[IPTVChannel] = []
        self.console = Console()
        self.current_filter = None

    def validate_url(self, url: str) -> bool:
        """Validate URL format and accessibility"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logging.error(f"URL validation error: {e}")
            return False

    def setup_vlc(self) -> Tuple[str, bool]:
        """Setup and verify VLC installation"""
        system = platform.system()
        vlc_paths = {
            "Windows": [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
            ],
            "Darwin": [
                "/Applications/VLC.app/Contents/MacOS/VLC"
            ],
            "Linux": [
                "/usr/bin/vlc",
                "/usr/local/bin/vlc"
            ]
        }

        # Check if 'vlc' is in PATH
        vlc_in_path = shutil.which("vlc")
        if vlc_in_path:
            return vlc_in_path, True

        # Check system-specific paths
        if system in vlc_paths:
            for path in vlc_paths[system]:
                if os.path.isfile(path):
                    return path, True

        return "", False

    def fetch_playlist(self, url: str) -> bool:
        """Fetch and parse the M3U playlist with error handling"""
        try:
            if not self.validate_url(url):
                raise URLValidationError("Invalid URL format")

            self.playlist_url = url
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            content = response.text
            if not content.strip().startswith('#EXTM3U'):
                raise PlaylistParsingError("Invalid M3U format: Missing #EXTM3U header")

            self._parse_playlist(content)
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e}")
            raise
        except PlaylistParsingError as e:
            logging.error(f"Parsing error: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise

    def _parse_playlist(self, content: str):
        """Parse playlist content with error handling"""
        try:
            patterns = {
                'name': re.compile(r'tvg-name="([^"]*)"'),
                'group': re.compile(r'group-title="([^"]*)"'),
                'logo': re.compile(r'tvg-logo="([^"]*)"'),
                'epg_id': re.compile(r'tvg-id="([^"]*)"'),
                'country': re.compile(r'tvg-country="([^"]*)"'),
                'language': re.compile(r'tvg-language="([^"]*)"')
            }

            self.channels = []
            buffer = io.StringIO(content)
            buffer.readline()  # Skip #EXTM3U line

            extinf_line = None
            line_number = 1

            for line in buffer:
                line_number += 1
                line = line.strip()
                if not line:
                    continue

                if line.startswith('#EXTINF:'):
                    extinf_line = line
                elif extinf_line and not line.startswith('#'):
                    try:
                        name = patterns['name'].search(extinf_line)
                        name = name.group(1) if name else extinf_line.split(',')[-1].strip()

                        channel = IPTVChannel(
                            name=name,
                            group=patterns['group'].search(extinf_line).group(1) if patterns['group'].search(
                                extinf_line) else "Ungrouped",
                            url=line,
                            logo=patterns['logo'].search(extinf_line).group(1) if patterns['logo'].search(
                                extinf_line) else None,
                            epg_id=patterns['epg_id'].search(extinf_line).group(1) if patterns['epg_id'].search(
                                extinf_line) else None,
                            country=patterns['country'].search(extinf_line).group(1) if patterns['country'].search(
                                extinf_line) else None,
                            language=patterns['language'].search(extinf_line).group(1) if patterns['language'].search(
                                extinf_line) else None
                        )
                        self.channels.append(channel)
                    except Exception as e:
                        logging.warning(f"Error parsing channel at line {line_number}: {e}")
                    finally:
                        extinf_line = None

        except Exception as e:
            logging.error(f"Playlist parsing error: {e}")
            raise PlaylistParsingError(f"Failed to parse playlist: {e}")

    def search_channels(self, query: str) -> List[IPTVChannel]:
        """Search channels with error handling"""
        try:
            query = query.strip().lower()
            if not query:
                return []

            results = []
            for channel in self.channels:
                try:
                    ratio = fuzz.partial_ratio(query, channel.name.lower())
                    if ratio > 80:
                        results.append(channel)
                except Exception as e:
                    logging.warning(f"Error matching channel {channel.name}: {e}")
                    continue
            return results

        except Exception as e:
            logging.error(f"Search error: {e}")
            return []

    def play_channel(self, channel: IPTVChannel) -> bool:
        """Play channel with error handling"""
        try:
            vlc_path, vlc_exists = self.setup_vlc()
            if not vlc_exists:
                raise VLCNotFoundError("VLC media player not found")

            subprocess.Popen([vlc_path, channel.url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True

        except VLCNotFoundError as e:
            logging.error(f"VLC error: {e}")
            raise
        except Exception as e:
            logging.error(f"Playback error: {e}")
            raise

    def display_channels(self, channels: List[IPTVChannel]):
        """Display channels with error handling"""
        try:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim")
            table.add_column("Name")
            table.add_column("Group")
            table.add_column("Language", justify="right")

            for idx, channel in enumerate(channels, 1):
                try:
                    table.add_row(
                        str(idx),
                        channel.name,
                        channel.group or "N/A",
                        channel.language or "N/A"
                    )
                except Exception as e:
                    logging.warning(f"Error displaying channel {channel.name}: {e}")
                    continue

            self.console.print(table)

        except Exception as e:
            logging.error(f"Display error: {e}")
            self.console.print("[red]Error displaying channels[/red]")

    def group_channels(self) -> Dict[str, List[IPTVChannel]]:
        """Group channels with error handling"""
        try:
            groups = defaultdict(list)
            for channel in self.channels:
                groups[channel.group or "Ungrouped"].append(channel)
            return dict(groups)
        except Exception as e:
            logging.error(f"Grouping error: {e}")
            return {"Error": []}

    def main_menu(self):
        """Main menu with error handling"""
        while True:
            try:
                self.console.clear()
                self.console.print(Panel.fit(
                    "IPTV Browser\n\n"
                    "[1] View All Channels\n"
                    "[2] Browse by Group\n"
                    "[3] Search Channels\n"
                    "[4] Exit",
                    title="Main Menu"
                ))

                choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])

                if choice == "1":
                    self.browse_channels(self.channels)
                elif choice == "2":
                    self.browse_groups()
                elif choice == "3":
                    self.search_menu()
                elif choice == "4":
                    break

            except KeyboardInterrupt:
                if Prompt.ask("\nDo you want to exit?", choices=["y", "n"]) == "y":
                    break
            except Exception as e:
                logging.error(f"Menu error: {e}")
                self.console.print("[red]An error occurred. Please try again.[/red]")
                input("Press Enter to continue...")

    def browse_channels(self, channels: List[IPTVChannel]):
        """Browse channels with error handling"""
        while True:
            try:
                self.console.clear()
                self.display_channels(channels)
                choice = Prompt.ask("\nEnter channel number to play, 'b' for back", default="b")

                if choice.lower() == 'b':
                    break

                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(channels):
                        self.play_channel(channels[idx])
                    else:
                        self.console.print("[red]Invalid channel number[/red]")
                except ValueError:
                    self.console.print("[red]Invalid input[/red]")

            except KeyboardInterrupt:
                break
            except VLCNotFoundError:
                self.console.print("[red]Error: VLC media player not found[/red]")
                input("Press Enter to continue...")
            except Exception as e:
                logging.error(f"Browse error: {e}")
                self.console.print("[red]An error occurred. Please try again.[/red]")
                input("Press Enter to continue...")

    def browse_groups(self):
        """Browse groups with error handling"""
        try:
            groups = self.group_channels()
            while True:
                self.console.clear()
                for idx, group in enumerate(groups.keys(), 1):
                    self.console.print(f"[{idx}] {group} ({len(groups[group])} channels)")

                choice = Prompt.ask("\nSelect group number, 'b' for back", default="b")

                if choice.lower() == 'b':
                    break

                try:
                    idx = int(choice) - 1
                    group_name = list(groups.keys())[idx]
                    self.browse_channels(groups[group_name])
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid group number[/red]")

        except Exception as e:
            logging.error(f"Group browse error: {e}")
            self.console.print("[red]An error occurred while browsing groups[/red]")
            input("Press Enter to continue...")

    def search_menu(self):
        """Search menu with error handling"""
        while True:
            try:
                self.console.clear()
                query = Prompt.ask("\nEnter search term (or 'b' for back)")

                if query.lower() == 'b':
                    break

                results = self.search_channels(query)
                if results:
                    self.browse_channels(results)
                else:
                    self.console.print("[yellow]No channels found[/yellow]")
                    input("Press Enter to continue...")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Search error: {e}")
                self.console.print("[red]An error occurred during search[/red]")
                input("Press Enter to continue...")


def main():
    browser = IPTVBrowser()
    console = Console()

    while True:
        try:
            url = Prompt.ask("Enter M3U playlist URL (or 'q' to quit)")
            if url.lower() == 'q':
                break

            console.print("Validating and fetching playlist...")
            browser.fetch_playlist(url)

            if browser.channels:
                console.print(f"[green]Successfully loaded {len(browser.channels)} channels[/green]")
                browser.main_menu()
                break
            else:
                console.print("[yellow]No channels found in playlist[/yellow]")

        except URLValidationError:
            console.print("[red]Error: Invalid URL format[/red]")
        except requests.exceptions.RequestException:
            console.print("[red]Error: Could not fetch playlist. Check your internet connection and URL[/red]")
        except PlaylistParsingError:
            console.print("[red]Error: Invalid playlist format[/red]")
        except KeyboardInterrupt:
            if Prompt.ask("\nDo you want to quit?", choices=["y", "n"]) == "y":
                break
        except Exception as e:
            logging.error(f"Main error: {e}")
            console.print("[red]An unexpected error occurred[/red]")


if __name__ == "__main__":
    main()
