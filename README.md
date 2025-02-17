# IPTV Console Browser

A terminal-based IPTV playlist browser with VLC integration. Browse, search, and play channels from your M3U playlists.

## Features

- Rich terminal user interface
- Fuzzy channel search
- Group-based browsing
- VLC media player integration
- Cross-platform support
- Comprehensive error handling
- Activity logging

## Prerequisites

- Python 3.8+
- VLC media player
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/iptv-browser.git
cd iptv-browser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the browser:
```bash
python iptv_browser.py
```

2. Enter your M3U playlist URL when prompted

3. Navigate using the menu options:
   - View All Channels
   - Browse by Group
   - Search Channels

4. Select a channel to play it in VLC

## Controls

- Use number keys to select menu options
- Enter 'b' to go back to previous menu
- Ctrl+C to exit current view
- Enter 'q' at URL prompt to quit

## Logging

Logs are stored in `iptv_browser.log` in the application directory.

## Error Handling

The application handles:
- Invalid URLs
- Network connectivity issues
- Malformed playlists
- Missing VLC player
- Invalid user input

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, please create an issue in the GitHub repository.
