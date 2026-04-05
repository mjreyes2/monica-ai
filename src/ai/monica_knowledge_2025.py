"""
Monica's 2025 Knowledge Base
Current events, technology, culture, and world knowledge as of 2025
"""

from typing import Dict, List, Any

# 2025 CURRENT EVENTS AND KNOWLEDGE
KNOWLEDGE_2025 = {
    # Technology & AI
    "technology": {
        "ai_developments": {
            "large_language_models": {
                "gpt4_turbo": "OpenAI's GPT-4 Turbo with 128K context window",
                "claude_3": "Anthropic's Claude 3 family (Haiku, Sonnet, Opus)",
                "gemini": "Google's Gemini models (Pro, Ultra)",
                "llama3": "Meta's open-source Llama 3 models",
                "mistral": "Mistral AI's efficient open models",
                "local_ai": "Rise of local AI with Ollama, LM Studio, and on-device models"
            },
            "ai_assistants": {
                "chatgpt": "OpenAI's ChatGPT with voice, vision, and plugins",
                "copilot": "Microsoft Copilot integrated across Windows and Office",
                "gemini_assistant": "Google's Gemini replacing Google Assistant",
                "siri_ai": "Apple's enhanced Siri with AI capabilities",
                "alexa_llm": "Amazon Alexa with LLM integration"
            },
            "ai_image_generation": {
                "midjourney_v6": "Midjourney V6 with photorealistic capabilities",
                "dalle3": "DALL-E 3 integrated with ChatGPT",
                "stable_diffusion_3": "Stability AI's SD3 with improved text rendering",
                "firefly": "Adobe Firefly for commercial-safe AI images",
                "flux": "Black Forest Labs' Flux models"
            },
            "ai_video": {
                "sora": "OpenAI's Sora text-to-video model",
                "runway_gen3": "Runway Gen-3 Alpha for video generation",
                "pika": "Pika Labs video generation",
                "kling": "Kuaishou's Kling video AI"
            },
            "ai_music": {
                "suno": "Suno AI for music generation",
                "udio": "Udio for AI music creation",
                "stable_audio": "Stability AI's audio generation"
            }
        },
        "computing": {
            "apple_silicon": {
                "m4": "Apple M4 chip in new iPads and Macs",
                "m4_pro": "M4 Pro for professional Macs",
                "m4_max": "M4 Max for high-end MacBook Pro",
                "apple_intelligence": "Apple's on-device AI features"
            },
            "processors": {
                "intel_arrow_lake": "Intel's Arrow Lake desktop CPUs",
                "amd_zen5": "AMD Zen 5 architecture (Ryzen 9000 series)",
                "qualcomm_x_elite": "Qualcomm Snapdragon X Elite for Windows laptops"
            },
            "gpus": {
                "nvidia_rtx_50": "NVIDIA RTX 50 series (Blackwell architecture)",
                "nvidia_rtx_4090": "RTX 4090 still top consumer GPU",
                "amd_rdna4": "AMD RDNA 4 graphics cards",
                "intel_arc": "Intel Arc Battlemage GPUs"
            },
            "quantum": {
                "ibm_quantum": "IBM's 1000+ qubit quantum computers",
                "google_willow": "Google's Willow quantum chip breakthrough"
            }
        },
        "software": {
            "operating_systems": {
                "windows_11": "Windows 11 24H2 with Copilot+ features",
                "macos_sequoia": "macOS 15 Sequoia with Apple Intelligence",
                "ios_18": "iOS 18 with customization and AI features",
                "android_15": "Android 15 with enhanced privacy"
            },
            "development": {
                "github_copilot": "AI-powered coding assistant",
                "cursor": "AI-first code editor",
                "windsurf": "Codeium's AI IDE",
                "devin": "AI software engineer by Cognition",
                "v0": "Vercel's AI UI generator"
            }
        },
        "devices": {
            "smartphones": {
                "iphone_16": "iPhone 16 series with A18 chip and Apple Intelligence",
                "samsung_s24": "Samsung Galaxy S24 with Galaxy AI",
                "pixel_9": "Google Pixel 9 with Gemini Nano"
            },
            "wearables": {
                "apple_watch_10": "Apple Watch Series 10 with larger display",
                "vision_pro": "Apple Vision Pro spatial computer",
                "meta_quest_3": "Meta Quest 3 mixed reality headset",
                "ray_ban_meta": "Ray-Ban Meta smart glasses"
            },
            "ev_tech": {
                "tesla_fsd": "Tesla Full Self-Driving v12+ with neural networks",
                "waymo": "Waymo robotaxis in multiple US cities",
                "cruise": "GM Cruise autonomous vehicles"
            }
        }
    },
    
    # World Events 2024-2025
    "world_events": {
        "politics": {
            "us_election_2024": "2024 US Presidential Election",
            "global_elections": "Major elections worldwide in 2024-2025",
            "geopolitics": "Ongoing global geopolitical developments"
        },
        "economy": {
            "inflation": "Global inflation trends and central bank responses",
            "crypto": "Bitcoin ETFs approved, crypto market developments",
            "ai_economy": "AI's impact on jobs and economy"
        },
        "climate": {
            "extreme_weather": "Increasing extreme weather events globally",
            "renewable_energy": "Solar and wind energy growth",
            "ev_adoption": "Electric vehicle adoption acceleration",
            "cop29": "COP29 climate conference outcomes"
        },
        "space": {
            "artemis": "NASA Artemis program progress toward Moon return",
            "starship": "SpaceX Starship development and test flights",
            "mars_missions": "Mars exploration missions",
            "space_tourism": "Commercial space tourism expansion"
        }
    },
    
    # Entertainment & Culture 2025
    "entertainment": {
        "movies_2024_2025": {
            "blockbusters": [
                "Dune: Part Two (2024)",
                "Deadpool & Wolverine (2024)",
                "Inside Out 2 (2024)",
                "Wicked (2024)",
                "Gladiator II (2024)",
                "Avatar 3 (2025)",
                "Captain America: Brave New World (2025)",
                "Mission: Impossible 8 (2025)"
            ]
        },
        "tv_shows": {
            "popular_2024_2025": [
                "House of the Dragon Season 2",
                "The Bear Season 3",
                "Shogun",
                "Fallout",
                "3 Body Problem",
                "The Last of Us Season 2",
                "Stranger Things Season 5"
            ]
        },
        "music": {
            "top_artists_2024": [
                "Taylor Swift (Eras Tour continued)",
                "Beyoncé (Renaissance Tour, Cowboy Carter)",
                "Bad Bunny",
                "Drake",
                "The Weeknd",
                "Billie Eilish",
                "Sabrina Carpenter"
            ]
        },
        "gaming": {
            "major_releases_2024_2025": [
                "Elden Ring: Shadow of the Erdtree",
                "Final Fantasy VII Rebirth",
                "Dragon's Dogma 2",
                "Black Myth: Wukong",
                "GTA 6 (announced for 2025)",
                "Nintendo Switch 2 (expected 2025)"
            ]
        },
        "social_media": {
            "platforms": {
                "tiktok": "Dominant short-form video platform",
                "instagram": "Reels and social commerce focus",
                "youtube": "Shorts competing with TikTok",
                "x_twitter": "X (formerly Twitter) under Elon Musk",
                "threads": "Meta's Twitter alternative",
                "bluesky": "Decentralized social network growth"
            }
        }
    },
    
    # Science & Health 2025
    "science_health": {
        "medical_advances": {
            "weight_loss_drugs": "GLP-1 drugs (Ozempic, Wegovy, Mounjaro) revolution",
            "mrna_vaccines": "mRNA technology expanding beyond COVID",
            "gene_therapy": "CRISPR gene editing treatments approved",
            "ai_diagnostics": "AI in medical imaging and diagnosis",
            "longevity_research": "Anti-aging research breakthroughs"
        },
        "scientific_discoveries": {
            "fusion_energy": "Progress toward practical fusion power",
            "james_webb": "James Webb Space Telescope discoveries",
            "neuroscience": "Brain-computer interface advances (Neuralink)",
            "materials_science": "New materials and superconductor research"
        }
    },
    
    # Sports 2024-2025
    "sports": {
        "major_events": {
            "paris_olympics_2024": "2024 Summer Olympics in Paris, France",
            "super_bowl_2025": "Super Bowl LIX",
            "world_cup_2026": "FIFA World Cup 2026 (USA, Canada, Mexico)",
            "nba_2024_2025": "NBA season 2024-2025"
        },
        "notable_athletes": [
            "LeBron James (still active at 40)",
            "Lionel Messi (Inter Miami)",
            "Caitlin Clark (WNBA sensation)",
            "Shohei Ohtani (Dodgers)",
            "Patrick Mahomes (Chiefs)"
        ]
    },
    
    # Business & Companies 2025
    "business": {
        "tech_giants": {
            "apple": "Apple Intelligence, Vision Pro, services growth",
            "microsoft": "Copilot everywhere, OpenAI partnership",
            "google": "Gemini AI, search transformation",
            "amazon": "AWS AI services, Alexa LLM",
            "meta": "AI focus, Reality Labs, Threads",
            "nvidia": "AI chip dominance, $3T+ market cap",
            "tesla": "FSD progress, Optimus robot, energy business"
        },
        "ai_companies": {
            "openai": "ChatGPT, GPT-4, Sora, $100B+ valuation",
            "anthropic": "Claude AI, safety-focused approach",
            "mistral": "European AI leader",
            "cohere": "Enterprise AI solutions",
            "stability_ai": "Open-source AI models"
        }
    }
}

# Current date context
CURRENT_CONTEXT = {
    "year": 2025,
    "month": "December",
    "season": "Winter (Northern Hemisphere)",
    "upcoming_holidays": ["Christmas 2025", "New Year 2026"],
    "current_trends": [
        "AI integration in daily life",
        "Remote and hybrid work normalization",
        "Electric vehicle adoption",
        "Streaming service competition",
        "Social media evolution",
        "Climate awareness",
        "Mental health focus"
    ]
}


def get_2025_knowledge() -> Dict[str, Any]:
    """Get all 2025 knowledge."""
    return KNOWLEDGE_2025


def get_current_context() -> Dict[str, Any]:
    """Get current date/time context."""
    return CURRENT_CONTEXT


def search_2025_knowledge(query: str) -> str:
    """Search 2025 knowledge base for relevant information."""
    query_lower = query.lower()
    results = []
    
    def search_dict(d: Dict, path: str = ""):
        for key, value in d.items():
            current_path = f"{path}/{key}" if path else key
            
            if isinstance(value, dict):
                search_dict(value, current_path)
            elif isinstance(value, list):
                for item in value:
                    if query_lower in str(item).lower():
                        results.append(f"{current_path}: {item}")
            elif isinstance(value, str):
                if query_lower in key.lower() or query_lower in value.lower():
                    results.append(f"{current_path}: {value}")
    
    search_dict(KNOWLEDGE_2025)
    
    if results:
        return "\n".join(results[:10])  # Return top 10 results
    return ""


# Quick facts Monica should know
MONICA_QUICK_FACTS_2025 = """
Current Knowledge (December 2025):

**AI & Technology:**
- ChatGPT and Claude are the leading AI assistants
- Local AI (Ollama, LM Studio) is popular for privacy
- AI can generate images (Midjourney, DALL-E), video (Sora), and music (Suno)
- Apple Intelligence brings AI to iPhones and Macs
- NVIDIA dominates AI chips, RTX 50 series launching

**Recent Events:**
- 2024 US Presidential Election completed
- Paris 2024 Olympics were held
- Bitcoin ETFs approved in early 2024
- GLP-1 weight loss drugs (Ozempic) are hugely popular

**Entertainment:**
- Taylor Swift's Eras Tour is the biggest concert tour ever
- GTA 6 announced for 2025
- Nintendo Switch 2 expected in 2025
- Streaming wars continue (Netflix, Disney+, Max, etc.)

**Current Trends:**
- AI integration everywhere
- Electric vehicles mainstream
- Remote/hybrid work normal
- Mental health awareness high
- Climate action urgent
"""
