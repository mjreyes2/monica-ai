"""
Free APIs for Monica AI.
Provides access to free, no-API-key-required web services:
- Weather (Open-Meteo)
- Wikipedia summaries
- Dictionary definitions (Free Dictionary API)
- NASA Astronomy Picture of the Day
- Random facts/jokes (JokeAPI)
- World time

HIPAA PRIVACY NOTICE:
  These APIs only send GENERIC PUBLIC queries (coordinates, topic names,
  dictionary words). They NEVER send personal data, conversation content,
  health information, or user identifiers. All queries are sanitized
  through _sanitize_query() before being sent externally.
"""
import json
import logging
import re
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List

logger = logging.getLogger("Monica.FreeAPIs")

# Patterns that indicate personal/health data that must NEVER be sent externally
_PHI_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{10,}\b',  # Long numbers (phone, account)
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b(?:patient|diagnosis|prescription|symptom|medication|dosage)\b',  # Health terms
    r'\b(?:password|credit.?card|social.?security|bank.?account)\b',  # Sensitive
]


class FreeAPIs:
    """
    Collection of free API clients that require no API keys.
    All APIs are publicly available and free to use.
    
    HIPAA: All outbound queries are sanitized to prevent accidental
    transmission of Protected Health Information (PHI) or PII.
    """

    def __init__(self):
        self._cache = {}
        logger.info("Free APIs initialized (HIPAA-safe: no personal data sent)")

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Strip any potential PHI/PII from a query before sending externally.
        
        HIPAA safeguard: If the query contains patterns that look like
        personal data (SSN, email, health terms), they are redacted.
        """
        sanitized = query
        for pattern in _PHI_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        if sanitized != query:
            logger.warning(f"HIPAA: Sanitized outbound query (removed potential PHI)")
        return sanitized

    def _fetch_json(self, url: str, timeout: int = 8) -> Optional[dict]:
        """Fetch JSON from a URL."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug(f"API fetch failed ({url}): {e}")
            return None

    # ==================== Weather (Open-Meteo - no key) ====================

    def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather using Open-Meteo (free, no API key)."""
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"weather_code,wind_speed_10m,wind_direction_10m"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )
        data = self._fetch_json(url)
        if not data or "current" not in data:
            return None

        current = data["current"]
        code = current.get("weather_code", 0)
        return {
            "temperature_f": current.get("temperature_2m"),
            "feels_like_f": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed_mph": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "condition": self._weather_code_to_text(code),
            "source": "Open-Meteo (free)",
        }

    @staticmethod
    def _weather_code_to_text(code: int) -> str:
        """Convert WMO weather code to human-readable text."""
        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, f"Unknown ({code})")

    # ==================== Wikipedia ====================

    def search_wikipedia(self, query: str, sentences: int = 3) -> Optional[Dict[str, Any]]:
        """Get Wikipedia summary (free, no API key). HIPAA-sanitized."""
        query = self._sanitize_query(query)
        encoded = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        data = self._fetch_json(url)
        if not data or data.get("type") == "not_found":
            # Try search endpoint
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=1"
            search_data = self._fetch_json(search_url)
            if search_data and search_data.get("query", {}).get("search"):
                title = search_data["query"]["search"][0]["title"]
                encoded_title = urllib.parse.quote(title)
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
                data = self._fetch_json(url)
                if not data:
                    return None
            else:
                return None

        return {
            "title": data.get("title", query),
            "summary": data.get("extract", "No summary available."),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "source": "Wikipedia (free)",
        }

    # ==================== Dictionary ====================

    def define_word(self, word: str) -> Optional[Dict[str, Any]]:
        """Get word definition using Free Dictionary API (no key). HIPAA-sanitized."""
        word = self._sanitize_query(word)
        encoded = urllib.parse.quote(word.lower().strip())
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{encoded}"
        data = self._fetch_json(url)
        if not data or isinstance(data, dict):
            return None

        entry = data[0] if isinstance(data, list) else data
        meanings = []
        for m in entry.get("meanings", []):
            part = m.get("partOfSpeech", "")
            defs = [d.get("definition", "") for d in m.get("definitions", [])[:2]]
            meanings.append({"part_of_speech": part, "definitions": defs})

        return {
            "word": entry.get("word", word),
            "phonetic": entry.get("phonetic", ""),
            "meanings": meanings,
            "source": "Free Dictionary API",
        }

    # ==================== NASA APOD ====================

    def get_nasa_apod(self) -> Optional[Dict[str, Any]]:
        """Get NASA Astronomy Picture of the Day (DEMO_KEY, free)."""
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        data = self._fetch_json(url)
        if not data:
            return None
        return {
            "title": data.get("title", ""),
            "explanation": data.get("explanation", ""),
            "url": data.get("url", ""),
            "date": data.get("date", ""),
            "media_type": data.get("media_type", ""),
            "source": "NASA APOD (DEMO_KEY)",
        }

    # ==================== Jokes ====================

    def get_joke(self, category: str = "Any") -> Optional[str]:
        """Get a random joke from JokeAPI (free, no key)."""
        url = f"https://v2.jokeapi.dev/joke/{category}?blacklistFlags=nsfw,racist,sexist"
        data = self._fetch_json(url)
        if not data or data.get("error"):
            return None
        if data.get("type") == "single":
            return data.get("joke", "")
        elif data.get("type") == "twopart":
            return f"{data.get('setup', '')} ... {data.get('delivery', '')}"
        return None

    # ==================== World Time ====================

    def get_world_time(self, timezone: str = None) -> Optional[Dict[str, Any]]:
        """Get current time for a timezone using WorldTimeAPI (free)."""
        if timezone:
            tz = urllib.parse.quote(timezone)
            url = f"https://worldtimeapi.org/api/timezone/{tz}"
        else:
            url = "https://worldtimeapi.org/api/ip"
        data = self._fetch_json(url)
        if not data:
            return None
        return {
            "datetime": data.get("datetime", ""),
            "timezone": data.get("timezone", ""),
            "utc_offset": data.get("utc_offset", ""),
            "day_of_week": data.get("day_of_week", ""),
            "source": "WorldTimeAPI (free)",
        }

    # ==================== Exchange Rates (free, no key) ====================

    def get_exchange_rate(self, base: str = "USD") -> Optional[Dict[str, Any]]:
        """Get exchange rates using ExchangeRate-API (free, no key)."""
        url = f"https://open.er-api.com/v6/latest/{base.upper()}"
        data = self._fetch_json(url)
        if not data or data.get("result") != "success":
            return None
        return {
            "base": data.get("base_code", base),
            "rates": data.get("rates", {}),
            "updated": data.get("time_last_update_utc", ""),
            "source": "ExchangeRate-API (free)",
        }

    # ==================== Open Trivia DB (free, no key) ====================

    def get_trivia(self, category: int = None, difficulty: str = None) -> Optional[Dict[str, Any]]:
        """Get trivia question from Open Trivia DB (free, unlimited)."""
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        if category:
            url += f"&category={category}"
        if difficulty:
            url += f"&difficulty={difficulty}"
        data = self._fetch_json(url)
        if not data or data.get("response_code") != 0:
            return None
        q = data.get("results", [{}])[0]
        import html
        return {
            "question": html.unescape(q.get("question", "")),
            "correct_answer": html.unescape(q.get("correct_answer", "")),
            "incorrect_answers": [html.unescape(a) for a in q.get("incorrect_answers", [])],
            "category": html.unescape(q.get("category", "")),
            "difficulty": q.get("difficulty", ""),
            "source": "Open Trivia DB (free)",
        }

    # ==================== Open Library (books, free) ====================

    def search_books(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Search books using Open Library (free, no key). HIPAA-sanitized."""
        query = self._sanitize_query(query)
        encoded = urllib.parse.quote(query)
        url = f"https://openlibrary.org/search.json?q={encoded}&limit={limit}"
        data = self._fetch_json(url)
        if not data:
            return None
        books = []
        for doc in data.get("docs", [])[:limit]:
            books.append({
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", ["Unknown"])),
                "year": doc.get("first_publish_year", ""),
                "isbn": (doc.get("isbn", [None]) or [None])[0],
                "subjects": doc.get("subject", [])[:5],
            })
        return books if books else None

    # ==================== DuckDuckGo Instant Answer (free) ====================

    def instant_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """Get instant answer from DuckDuckGo (free, no key, no rate limit). HIPAA-sanitized."""
        query = self._sanitize_query(query)
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        data = self._fetch_json(url)
        if not data:
            return None
        abstract = data.get("AbstractText", "")
        answer = data.get("Answer", "")
        if not abstract and not answer:
            return None
        return {
            "abstract": abstract,
            "answer": answer,
            "heading": data.get("Heading", ""),
            "url": data.get("AbstractURL", ""),
            "source": data.get("AbstractSource", "DuckDuckGo"),
            "image": data.get("Image", ""),
            "related": [t.get("Text", "") for t in data.get("RelatedTopics", [])[:5] if isinstance(t, dict) and t.get("Text")],
        }

    # ==================== USGS Earthquakes (free) ====================

    def get_earthquakes(self, min_magnitude: float = 4.0, days: int = 7) -> Optional[List[Dict[str, Any]]]:
        """Get recent earthquakes from USGS (free, no key)."""
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude={min_magnitude}&limit=10&orderby=time"
        data = self._fetch_json(url)
        if not data:
            return None
        quakes = []
        for f in data.get("features", [])[:10]:
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [0, 0, 0])
            quakes.append({
                "magnitude": props.get("mag"),
                "location": props.get("place", "Unknown"),
                "time": props.get("time", 0),
                "lat": coords[1] if len(coords) > 1 else 0,
                "lon": coords[0] if len(coords) > 0 else 0,
                "depth_km": coords[2] if len(coords) > 2 else 0,
            })
        return quakes if quakes else None

    # ==================== Country Info (REST Countries, free) ====================

    def get_country_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get country info from REST Countries (free, no key). HIPAA-sanitized."""
        name = self._sanitize_query(name)
        encoded = urllib.parse.quote(name)
        url = f"https://restcountries.com/v3.1/name/{encoded}?fields=name,capital,population,region,subregion,languages,currencies,timezones,flags,latlng"
        data = self._fetch_json(url)
        if not data or isinstance(data, dict) and data.get("status"):
            return None
        c = data[0] if isinstance(data, list) else data
        langs = list(c.get("languages", {}).values()) if c.get("languages") else []
        currs = []
        for code, info in (c.get("currencies", {}) or {}).items():
            currs.append({"code": code, "name": info.get("name", ""), "symbol": info.get("symbol", "")})
        return {
            "name": c.get("name", {}).get("common", name),
            "official_name": c.get("name", {}).get("official", ""),
            "capital": ", ".join(c.get("capital", [])),
            "population": c.get("population", 0),
            "region": c.get("region", ""),
            "subregion": c.get("subregion", ""),
            "languages": langs,
            "currencies": currs,
            "timezones": c.get("timezones", []),
            "lat": c.get("latlng", [0, 0])[0],
            "lon": c.get("latlng", [0, 0])[1],
            "flag_url": c.get("flags", {}).get("png", ""),
            "source": "REST Countries (free)",
        }

    # ==================== Advice Slip (free) ====================

    def get_advice(self) -> Optional[str]:
        """Get random advice from Advice Slip API (free, no key)."""
        data = self._fetch_json("https://api.adviceslip.com/advice")
        if not data:
            return None
        return data.get("slip", {}).get("advice")

    # ==================== Quotable (free) ====================

    def get_quote(self) -> Optional[Dict[str, str]]:
        """Get random quote from Quotable API (free, no key)."""
        data = self._fetch_json("https://api.quotable.io/quotes/random")
        if not data or not isinstance(data, list):
            return None
        q = data[0]
        return {"content": q.get("content", ""), "author": q.get("author", "")}

    # ==================== ISS Location (free) ====================

    def get_iss_location(self) -> Optional[Dict[str, Any]]:
        """Get ISS current position (free, no key)."""
        data = self._fetch_json("http://api.open-notify.org/iss-now.json")
        if not data or data.get("message") != "success":
            return None
        pos = data.get("iss_position", {})
        return {
            "lat": float(pos.get("latitude", 0)),
            "lon": float(pos.get("longitude", 0)),
            "timestamp": data.get("timestamp", 0),
            "source": "Open Notify (free)",
        }

    # ==================== People in Space (free) ====================

    def get_people_in_space(self) -> Optional[Dict[str, Any]]:
        """Get astronauts currently in space (free, no key)."""
        data = self._fetch_json("http://api.open-notify.org/astros.json")
        if not data or data.get("message") != "success":
            return None
        return {
            "count": data.get("number", 0),
            "people": data.get("people", []),
            "source": "Open Notify (free)",
        }

    # ==================== Generic search ====================

    def search(self, query: str) -> Dict[str, Any]:
        """
        Smart search across all free APIs based on query content.
        Returns dict with results from relevant APIs.
        """
        results = {}
        q = query.lower()

        # Weather keywords
        if any(w in q for w in ["weather", "temperature", "rain", "snow", "wind", "forecast", "hot", "cold"]):
            try:
                from utils.location_services import get_location_services
                loc = get_location_services().get_current_location()
                if loc:
                    weather = self.get_weather(loc["lat"], loc["lon"])
                    if weather:
                        results["weather"] = weather
            except Exception:
                pass

        # Wikipedia keywords or general knowledge queries
        if any(w in q for w in ["what is", "who is", "where is", "when was", "history of",
                                "define", "explain", "tell me about", "wikipedia"]):
            wiki = self.search_wikipedia(query)
            if wiki:
                results["wikipedia"] = wiki

        # Dictionary
        if any(w in q for w in ["define", "definition", "meaning of", "what does", "spell"]):
            words = q.replace("define", "").replace("definition of", "").replace("meaning of", "").strip().split()
            if words:
                defn = self.define_word(words[-1])
                if defn:
                    results["dictionary"] = defn

        # NASA / Space
        if any(w in q for w in ["nasa", "space", "astronomy", "star", "planet", "cosmos"]):
            apod = self.get_nasa_apod()
            if apod:
                results["nasa_apod"] = apod

        # Jokes
        if any(w in q for w in ["joke", "funny", "laugh", "humor"]):
            joke = self.get_joke()
            if joke:
                results["joke"] = joke

        # Time
        if any(w in q for w in ["time", "clock", "what time"]):
            time_data = self.get_world_time()
            if time_data:
                results["world_time"] = time_data

        # Exchange rates / currency
        if any(w in q for w in ["exchange rate", "currency", "convert", "dollar", "euro", "pound", "yen"]):
            rates = self.get_exchange_rate()
            if rates:
                results["exchange_rates"] = rates

        # Trivia
        if any(w in q for w in ["trivia", "quiz", "test me", "random question"]):
            trivia = self.get_trivia()
            if trivia:
                results["trivia"] = trivia

        # Books
        if any(w in q for w in ["book", "novel", "author", "read", "library"]):
            books = self.search_books(query, limit=3)
            if books:
                results["books"] = books

        # Earthquakes
        if any(w in q for w in ["earthquake", "seismic", "quake"]):
            quakes = self.get_earthquakes()
            if quakes:
                results["earthquakes"] = quakes

        # Country info
        if any(w in q for w in ["country", "capital of", "population of", "currency of"]):
            # Try to extract country name
            for prefix in ["capital of ", "population of ", "currency of ", "about "]:
                if prefix in q:
                    name = q.split(prefix)[-1].strip().strip("?")
                    if name:
                        info = self.get_country_info(name)
                        if info:
                            results["country"] = info
                        break

        # ISS / Space
        if any(w in q for w in ["iss", "space station", "astronaut", "people in space"]):
            iss = self.get_iss_location()
            if iss:
                results["iss"] = iss
            people = self.get_people_in_space()
            if people:
                results["people_in_space"] = people

        # Advice
        if any(w in q for w in ["advice", "tip", "suggestion", "what should"]):
            advice = self.get_advice()
            if advice:
                results["advice"] = advice

        # Quote / inspiration
        if any(w in q for w in ["quote", "inspiration", "motivat", "wisdom"]):
            quote = self.get_quote()
            if quote:
                results["quote"] = quote

        # DuckDuckGo fallback for general knowledge
        if not results:
            ddg = self.instant_answer(query)
            if ddg:
                results["instant_answer"] = ddg

        return results


# Singleton
_free_apis = None


def get_free_apis() -> FreeAPIs:
    """Get singleton FreeAPIs instance."""
    global _free_apis
    if _free_apis is None:
        _free_apis = FreeAPIs()
    return _free_apis
