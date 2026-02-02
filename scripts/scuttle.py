import requests
from bs4 import BeautifulSoup
import re
import json

class ScuttleError(Exception):
    pass

class Scuttler:
    """Abstract base class for source-specific scuttlers."""
    def can_handle(self, url):
        return False

    def scuttle(self, url):
        """Returns a dict with: source, type, title, content, confidence, tags"""
        raise NotImplementedError

class RedditScuttler(Scuttler):
    def can_handle(self, url):
        return "reddit.com" in url or "redd.it" in url

    def scuttle(self, url):
        # Clean URL and append .json
        if "?" in url:
            url = url.split("?")[0]
        if not url.endswith(".json"):
            json_url = url.strip("/") + ".json"
        else:
            json_url = url

        headers = {"User-Agent": "ResearchVault/1.0.1"}
        try:
            resp = requests.get(json_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            # Reddit JSON structure: [listing_post, listing_comments]
            post_data = data[0]['data']['children'][0]['data']
            
            title = post_data.get('title', 'No Title')
            body = post_data.get('selftext', '')
            score = post_data.get('score', 0)
            subreddit = post_data.get('subreddit', 'unknown')
            
            content = f"Subreddit: r/{subreddit}\nScore: {score}\nBody: {body}\n"
            
            # Try to get top comment if available
            try:
                comments = data[1]['data']['children']
                if comments:
                    top_comment = comments[0]['data'].get('body', '')
                    if top_comment:
                        content += f"\n--- Top Comment ---\n{top_comment}"
            except (IndexError, KeyError):
                pass

            return {
                "source": f"reddit/r/{subreddit}",
                "type": "SCUTTLE_REDDIT",
                "title": title,
                "content": content,
                "confidence": 1.0 if score > 10 else 0.8,
                "tags": f"reddit,{subreddit}"
            }
        except Exception as e:
            raise ScuttleError(f"Reddit scuttle failed: {e}")

class MoltbookScuttler(Scuttler):
    def can_handle(self, url):
        return "moltbook" in url

    def scuttle(self, url):
        # Mock implementation for the fictional platform
        # URL format: moltbook://post/<id>
        return {
            "source": "moltbook",
            "type": "SCUTTLE_MOLTBOOK",
            "title": "State Management in Autonomous Agents",
            "content": "Modular state management is the missing piece. Persistent SQLite vault + multi-source scuttling = agents that can actually remember and learn across sessions.",
            "confidence": 0.99,
            "tags": "moltbook,agents,state"
        }

class WebScuttler(Scuttler):
    def can_handle(self, url):
        return True # Fallback

    def scuttle(self, url):
        headers = {"User-Agent": "ResearchVault/1.0.1"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            title = soup.title.string if soup.title else url
            
            # Very basic extraction: get all paragraphs
            # In a real tool this would be more sophisticated (readability.js style)
            paragraphs = soup.find_all('p')
            text_content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])
            
            if not text_content:
                text_content = soup.get_text()[:2000] # Fallback to raw text, truncated

            return {
                "source": "web",
                "type": "SCUTTLE_WEB",
                "title": title.strip(),
                "content": text_content[:5000], # Limit payload
                "confidence": 0.7,
                "tags": "web,scraping"
            }
        except Exception as e:
            raise ScuttleError(f"Web scuttle failed: {e}")

def get_scuttler(url):
    scuttlers = [RedditScuttler(), MoltbookScuttler(), WebScuttler()]
    for s in scuttlers:
        if s.can_handle(url):
            return s
    return WebScuttler() # Should not be reached due to fallback, but safe
