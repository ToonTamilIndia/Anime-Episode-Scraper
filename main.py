import requests
from bs4 import BeautifulSoup
import json
import concurrent.futures
import os
from tqdm import tqdm
import re
from urllib.parse import urlparse
import base64
import sys
from colorama import Fore, Style, init
from functools import wraps
import time
import getpass
from typing import Dict, List, Optional, Tuple
import random


init()


VERSION = "3.0"
CONFIG_FILE = "config.json"
DEFAULT_MAX_WORKERS = 5
TMDB_API_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 1


GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
CYAN = Fore.CYAN
RESET = Style.RESET_ALL

def print_header():

    print(f"\n{CYAN}{'=' * 80}")
    print(f"Toonstream, AnimeDekho, HindiAnimeVerse, AniTown4u, HindiSubAnime Scraper".center(80))
    print(f"{'=' * 80}{RESET}")
    print(f"{YELLOW}Version: {VERSION}{RESET}")

def retry(max_retries: int = MAX_RETRIES, delay: int = RETRY_DELAY):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"{YELLOW}Retry {retries + 1}/{max_retries} for {func.__name__}: {e}{RESET}")
                    time.sleep(delay * (retries + 1)) 
                    retries += 1
            raise Exception(f"{RED}Max retries ({max_retries}) exceeded{RESET}")
        return wrapper
    return decorator


def decode_embed_id(embed_id: str) -> str:
    try:
        
        if ':' in embed_id:
            _, encoded_url = embed_id.split(':', 1)
            return base64.b64decode(encoded_url).decode("utf-8")
    except Exception as e:
        print(f"Error decoding embed id: {e}")
    return ""

class TMDBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json"
        })
        self.episode_cache: Dict[Tuple[int, int], str] = {}

    @retry()
    def validate_api_key(self) -> bool:

        try:
            response = self.session.get(f"{TMDB_API_URL}/account", timeout=REQUEST_TIMEOUT)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @retry()
    def get_episode_name(self, series_id: str, season: int, episode: int) -> str:
    
        cache_key = (season, episode)
        if cache_key in self.episode_cache:
            return self.episode_cache[cache_key]

        try:
            url = f"{TMDB_API_URL}/tv/{series_id}/season/{season}/episode/{episode}"
            response = self.session.get(url, params={"language": "en-US"}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            name = data.get("name", "Unknown Episode")
            self.episode_cache[cache_key] = name
            return name
        except requests.RequestException as e:
            print(f"{YELLOW}TMDB Error: {e}{RESET}")
            return "Unknown Episode"

class Scraper:
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:122.0) Gecko/20100101 Firefox/122.0"
        })

    @retry()
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            print(f"{RED}Failed to fetch {url}: {e}{RESET}")
            return None

    def extract_animedekho_details(self, url: str) -> List[Dict[str, str]]:
 
        try:
            soup = self.fetch_page(url)
            if not soup:
                return []

            body_class = " ".join(soup.select_one("body").get("class", []))
            match = re.search(r"(?:term|postid)-(\d+)", body_class)
            if not match:
                print(f"{YELLOW}No term/postid found in body class{RESET}")
                return []

            term = match.group(1)
            results = []
            
 
            for i in range(5):
                try:
                    dynamic_url = f"https://animedekho.co/?trdekho={i}&trid={term}&trtype=2"
                    iframe_soup = self.fetch_page(dynamic_url)
                    if iframe := iframe_soup.select_one("iframe[src]"):
                        src = iframe["src"]
                        results.append({
                            "Provider Host": urlparse(src).netloc,
                            "Url": src
                        })
                except Exception as e:
                    continue

            return results
        except Exception as e:
            print(f"{RED}Animedekho error: {e}{RESET}")
            return []
    def extract_anime4u_details(self, url: str) -> List[Dict[str, str]]:
        try:
            soup = self.fetch_page(url)
            if not soup:
                return []

            results = []

            player_spans = soup.select("div.player-selection span[data-dub-name][data-embed-id]")
            for span in player_spans:
                try:
                    provider = span["data-dub-name"].strip()
                    embed_id = span["data-embed-id"]
                    base_urls = [
                    "https://anitown4u.com",
                    "https://app-123.anitown4u.com"
                ]
                    stream_url = random.choice(base_urls) + decode_embed_id(embed_id)
                    if stream_url:
                        results.append({
                            "Provider Host": provider,
                            "Url": stream_url
                        })
                except Exception as e:
                    print(f"{YELLOW}Skipping player span: {e}{RESET}")

            return results

        except Exception as e:
            print(f"{RED}Generic scrape error: {e}{RESET}")
            return []
    
        
        
    
    def extract_hindisubanime_details(self, url: str) -> List[Dict[str, str]]:
 
        try:
            
            soup = self.fetch_page(url)
            if not soup:
                return []

            body_class = " ".join(soup.select_one("body").get("class", []))
            match = re.search(r"(?:term|postid)-(\d+)", body_class)
            if not match:
                print(f"{YELLOW}No term/postid found in body class{RESET}")
                return []

            term = match.group(1)
            results = []
            
 
            for i in range(5):
                try:
                    dynamic_url = f"https://hindisubanime.co/?trdekho={i}&trid={term}&trtype=2"
                    iframe_soup = self.fetch_page(dynamic_url)
                    if iframe := iframe_soup.select_one("iframe[src]"):
                        src = iframe["src"]
                        results.append({
                            "Provider Host": urlparse(src).netloc,
                            "Url": src
                        })
                except Exception as e:
                    continue

            return results
        except Exception as e:
            print(f"{RED}HindiSubAnime error: {e}{RESET}")
            return []
    def extract_hindianimeverse_details(self, url: str) -> List[Dict[str, str]]:
 
        try:
            
            soup = self.fetch_page(url)
            if not soup:
                return []
            player_options = soup.find_all('li', class_='dooplay_player_option')
            results = []
            for option in player_options:
                data_post = option.get('data-post')
                data_type = option.get('data-type')
                data_nume = option.get('data-nume')

                post_data = {
                "action": "doo_player_ajax",
                "post": data_post,
                "nume": data_nume,
                "type": data_type
                }
                ajax_url = "https://hindianimeverse.org/wp-admin/admin-ajax.php"

                r = requests.post(ajax_url, data=post_data)
                if r.status_code == 200:
                    json_data = r.json()
                    embed_url = json_data.get('embed_url')
                    if embed_url:
                        results.append({
                                "Provider Host": urlparse(embed_url).netloc,
                                "Url": embed_url
                            })
            return results
        except Exception as e:
            print(f"{RED}HindiAnimeverse error: {e}{RESET}")
            return []

    def scrape_generic(self, url: str) -> List[Dict[str, str]]:

        try:
            soup = self.fetch_page(url)
            if not soup:
                return []

            iframes = []
            for iframe in soup.select("iframe[data-src]"):
                try:
                    src = iframe["data-src"]
                    iframe_soup = self.fetch_page(src)
                    if nested_iframe := iframe_soup.select_one("iframe[src]"):
                        host = urlparse(nested_iframe["src"]).netloc
                        iframes.append({"Provider Host": host, "Url": nested_iframe["src"]})
                except Exception as e:
                    print(f"{YELLOW}Skipping iframe: {e}{RESET}")

            return iframes
        except Exception as e:
            print(f"{RED}Generic scrape error: {e}{RESET}")
            return []

    def get_episode_data(self, url: str) -> Optional[Dict]:

        try:
            if "animedekho" in url:
                details = self.extract_animedekho_details(url)
                title = self.extract_title(url, " - AnimeDekho")
            elif "hindisubanime" in url:
                details = self.extract_hindisubanime_details(url)
                title = self.extract_title(url, " - Hindi Sub Anime")
            elif "anitown4u" in url:
                details = self.extract_anime4u_details(url)
                title = self.extract_title(url, " – AniTown4U")
            elif "hindianimeverse" in url:
                details = self.extract_hindianimeverse_details(url)
                title = self.extract_title(url, " | Hindi Anime Verse")
                title = title.replace("Watch & Download ", "").replace(" Free", "").strip()
            else:
                details = self.scrape_generic(url)
                title = self.extract_title(url, " - Toonstream")

            return {"Title": title, "Details": details} if details else None
        except Exception as e:
            print(f"{RED}Scrape failed for {url}: {e}{RESET}")
            return None

    def extract_title(self, url: str, suffix: str) -> str:
       
        soup = self.fetch_page(url)
        title = soup.title.string if soup and soup.title else url.split("/")[-1]
        return title.replace(suffix, "").replace("Watch Online ", "").strip()

def load_config() -> Dict:
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"{YELLOW}Invalid config file, using defaults{RESET}")
    return {}

def save_config(config: Dict):
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def validate_url(url: str) -> bool:
    
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc]) and any(
        domain in parsed.netloc for domain in ["toonstream", "animedekho", "hindisubanime", "anitown4u", "hindianimeverse"]
    )

def generate_episode_urls(base_url: str, seasons: Dict[int, int]) -> List[Tuple[str, int, int]]:
    
    urls = []
    base_slug = re.search(r"(.+-\d+x)\d+$", base_url)
    if not base_slug:
        print(f"{RED}Invalid episode URL format{RESET}")
        sys.exit(1)

    slug_prefix = base_slug.group(1)
    
    for season, episodes in seasons.items():
        for ep in range(1, episodes + 1):
            episode_url = f"{base_url.rsplit('-', 1)[0]}-{season}x{ep}"
            urls.append((episode_url, season, ep))
    
    return urls

def gen_episode_urls(base_url: str, seasons: Dict[int, int]) -> List[Tuple[str, int, int]]:
    urls = []
    
    match = re.match(r"(.*-episode-)\d+$", base_url)
    if not match:
        print(f"{RED}Invalid episode URL format{RESET}")
        return []

    base_slug = match.group(1)
    for season, episodes in seasons.items():
        for ep in range(1, episodes + 1):
            episode_url = f"{base_slug}{ep}"
            urls.append((episode_url,season, ep))
    
    
    return urls



def main():
    print_header()
    config = load_config()
    scraper = Scraper()

    
    base_url = input(f"{CYAN}Enter episode 1 URL: {RESET}").strip()
    while not validate_url(base_url):
        print(f"{RED}Invalid URL format - must be ToonStream, AniTown4u, HindiSubAnime, HindiAnimeverse or AnimeDekho{RESET}")
        base_url = input(f"{CYAN}Enter episode 1 URL: {RESET}").strip()

    base_url = base_url[:-1] if base_url.endswith("/") else base_url

    seasons = {}
    while True:
        try:
            if "anitown4u" not in base_url:
                season = int(input(f"{CYAN}Enter season number: {RESET}"))
            if "anitown4u" in base_url:
                season = 1
            episodes = int(input(f"{CYAN}Episodes in season {season}: {RESET}"))
            seasons[season] = episodes
            if "anitown4u" not in base_url:
               if input(f"{CYAN}Add another season? (y/n): {RESET}").lower() != "y":
                 break
            else:
                break
        except ValueError:
            print(f"{RED}Invalid number input{RESET}")

    
    tmdb_client = None
    if input(f"{CYAN}Enable TMDB integration? (y/n): {RESET}").lower() == "y":
        api_key = config.get("tmdb_api_key") or getpass.getpass(f"{CYAN}TMDB API key: {RESET}")
        tmdb_client = TMDBClient(api_key)
        
        if not tmdb_client.validate_api_key():
            print(f"{RED}Invalid TMDB API key{RESET}")
            tmdb_client = None
        else:
            series_id = input(f"{CYAN}TMDB Series ID: {RESET}").strip()
            config.update({"tmdb_api_key": api_key, "tmdb_series_id": series_id})
            save_config(config)

    
    use_concurrent = input(f"{CYAN}Enable concurrent processing? (y/n): {RESET}").lower() == "y"
    max_workers = DEFAULT_MAX_WORKERS
    if use_concurrent:
        try:
            max_workers = int(input(f"{CYAN}Max workers (1-20) [5]: {RESET}") or 5)
            max_workers = max(1, min(20, max_workers))
        except ValueError:
            max_workers = DEFAULT_MAX_WORKERS

    
    results = []
    if "anitown4u" in base_url:
        urls = gen_episode_urls(base_url, seasons)
    else:
        urls = generate_episode_urls(base_url, seasons)
    
    total_episodes = sum(seasons.values())
    
    print(f"\n{GREEN}Starting scrape for {total_episodes} episodes across {len(seasons)} seasons{RESET}")
    
    with tqdm(total=total_episodes, desc="Scraping", unit="ep") as pbar:
        if use_concurrent:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(scraper.get_episode_data, url): (s, e) 
                          for url, s, e in urls}
                for future in concurrent.futures.as_completed(futures):
                    season, episode = futures[future]
                    try:
                        data = future.result()
                        if data:
                            if tmdb_client:
                                ep_name = tmdb_client.get_episode_name(
                                    config.get("tmdb_series_id", ""),
                                    season,
                                    episode
                                )
                                data["TMDB Name"] = ep_name
                            results.append({
                                "Season": season,
                                "Episode": episode,
                                **data
                            })
                    except Exception as e:
                        print(f"{RED}Processing error: {e}{RESET}")
                    pbar.update(1)
        else:
            for url, season, episode in urls:
                data = scraper.get_episode_data(url)
                if data:
                    if tmdb_client:
                        ep_name = tmdb_client.get_episode_name(
                            config.get("tmdb_series_id", ""),
                            season,
                            episode
                        )
                        data["TMDB Name"] = ep_name
                    results.append({
                        "Season": season,
                        "Episode": episode,
                        **data
                    })
                pbar.update(1)

    
    output_file = input(f"{CYAN}Output filename (without extension): {RESET}").strip() + ".json"
    results.sort(key=lambda x: (x["Season"], x["Episode"]))
    
    output_data = {
        "metadata": {
            "source": base_url,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "script_version": VERSION,
            "total_episodes": total_episodes,
            "seasons": seasons
        },
        "episodes": results
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{GREEN}Successfully saved {len(results)} episodes to {output_file}{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}Operation cancelled by user{RESET}")
        sys.exit(1)
