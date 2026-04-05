"""
Monica's Software & Programming Skills Knowledge Base
Adobe Creative Cloud, Programming Languages, Game Engines, 3D Software
"""

from typing import Dict, List, Any

# ADOBE CREATIVE CLOUD
ADOBE_KNOWLEDGE = {
    "photoshop": {
        "name": "Adobe Photoshop",
        "purpose": "Image editing and manipulation",
        "key_features": [
            "Layers and layer masks",
            "Selection tools (Lasso, Magic Wand, Quick Selection)",
            "Adjustment layers (Levels, Curves, Hue/Saturation)",
            "Filters and effects",
            "Content-Aware Fill",
            "Clone Stamp and Healing Brush",
            "Text and typography",
            "Smart Objects",
            "Actions and batch processing",
            "Camera Raw"
        ],
        "shortcuts": {
            "Ctrl+J": "Duplicate layer",
            "Ctrl+T": "Free Transform",
            "Ctrl+D": "Deselect",
            "Ctrl+Shift+I": "Invert selection",
            "B": "Brush tool",
            "V": "Move tool",
            "M": "Marquee selection",
            "L": "Lasso tool",
            "W": "Magic Wand",
            "[/]": "Decrease/Increase brush size"
        },
        "file_formats": ["PSD", "JPEG", "PNG", "TIFF", "GIF", "PDF", "RAW"]
    },
    "illustrator": {
        "name": "Adobe Illustrator",
        "purpose": "Vector graphics and illustration",
        "key_features": [
            "Pen tool and Bezier curves",
            "Shape tools",
            "Pathfinder operations",
            "Gradient mesh",
            "Pattern creation",
            "Typography and text on path",
            "Artboards",
            "Symbols and instances",
            "Image trace",
            "3D effects"
        ],
        "shortcuts": {
            "P": "Pen tool",
            "A": "Direct Selection",
            "V": "Selection tool",
            "Ctrl+G": "Group",
            "Ctrl+Shift+G": "Ungroup",
            "Ctrl+[/]": "Send backward/forward"
        },
        "file_formats": ["AI", "EPS", "SVG", "PDF"]
    },
    "premiere_pro": {
        "name": "Adobe Premiere Pro",
        "purpose": "Video editing",
        "key_features": [
            "Timeline editing",
            "Multi-track audio",
            "Color correction (Lumetri)",
            "Transitions and effects",
            "Motion graphics templates",
            "Audio mixing",
            "Multicam editing",
            "Proxy workflows",
            "Export presets",
            "Dynamic Link with After Effects"
        ],
        "shortcuts": {
            "I/O": "Set In/Out points",
            "C": "Razor tool",
            "V": "Selection tool",
            "Space": "Play/Pause",
            "J/K/L": "Reverse/Stop/Forward",
            "Ctrl+K": "Cut at playhead"
        }
    },
    "after_effects": {
        "name": "Adobe After Effects",
        "purpose": "Motion graphics and visual effects",
        "key_features": [
            "Keyframe animation",
            "Expressions",
            "3D layers and cameras",
            "Particle systems",
            "Rotoscoping",
            "Motion tracking",
            "Green screen (keying)",
            "Shape layers",
            "Text animation",
            "Plugins (Element 3D, Trapcode)"
        ],
        "shortcuts": {
            "U": "Show keyframes",
            "P/S/R/T": "Position/Scale/Rotation/Opacity",
            "Ctrl+D": "Duplicate layer",
            "Space": "RAM preview"
        }
    },
    "indesign": {
        "name": "Adobe InDesign",
        "purpose": "Page layout and publishing",
        "key_features": [
            "Master pages",
            "Paragraph and character styles",
            "Text threading",
            "Tables",
            "GREP styling",
            "Book feature",
            "Interactive PDFs",
            "EPUB export",
            "Data merge",
            "Preflight"
        ]
    },
    "lightroom": {
        "name": "Adobe Lightroom",
        "purpose": "Photo organization and editing",
        "key_features": [
            "Catalog management",
            "Non-destructive editing",
            "Presets",
            "Batch processing",
            "RAW processing",
            "Local adjustments",
            "HDR merge",
            "Panorama stitching"
        ]
    },
    "xd": {
        "name": "Adobe XD",
        "purpose": "UI/UX design and prototyping",
        "key_features": [
            "Artboards",
            "Components and states",
            "Repeat grid",
            "Prototyping and interactions",
            "Auto-animate",
            "Voice prototyping",
            "Design specs",
            "Collaboration"
        ]
    },
    "audition": {
        "name": "Adobe Audition",
        "purpose": "Audio editing and production",
        "key_features": [
            "Multitrack editing",
            "Spectral display",
            "Noise reduction",
            "Audio restoration",
            "Effects rack",
            "Podcast production"
        ]
    }
}

# PROGRAMMING LANGUAGES
PROGRAMMING_LANGUAGES = {
    "python": {
        "name": "Python",
        "paradigm": ["Object-oriented", "Functional", "Procedural"],
        "typing": "Dynamic",
        "use_cases": ["Web development", "Data science", "AI/ML", "Automation", "Scientific computing"],
        "key_concepts": {
            "basics": ["Variables", "Data types", "Operators", "Control flow", "Functions"],
            "data_structures": ["Lists", "Tuples", "Dictionaries", "Sets"],
            "oop": ["Classes", "Objects", "Inheritance", "Polymorphism", "Encapsulation"],
            "advanced": ["Decorators", "Generators", "Context managers", "Async/await"]
        },
        "popular_frameworks": ["Django", "Flask", "FastAPI", "PyTorch", "TensorFlow", "Pandas", "NumPy"],
        "example": '''
# Hello World
print("Hello, World!")

# Function
def greet(name):
    return f"Hello, {name}!"

# Class
class Person:
    def __init__(self, name):
        self.name = name
    
    def say_hello(self):
        return f"Hi, I'm {self.name}"
'''
    },
    "javascript": {
        "name": "JavaScript",
        "paradigm": ["Object-oriented", "Functional", "Event-driven"],
        "typing": "Dynamic",
        "use_cases": ["Web development", "Server-side (Node.js)", "Mobile apps", "Desktop apps"],
        "key_concepts": {
            "basics": ["Variables (let, const, var)", "Data types", "Functions", "Arrow functions"],
            "dom": ["Document Object Model", "Event handling", "DOM manipulation"],
            "async": ["Callbacks", "Promises", "Async/await", "Fetch API"],
            "es6+": ["Classes", "Modules", "Destructuring", "Spread operator", "Template literals"]
        },
        "popular_frameworks": ["React", "Vue", "Angular", "Node.js", "Express", "Next.js"],
        "example": '''
// Hello World
console.log("Hello, World!");

// Function
const greet = (name) => `Hello, ${name}!`;

// Class
class Person {
    constructor(name) {
        this.name = name;
    }
    
    sayHello() {
        return `Hi, I'm ${this.name}`;
    }
}
'''
    },
    "java": {
        "name": "Java",
        "paradigm": ["Object-oriented"],
        "typing": "Static",
        "use_cases": ["Enterprise applications", "Android apps", "Web services", "Big data"],
        "key_concepts": {
            "basics": ["Variables", "Data types", "Control flow", "Methods"],
            "oop": ["Classes", "Interfaces", "Inheritance", "Polymorphism", "Abstraction"],
            "advanced": ["Generics", "Collections", "Streams", "Lambda expressions", "Multithreading"]
        },
        "popular_frameworks": ["Spring", "Hibernate", "Maven", "Gradle"]
    },
    "cpp": {
        "name": "C++",
        "paradigm": ["Object-oriented", "Procedural", "Generic"],
        "typing": "Static",
        "use_cases": ["System programming", "Game development", "Embedded systems", "High-performance apps"],
        "key_concepts": {
            "basics": ["Variables", "Pointers", "References", "Memory management"],
            "oop": ["Classes", "Inheritance", "Virtual functions", "Operator overloading"],
            "stl": ["Vectors", "Maps", "Algorithms", "Iterators"],
            "modern": ["Smart pointers", "Move semantics", "Lambda expressions", "Templates"]
        }
    },
    "csharp": {
        "name": "C#",
        "paradigm": ["Object-oriented", "Functional"],
        "typing": "Static",
        "use_cases": ["Windows apps", "Game development (Unity)", "Web services", "Enterprise"],
        "key_concepts": {
            "basics": ["Variables", "Data types", "Control flow", "Methods"],
            "oop": ["Classes", "Interfaces", "Properties", "Events", "Delegates"],
            "advanced": ["LINQ", "Async/await", "Generics", "Reflection"]
        },
        "popular_frameworks": [".NET", "ASP.NET", "Unity", "Xamarin"]
    },
    "rust": {
        "name": "Rust",
        "paradigm": ["Systems", "Functional", "Concurrent"],
        "typing": "Static",
        "use_cases": ["Systems programming", "WebAssembly", "CLI tools", "Embedded"],
        "key_concepts": ["Ownership", "Borrowing", "Lifetimes", "Pattern matching", "Traits"]
    },
    "go": {
        "name": "Go (Golang)",
        "paradigm": ["Procedural", "Concurrent"],
        "typing": "Static",
        "use_cases": ["Cloud services", "Microservices", "CLI tools", "DevOps"],
        "key_concepts": ["Goroutines", "Channels", "Interfaces", "Packages"]
    },
    "swift": {
        "name": "Swift",
        "paradigm": ["Object-oriented", "Functional", "Protocol-oriented"],
        "typing": "Static",
        "use_cases": ["iOS/macOS apps", "Server-side"],
        "key_concepts": ["Optionals", "Closures", "Protocols", "Extensions", "Generics"]
    },
    "kotlin": {
        "name": "Kotlin",
        "paradigm": ["Object-oriented", "Functional"],
        "typing": "Static",
        "use_cases": ["Android apps", "Server-side", "Multiplatform"],
        "key_concepts": ["Null safety", "Data classes", "Coroutines", "Extension functions"]
    },
    "typescript": {
        "name": "TypeScript",
        "paradigm": ["Object-oriented", "Functional"],
        "typing": "Static (superset of JavaScript)",
        "use_cases": ["Large-scale web apps", "Node.js", "React/Angular/Vue"],
        "key_concepts": ["Types", "Interfaces", "Generics", "Decorators", "Modules"]
    },
    "sql": {
        "name": "SQL",
        "paradigm": ["Declarative"],
        "use_cases": ["Database queries", "Data analysis", "Reporting"],
        "key_concepts": {
            "basics": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "joins": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"],
            "advanced": ["Subqueries", "CTEs", "Window functions", "Indexes"]
        }
    },
    "html_css": {
        "name": "HTML/CSS",
        "purpose": "Web page structure and styling",
        "html_concepts": ["Elements", "Attributes", "Semantic HTML", "Forms", "Tables"],
        "css_concepts": ["Selectors", "Box model", "Flexbox", "Grid", "Animations", "Media queries"]
    }
}

# 3D SOFTWARE
SOFTWARE_3D = {
    "blender": {
        "name": "Blender",
        "purpose": "3D modeling, animation, rendering",
        "price": "Free and open source",
        "features": {
            "modeling": ["Mesh modeling", "Sculpting", "Modifiers", "Curves", "Text"],
            "animation": ["Keyframes", "Armatures", "Shape keys", "NLA editor", "Motion capture"],
            "rendering": ["Cycles (path tracing)", "Eevee (real-time)", "Workbench"],
            "simulation": ["Physics", "Cloth", "Fluid", "Smoke", "Particles"],
            "compositing": ["Node-based", "Color correction", "Keying"],
            "video_editing": ["Timeline", "Transitions", "Effects"]
        },
        "shortcuts": {
            "G": "Grab/Move",
            "R": "Rotate",
            "S": "Scale",
            "E": "Extrude",
            "Tab": "Edit/Object mode toggle",
            "Shift+A": "Add menu",
            "X": "Delete",
            "Ctrl+R": "Loop cut"
        }
    },
    "unity": {
        "name": "Unity",
        "purpose": "Game engine and real-time 3D",
        "language": "C#",
        "features": {
            "core": ["Scene management", "GameObjects", "Components", "Prefabs"],
            "graphics": ["Materials", "Shaders", "Lighting", "Post-processing"],
            "physics": ["Rigidbody", "Colliders", "Joints", "Raycasting"],
            "animation": ["Animator", "Animation clips", "Blend trees", "IK"],
            "ui": ["Canvas", "UI elements", "Event system"],
            "scripting": ["MonoBehaviour", "Coroutines", "Events", "ScriptableObjects"]
        },
        "key_concepts": {
            "lifecycle": ["Awake()", "Start()", "Update()", "FixedUpdate()", "LateUpdate()"],
            "input": ["Input.GetKey()", "Input.GetAxis()", "New Input System"],
            "physics": ["OnCollisionEnter()", "OnTriggerEnter()"]
        }
    },
    "unreal_engine": {
        "name": "Unreal Engine",
        "purpose": "Game engine and real-time 3D",
        "languages": ["C++", "Blueprints (visual scripting)"],
        "features": {
            "graphics": ["Nanite", "Lumen", "Materials", "Niagara particles"],
            "world_building": ["Landscape", "Foliage", "World Partition"],
            "animation": ["Sequencer", "Control Rig", "Animation Blueprints"],
            "physics": ["Chaos physics", "Destruction"]
        }
    }
}

# COMPUTER BUILDING
COMPUTER_BUILDING = {
    "components": {
        "cpu": {
            "name": "Central Processing Unit",
            "function": "Brain of the computer, executes instructions",
            "brands": ["Intel", "AMD"],
            "specs": ["Cores", "Threads", "Clock speed (GHz)", "Cache", "TDP"],
            "installation": "Apply thermal paste, align with socket, secure cooler"
        },
        "motherboard": {
            "name": "Motherboard",
            "function": "Main circuit board connecting all components",
            "form_factors": ["ATX", "Micro-ATX", "Mini-ITX"],
            "features": ["CPU socket", "RAM slots", "PCIe slots", "M.2 slots", "I/O ports"]
        },
        "ram": {
            "name": "Random Access Memory",
            "function": "Short-term memory for active programs",
            "types": ["DDR4", "DDR5"],
            "specs": ["Capacity (GB)", "Speed (MHz)", "Latency (CL)"],
            "installation": "Align notch, press firmly until clips click"
        },
        "storage": {
            "types": {
                "ssd_nvme": "Fastest, connects via M.2 slot",
                "ssd_sata": "Fast, connects via SATA cable",
                "hdd": "Slower but cheaper, good for mass storage"
            }
        },
        "gpu": {
            "name": "Graphics Processing Unit",
            "function": "Renders graphics, accelerates parallel tasks",
            "brands": ["NVIDIA", "AMD"],
            "specs": ["VRAM", "CUDA/Stream cores", "Clock speed", "TDP"]
        },
        "psu": {
            "name": "Power Supply Unit",
            "function": "Converts AC to DC power for components",
            "specs": ["Wattage", "Efficiency rating (80+)", "Modularity"],
            "calculation": "Sum component TDP + 20% headroom"
        },
        "case": {
            "name": "Computer Case",
            "function": "Houses and protects components",
            "considerations": ["Size", "Airflow", "Cable management", "Aesthetics"]
        },
        "cooling": {
            "types": {
                "air": "Heatsink with fans",
                "aio": "All-in-one liquid cooler",
                "custom_loop": "Custom liquid cooling"
            }
        }
    },
    "build_steps": [
        "1. Install CPU on motherboard",
        "2. Install RAM",
        "3. Install M.2 SSD (if applicable)",
        "4. Mount motherboard in case",
        "5. Install power supply",
        "6. Install GPU",
        "7. Connect all cables",
        "8. Install storage drives",
        "9. Cable management",
        "10. First boot and BIOS setup",
        "11. Install operating system"
    ]
}


class SoftwareSkillsSystem:
    """Complete software and programming skills"""
    
    def __init__(self):
        self.adobe = ADOBE_KNOWLEDGE
        self.programming = PROGRAMMING_LANGUAGES
        self.software_3d = SOFTWARE_3D
        self.computer_building = COMPUTER_BUILDING
        print("[OK] Software Skills System initialized")
        print(f"   - {len(self.adobe)} Adobe apps")
        print(f"   - {len(self.programming)} programming languages")
        print(f"   - {len(self.software_3d)} 3D/game engines")
    
    def get_adobe_app(self, app: str) -> Dict:
        return self.adobe.get(app.lower(), {})
    
    def get_language(self, lang: str) -> Dict:
        return self.programming.get(lang.lower(), {})
    
    def get_3d_software(self, software: str) -> Dict:
        return self.software_3d.get(software.lower(), {})
    
    def search_all(self, query: str) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        # Search Adobe
        for app, data in self.adobe.items():
            if query_lower in str(data).lower():
                results.append({"category": "Adobe", "item": app, "data": data})
        
        # Search Programming
        for lang, data in self.programming.items():
            if query_lower in str(data).lower():
                results.append({"category": "Programming", "item": lang, "data": data})
        
        return results


_software_system = None

def get_software_skills() -> SoftwareSkillsSystem:
    global _software_system
    if _software_system is None:
        _software_system = SoftwareSkillsSystem()
    return _software_system


if __name__ == "__main__":
    skills = get_software_skills()
    
    print("\n--- Photoshop Shortcuts ---")
    ps = skills.get_adobe_app("photoshop")
    for key, action in list(ps.get("shortcuts", {}).items())[:5]:
        print(f"  {key}: {action}")
    
    print("\n--- Python Frameworks ---")
    py = skills.get_language("python")
    print(f"  {py.get('popular_frameworks', [])}")
