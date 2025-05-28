# Anime Episode Scraper

A robust Python scraper that collects streaming links and metadata for anime episodes from popular Indian anime websites, including:

* Toonstream
* AnimeDekho
* AniTown4u
* HindiSubAnime
* HindiAnimeVerse
* WatchAnimeWorld
* ToonsHub
* TamilToon

Supports optional TMDB integration for retrieving official episode titles.

## Features

* Multi-source scraping from major Indian anime streaming sites
* Automatic extraction of streaming links
* Concurrent scraping for faster performance
* TMDB integration to fetch official episode names
* JSON output with metadata
* Configurable via a simple JSON file

## Requirements

* Python 3.8+
* Dependencies listed in `requirements.txt`:

  ```bash
  pip install requests beautifulsoup4 tqdm colorama
  ```

## Usage

```bash
python main.py
```

### Input

* Episode 1 URL (from one of the supported sites)
* Number of seasons and episodes per season
* Optional: TMDB API Key and Series ID
* Optional: Enable concurrent scraping

### Output

* A JSON file containing episode streaming URLs, providers, and optional TMDB episode names.

## Configuration

* The script uses `config.json` to store the TMDB API key and series ID for reuse.

## Example Output

```json
{
  "metadata": {
    "source": "https://example.com",
    "scraped_at": "2025-05-22 12:00:00 UTC",
    "script_version": "3.0",
    "total_episodes": 12,
    "seasons": {
      "1": 12
    }
  },
  "episodes": [
    {
      "Season": 1,
      "Episode": 1,
      "Title": "Episode 1 Title",
      "Details": [
        {
          "Provider Host": "provider.com",
          "Url": "https://provider.com/stream"
        }
      ],
      "TMDB Name": "TMDB Episode Title"
    }
  ]
}
```

## Notes

* TMDB integration is optional but recommended for better episode labeling.
* Some sources like AniTown4u have fixed season structure (season 1 only).

## License

MIT License

---

**Author:** \[ToonTamilIndia]
**Version:** 3.0
