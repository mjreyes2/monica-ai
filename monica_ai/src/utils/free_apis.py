"""
Monica Free APIs Module
All APIs are 100% FREE with NO authentication required!

Phase 1: Essential (Weather, Dictionary, Wikipedia, Currency, Jokes)
Phase 2: Enhancement (NASA, ISS, Earthquakes, Quotes)
Phase 3: Fun (Dad Jokes, Advice, Affirmations)

Created for Monica AI by MJP
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import lru_cache
import time

class MonicaFreeAPIs:
    """
    Collection of free APIs for Monica AI.
    All APIs require NO authentication!
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Monica-AI/1.0 (Personal Assistant)'
        })
        self.timeout = 10
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
        
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Cache result with timestamp."""
        self._cache[key] = (data, time.time())
    
    # ==================== PHASE 1: ESSENTIAL ====================
    
    def get_weather(self, location: str = None, lat: float = None, lon: float = None) -> Dict:
        """
        Get weather forecast using Open-Meteo (FREE, no key needed).
        
        Args:
            location: City name (will be geocoded)
            lat, lon: Direct coordinates
            
        Returns:
            Weather data including current conditions and forecast
        """
        try:
            # If location name provided, geocode it first
            if location and not (lat and lon):
                geo = self.geocode(location)
                if geo:
                    lat, lon = geo['lat'], geo['lon']
                else:
                    return {"error": f"Could not find location: {location}"}
            
            if not (lat and lon):
                # Default to New York
                lat, lon = 40.7128, -74.0060
            
            # Open-Meteo API - completely free!
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto",
                "forecast_days": 7
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if "current" in data:
                weather_codes = {
                    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Depositing rime fog",
                    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
                }
                
                current = data["current"]
                code = current.get("weather_code", 0)
                
                return {
                    "success": True,
                    "location": location or f"{lat}, {lon}",
                    "current": {
                        "temperature": round(current.get("temperature_2m", 0)),
                        "feels_like": round(current.get("apparent_temperature", 0)),
                        "humidity": current.get("relative_humidity_2m", 0),
                        "wind_speed": round(current.get("wind_speed_10m", 0)),
                        "condition": weather_codes.get(code, "Unknown"),
                        "weather_code": code
                    },
                    "forecast": data.get("daily", {}),
                    "timezone": data.get("timezone", "UTC")
                }
            
            return {"error": "No weather data available"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_simple_weather(self, location: str) -> str:
        """Get simple one-line weather using wttr.in."""
        try:
            url = f"https://wttr.in/{location}?format=3"
            response = self.session.get(url, timeout=self.timeout)
            return response.text.strip()
        except:
            return f"Could not get weather for {location}"
    
    def define_word(self, word: str) -> Dict:
        """
        Get word definition using Free Dictionary API.
        
        Args:
            word: Word to define
            
        Returns:
            Definition, pronunciation, examples, synonyms
        """
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"Word '{word}' not found"}
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                
                # Extract phonetic
                phonetic = entry.get("phonetic", "")
                if not phonetic and entry.get("phonetics"):
                    for p in entry["phonetics"]:
                        if p.get("text"):
                            phonetic = p["text"]
                            break
                
                # Extract meanings
                meanings = []
                for meaning in entry.get("meanings", [])[:3]:  # Limit to 3
                    part_of_speech = meaning.get("partOfSpeech", "")
                    definitions = []
                    for defn in meaning.get("definitions", [])[:2]:  # Limit to 2 per type
                        definitions.append({
                            "definition": defn.get("definition", ""),
                            "example": defn.get("example", ""),
                            "synonyms": defn.get("synonyms", [])[:5]
                        })
                    meanings.append({
                        "part_of_speech": part_of_speech,
                        "definitions": definitions
                    })
                
                return {
                    "success": True,
                    "word": entry.get("word", word),
                    "phonetic": phonetic,
                    "meanings": meanings
                }
            
            return {"error": "No definition found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_wikipedia(self, query: str, sentences: int = 3) -> Dict:
        """
        Search Wikipedia for information.
        
        Args:
            query: Search term
            sentences: Number of sentences to return (1-10)
            
        Returns:
            Summary and link to full article
        """
        try:
            # First, search for the page
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1
            }
            
            response = self.session.get(search_url, params=search_params, timeout=self.timeout)
            search_data = response.json()
            
            if not search_data.get("query", {}).get("search"):
                return {"error": f"No Wikipedia article found for '{query}'"}
            
            title = search_data["query"]["search"][0]["title"]
            
            # Get the summary
            summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")
            response = self.session.get(summary_url, timeout=self.timeout)
            data = response.json()
            
            if data.get("extract"):
                # Limit sentences
                extract = data["extract"]
                sentence_list = extract.split(". ")
                if len(sentence_list) > sentences:
                    extract = ". ".join(sentence_list[:sentences]) + "."
                
                return {
                    "success": True,
                    "title": data.get("title", title),
                    "summary": extract,
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", "")
                }
            
            return {"error": "No summary available"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """
        Convert currency using ExchangeRate-API (free tier).
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., USD)
            to_currency: Target currency code (e.g., EUR)
            
        Returns:
            Converted amount and exchange rate
        """
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            # Check cache
            cache_key = f"exchange_{from_currency}"
            cached = self._get_cached(cache_key)
            
            if cached:
                rates = cached
            else:
                url = f"https://open.er-api.com/v6/latest/{from_currency}"
                response = self.session.get(url, timeout=self.timeout)
                data = response.json()
                
                if data.get("result") != "success":
                    return {"error": f"Could not get exchange rates for {from_currency}"}
                
                rates = data.get("rates", {})
                self._set_cache(cache_key, rates)
            
            if to_currency not in rates:
                return {"error": f"Unknown currency: {to_currency}"}
            
            rate = rates[to_currency]
            converted = round(amount * rate, 2)
            
            return {
                "success": True,
                "from": from_currency,
                "to": to_currency,
                "amount": amount,
                "converted": converted,
                "rate": round(rate, 4)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_joke(self, category: str = "Any", safe: bool = True) -> Dict:
        """
        Get a joke using JokeAPI.
        
        Args:
            category: Any, Programming, Misc, Pun, Spooky, Christmas
            safe: If True, only safe jokes
            
        Returns:
            Joke text
        """
        try:
            url = f"https://v2.jokeapi.dev/joke/{category}"
            params = {"safe-mode": ""} if safe else {}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data.get("error"):
                return {"error": data.get("message", "Could not get joke")}
            
            if data.get("type") == "single":
                return {
                    "success": True,
                    "type": "single",
                    "joke": data.get("joke", ""),
                    "category": data.get("category", "")
                }
            else:
                return {
                    "success": True,
                    "type": "twopart",
                    "setup": data.get("setup", ""),
                    "delivery": data.get("delivery", ""),
                    "category": data.get("category", "")
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== PHASE 2: ENHANCEMENT ====================
    
    def get_nasa_apod(self) -> Dict:
        """
        Get NASA Astronomy Picture of the Day.
        Uses DEMO_KEY which has limited requests but works!
        """
        try:
            url = "https://api.nasa.gov/planetary/apod"
            params = {"api_key": "DEMO_KEY"}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "title": data.get("title", ""),
                "explanation": data.get("explanation", ""),
                "url": data.get("url", ""),
                "date": data.get("date", ""),
                "media_type": data.get("media_type", "image")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_iss_location(self) -> Dict:
        """
        Get current ISS (International Space Station) location.
        """
        try:
            url = "http://api.open-notify.org/iss-now.json"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            if data.get("message") == "success":
                pos = data.get("iss_position", {})
                lat = float(pos.get("latitude", 0))
                lon = float(pos.get("longitude", 0))
                
                # Get location name via reverse geocoding
                location_name = self._reverse_geocode(lat, lon)
                
                return {
                    "success": True,
                    "latitude": lat,
                    "longitude": lon,
                    "location": location_name,
                    "timestamp": data.get("timestamp", 0)
                }
            
            return {"error": "Could not get ISS location"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_astronauts_in_space(self) -> Dict:
        """
        Get list of people currently in space.
        """
        try:
            url = "http://api.open-notify.org/astros.json"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            if data.get("message") == "success":
                people = data.get("people", [])
                
                # Group by craft
                by_craft = {}
                for person in people:
                    craft = person.get("craft", "Unknown")
                    if craft not in by_craft:
                        by_craft[craft] = []
                    by_craft[craft].append(person.get("name", "Unknown"))
                
                return {
                    "success": True,
                    "count": data.get("number", len(people)),
                    "people": people,
                    "by_craft": by_craft
                }
            
            return {"error": "Could not get astronaut data"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_earthquakes(self, min_magnitude: float = 4.5, days: int = 1) -> Dict:
        """
        Get recent earthquakes from USGS.
        
        Args:
            min_magnitude: Minimum magnitude (default 4.5)
            days: Number of days to look back (default 1)
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson",
                "starttime": start_date.strftime("%Y-%m-%d"),
                "endtime": end_date.strftime("%Y-%m-%d"),
                "minmagnitude": min_magnitude,
                "orderby": "magnitude"
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            earthquakes = []
            for feature in data.get("features", [])[:10]:  # Limit to 10
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [0, 0, 0])
                
                earthquakes.append({
                    "magnitude": props.get("mag", 0),
                    "location": props.get("place", "Unknown"),
                    "time": datetime.fromtimestamp(props.get("time", 0) / 1000).strftime("%Y-%m-%d %H:%M UTC"),
                    "depth_km": round(coords[2], 1) if len(coords) > 2 else 0,
                    "url": props.get("url", "")
                })
            
            return {
                "success": True,
                "count": len(earthquakes),
                "earthquakes": earthquakes,
                "period": f"Last {days} day(s), magnitude {min_magnitude}+"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_spacex_latest_launch(self) -> Dict:
        """
        Get latest SpaceX launch information.
        """
        try:
            url = "https://api.spacexdata.com/v5/launches/latest"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "name": data.get("name", "Unknown"),
                "date": data.get("date_utc", "")[:10] if data.get("date_utc") else "",
                "success": data.get("success"),
                "details": data.get("details", "No details available"),
                "rocket": data.get("rocket", ""),
                "webcast": data.get("links", {}).get("webcast", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_quote(self) -> Dict:
        """
        Get a random inspirational quote.
        """
        try:
            url = "https://api.quotable.io/quotes/random"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                quote = data[0]
                return {
                    "success": True,
                    "content": quote.get("content", ""),
                    "author": quote.get("author", "Unknown"),
                    "tags": quote.get("tags", [])
                }
            
            return {"error": "Could not get quote"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_space_news(self, limit: int = 5) -> Dict:
        """
        Get latest space news.
        """
        try:
            url = "https://api.spaceflightnewsapi.net/v4/articles/"
            params = {"limit": limit}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            articles = []
            for article in data.get("results", []):
                articles.append({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", "")[:200] + "..." if len(article.get("summary", "")) > 200 else article.get("summary", ""),
                    "url": article.get("url", ""),
                    "published": article.get("published_at", "")[:10] if article.get("published_at") else ""
                })
            
            return {
                "success": True,
                "count": len(articles),
                "articles": articles
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== PHASE 3: FUN ====================
    
    def get_dad_joke(self) -> Dict:
        """
        Get a random dad joke.
        """
        try:
            url = "https://icanhazdadjoke.com/"
            headers = {"Accept": "application/json"}
            
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "joke": data.get("joke", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_advice(self) -> Dict:
        """
        Get random life advice.
        """
        try:
            url = "https://api.adviceslip.com/advice"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            slip = data.get("slip", {})
            return {
                "success": True,
                "advice": slip.get("advice", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_affirmation(self) -> Dict:
        """
        Get a positive affirmation.
        """
        try:
            url = "https://www.affirmations.dev/"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "affirmation": data.get("affirmation", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_chuck_norris_joke(self) -> Dict:
        """
        Get a Chuck Norris joke.
        """
        try:
            url = "https://api.chucknorris.io/jokes/random"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "joke": data.get("value", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_trivia(self, category: int = None, difficulty: str = "medium") -> Dict:
        """
        Get a trivia question.
        
        Args:
            category: Category ID (9=General, 17=Science, 21=Sports, 23=History)
            difficulty: easy, medium, hard
        """
        try:
            url = "https://opentdb.com/api.php"
            params = {
                "amount": 1,
                "difficulty": difficulty,
                "type": "multiple"
            }
            if category:
                params["category"] = category
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data.get("results"):
                q = data["results"][0]
                # Decode HTML entities
                import html
                return {
                    "success": True,
                    "question": html.unescape(q.get("question", "")),
                    "correct_answer": html.unescape(q.get("correct_answer", "")),
                    "incorrect_answers": [html.unescape(a) for a in q.get("incorrect_answers", [])],
                    "category": q.get("category", ""),
                    "difficulty": q.get("difficulty", "")
                }
            
            return {"error": "No trivia available"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_number_fact(self, number: int = None) -> Dict:
        """
        Get a fun fact about a number.
        
        Args:
            number: Specific number, or None for random
        """
        try:
            if number is None:
                url = "http://numbersapi.com/random/trivia?json"
            else:
                url = f"http://numbersapi.com/{number}/trivia?json"
            
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "number": data.get("number", number),
                "fact": data.get("text", ""),
                "type": data.get("type", "trivia")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_cat_fact(self) -> Dict:
        """
        Get a random cat fact.
        """
        try:
            url = "https://cat-fact.herokuapp.com/facts/random"
            response = self.session.get(url, timeout=self.timeout)
            data = response.json()
            
            return {
                "success": True,
                "fact": data.get("text", "")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== REST COUNTRIES API ====================
    
    def get_country_info(self, country_name: str) -> Dict:
        """
        Get detailed information about a country using Rest Countries API.
        
        Args:
            country_name: Name of the country (e.g., "Japan", "Brazil", "Germany")
            
        Returns:
            Country info including capital, population, languages, currency, etc.
        """
        try:
            # Search by name
            url = f"https://restcountries.com/v3.1/name/{country_name}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"Country '{country_name}' not found"}
            
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                country = data[0]
                
                # Extract languages
                languages = list(country.get("languages", {}).values()) if country.get("languages") else []
                
                # Extract currencies
                currencies = []
                if country.get("currencies"):
                    for code, info in country["currencies"].items():
                        currencies.append({
                            "code": code,
                            "name": info.get("name", ""),
                            "symbol": info.get("symbol", "")
                        })
                
                # Extract capital
                capitals = country.get("capital", [])
                capital = capitals[0] if capitals else "N/A"
                
                # Get coordinates for globe
                latlng = country.get("latlng", [0, 0])
                
                return {
                    "success": True,
                    "name": country.get("name", {}).get("common", country_name),
                    "official_name": country.get("name", {}).get("official", ""),
                    "capital": capital,
                    "population": country.get("population", 0),
                    "area_km2": country.get("area", 0),
                    "region": country.get("region", ""),
                    "subregion": country.get("subregion", ""),
                    "languages": languages,
                    "currencies": currencies,
                    "timezones": country.get("timezones", []),
                    "borders": country.get("borders", []),
                    "flag_emoji": country.get("flag", ""),
                    "flag_png": country.get("flags", {}).get("png", ""),
                    "flag_svg": country.get("flags", {}).get("svg", ""),
                    "coat_of_arms": country.get("coatOfArms", {}).get("png", ""),
                    "lat": latlng[0] if len(latlng) > 0 else 0,
                    "lon": latlng[1] if len(latlng) > 1 else 0,
                    "google_maps": country.get("maps", {}).get("googleMaps", ""),
                    "openstreet_maps": country.get("maps", {}).get("openStreetMaps", ""),
                    "driving_side": country.get("car", {}).get("side", ""),
                    "calling_code": country.get("idd", {}).get("root", "") + (country.get("idd", {}).get("suffixes", [""])[0] if country.get("idd", {}).get("suffixes") else ""),
                    "tld": country.get("tld", []),
                    "independent": country.get("independent", True),
                    "un_member": country.get("unMember", False)
                }
            
            return {"error": "No country data found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_country_by_code(self, code: str) -> Dict:
        """
        Get country info by ISO 3166-1 alpha-2 or alpha-3 code.
        
        Args:
            code: Country code (e.g., "US", "USA", "JP", "JPN")
        """
        try:
            url = f"https://restcountries.com/v3.1/alpha/{code}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"Country code '{code}' not found"}
            
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                country = data[0]
                return self.get_country_info(country.get("name", {}).get("common", code))
            
            return {"error": "No country data found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_countries_by_region(self, region: str) -> Dict:
        """
        Get all countries in a region.
        
        Args:
            region: Region name (Africa, Americas, Asia, Europe, Oceania)
        """
        try:
            url = f"https://restcountries.com/v3.1/region/{region}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"Region '{region}' not found"}
            
            data = response.json()
            
            countries = []
            for country in data:
                latlng = country.get("latlng", [0, 0])
                countries.append({
                    "name": country.get("name", {}).get("common", ""),
                    "capital": country.get("capital", ["N/A"])[0] if country.get("capital") else "N/A",
                    "population": country.get("population", 0),
                    "flag_emoji": country.get("flag", ""),
                    "lat": latlng[0] if len(latlng) > 0 else 0,
                    "lon": latlng[1] if len(latlng) > 1 else 0
                })
            
            # Sort by population
            countries.sort(key=lambda x: x["population"], reverse=True)
            
            return {
                "success": True,
                "region": region,
                "count": len(countries),
                "countries": countries
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_countries_by_language(self, language: str) -> Dict:
        """
        Get all countries that speak a language.
        
        Args:
            language: Language name (e.g., "spanish", "french", "arabic")
        """
        try:
            url = f"https://restcountries.com/v3.1/lang/{language}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"No countries found for language '{language}'"}
            
            data = response.json()
            
            countries = []
            for country in data:
                countries.append({
                    "name": country.get("name", {}).get("common", ""),
                    "population": country.get("population", 0),
                    "flag_emoji": country.get("flag", "")
                })
            
            # Sort by population
            countries.sort(key=lambda x: x["population"], reverse=True)
            
            return {
                "success": True,
                "language": language,
                "count": len(countries),
                "countries": countries
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_countries_by_currency(self, currency: str) -> Dict:
        """
        Get all countries that use a currency.
        
        Args:
            currency: Currency code (e.g., "USD", "EUR", "JPY")
        """
        try:
            url = f"https://restcountries.com/v3.1/currency/{currency}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                return {"error": f"No countries found for currency '{currency}'"}
            
            data = response.json()
            
            countries = []
            for country in data:
                countries.append({
                    "name": country.get("name", {}).get("common", ""),
                    "population": country.get("population", 0),
                    "flag_emoji": country.get("flag", "")
                })
            
            return {
                "success": True,
                "currency": currency.upper(),
                "count": len(countries),
                "countries": countries
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_countries(self) -> Dict:
        """
        Get a list of all countries with basic info.
        Useful for globe visualization.
        """
        try:
            # Check cache first (this is a large request)
            cache_key = "all_countries"
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            url = "https://restcountries.com/v3.1/all?fields=name,capital,population,latlng,flag,region"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            countries = []
            for country in data:
                latlng = country.get("latlng", [0, 0])
                countries.append({
                    "name": country.get("name", {}).get("common", ""),
                    "capital": country.get("capital", ["N/A"])[0] if country.get("capital") else "N/A",
                    "population": country.get("population", 0),
                    "region": country.get("region", ""),
                    "flag_emoji": country.get("flag", ""),
                    "lat": latlng[0] if len(latlng) > 0 else 0,
                    "lon": latlng[1] if len(latlng) > 1 else 0
                })
            
            result = {
                "success": True,
                "count": len(countries),
                "countries": countries
            }
            
            # Cache for 1 hour
            self._cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_country(self, query: str) -> Dict:
        """
        Smart search for country - tries name, code, capital.
        """
        # Try by name first
        result = self.get_country_info(query)
        if result.get("success"):
            return result
        
        # Try by code
        if len(query) <= 3:
            result = self.get_country_by_code(query)
            if result.get("success"):
                return result
        
        return {"error": f"Could not find country matching '{query}'"}
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def geocode(self, location: str) -> Optional[Dict]:
        """
        Convert location name to coordinates using Nominatim.
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", location)
                }
            return None
            
        except:
            return None
    
    def _reverse_geocode(self, lat: float, lon: float) -> str:
        """
        Convert coordinates to location name.
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json"
            }
            
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            address = data.get("address", {})
            
            # Try to get a meaningful location
            if address.get("country"):
                if address.get("city"):
                    return f"{address['city']}, {address['country']}"
                elif address.get("state"):
                    return f"{address['state']}, {address['country']}"
                else:
                    return address['country']
            
            # Over ocean
            return f"Over ocean ({lat:.1f}°, {lon:.1f}°)"
            
        except:
            return f"{lat:.2f}°, {lon:.2f}°"
    
    def get_sunrise_sunset(self, lat: float, lon: float) -> Dict:
        """
        Get sunrise and sunset times for a location.
        """
        try:
            url = "https://api.sunrisesunset.io/json"
            params = {
                "lat": lat,
                "lng": lon,
                "timezone": "auto",
                "date": "today"
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            if data.get("status") == "OK":
                results = data.get("results", {})
                return {
                    "success": True,
                    "sunrise": results.get("sunrise", ""),
                    "sunset": results.get("sunset", ""),
                    "day_length": results.get("day_length", ""),
                    "solar_noon": results.get("solar_noon", "")
                }
            
            return {"error": "Could not get sun times"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_books(self, query: str) -> Dict:
        """
        Search for books using Open Library.
        """
        try:
            url = "https://openlibrary.org/search.json"
            params = {"q": query, "limit": 5}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            books = []
            for doc in data.get("docs", [])[:5]:
                books.append({
                    "title": doc.get("title", "Unknown"),
                    "author": doc.get("author_name", ["Unknown"])[0] if doc.get("author_name") else "Unknown",
                    "year": doc.get("first_publish_year", "Unknown"),
                    "subjects": doc.get("subject", [])[:3]
                })
            
            return {
                "success": True,
                "count": len(books),
                "books": books
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def find_rhymes(self, word: str) -> Dict:
        """
        Find words that rhyme using Datamuse.
        """
        try:
            url = "https://api.datamuse.com/words"
            params = {"rel_rhy": word, "max": 10}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            rhymes = [item["word"] for item in data]
            
            return {
                "success": True,
                "word": word,
                "rhymes": rhymes
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def find_synonyms(self, word: str) -> Dict:
        """
        Find synonyms using Datamuse.
        """
        try:
            url = "https://api.datamuse.com/words"
            params = {"rel_syn": word, "max": 10}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            data = response.json()
            
            synonyms = [item["word"] for item in data]
            
            return {
                "success": True,
                "word": word,
                "synonyms": synonyms
            }
            
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_apis_instance = None

def get_free_apis() -> MonicaFreeAPIs:
    """Get singleton instance of MonicaFreeAPIs."""
    global _apis_instance
    if _apis_instance is None:
        _apis_instance = MonicaFreeAPIs()
    return _apis_instance


# ==================== VOICE COMMAND HELPERS ====================

def format_weather_response(data: Dict) -> str:
    """Format weather data for speech."""
    if data.get("error"):
        return f"Sorry, I couldn't get the weather. {data['error']}"
    
    current = data.get("current", {})
    location = data.get("location", "your location")
    
    return (
        f"In {location}, it's currently {current.get('temperature')} degrees "
        f"and {current.get('condition').lower()}. "
        f"It feels like {current.get('feels_like')} degrees "
        f"with {current.get('humidity')}% humidity."
    )

def format_definition_response(data: Dict) -> str:
    """Format dictionary definition for speech."""
    if data.get("error"):
        return f"Sorry, {data['error']}"
    
    word = data.get("word", "")
    meanings = data.get("meanings", [])
    
    if not meanings:
        return f"I couldn't find a definition for {word}."
    
    first_meaning = meanings[0]
    part = first_meaning.get("part_of_speech", "")
    defn = first_meaning.get("definitions", [{}])[0].get("definition", "")
    
    return f"{word} is a {part}. It means: {defn}"

def format_joke_response(data: Dict) -> str:
    """Format joke for speech."""
    if data.get("error"):
        return "Sorry, I couldn't think of a joke right now."
    
    if data.get("type") == "single":
        return data.get("joke", "")
    else:
        return f"{data.get('setup', '')} ... {data.get('delivery', '')}"

def format_iss_response(data: Dict) -> str:
    """Format ISS location for speech."""
    if data.get("error"):
        return "Sorry, I couldn't locate the ISS right now."
    
    return (
        f"The International Space Station is currently over {data.get('location', 'unknown location')}, "
        f"at coordinates {data.get('latitude', 0):.1f} latitude, {data.get('longitude', 0):.1f} longitude."
    )

def format_astronauts_response(data: Dict) -> str:
    """Format astronauts in space for speech."""
    if data.get("error"):
        return "Sorry, I couldn't get astronaut information."
    
    count = data.get("count", 0)
    by_craft = data.get("by_craft", {})
    
    response = f"There are currently {count} people in space. "
    for craft, names in by_craft.items():
        response += f"On the {craft}: {', '.join(names)}. "
    
    return response

def format_earthquake_response(data: Dict) -> str:
    """Format earthquake data for speech."""
    if data.get("error"):
        return "Sorry, I couldn't get earthquake data."
    
    quakes = data.get("earthquakes", [])
    if not quakes:
        return f"No significant earthquakes in the {data.get('period', 'recent period')}."
    
    response = f"There were {len(quakes)} significant earthquakes recently. "
    if quakes:
        biggest = quakes[0]
        response += f"The largest was magnitude {biggest.get('magnitude')} near {biggest.get('location')}."
    
    return response


# Test function
if __name__ == "__main__":
    apis = get_free_apis()
    
    print("Testing Monica Free APIs...")
    print("\n=== Weather ===")
    weather = apis.get_weather(location="New York")
    print(format_weather_response(weather))
    
    print("\n=== Dictionary ===")
    definition = apis.define_word("serendipity")
    print(format_definition_response(definition))
    
    print("\n=== Wikipedia ===")
    wiki = apis.search_wikipedia("Albert Einstein", sentences=2)
    if wiki.get("success"):
        print(f"{wiki['title']}: {wiki['summary']}")
    
    print("\n=== Currency ===")
    currency = apis.convert_currency(100, "USD", "EUR")
    if currency.get("success"):
        print(f"${currency['amount']} = €{currency['converted']} (rate: {currency['rate']})")
    
    print("\n=== Joke ===")
    joke = apis.get_joke()
    print(format_joke_response(joke))
    
    print("\n=== ISS Location ===")
    iss = apis.get_iss_location()
    print(format_iss_response(iss))
    
    print("\n=== Astronauts ===")
    astros = apis.get_astronauts_in_space()
    print(format_astronauts_response(astros))
    
    print("\n=== Dad Joke ===")
    dad = apis.get_dad_joke()
    if dad.get("success"):
        print(dad["joke"])
    
    print("\n=== Quote ===")
    quote = apis.get_quote()
    if quote.get("success"):
        print(f'"{quote["content"]}" - {quote["author"]}')
    
    print("\n[OK] All APIs working!")
