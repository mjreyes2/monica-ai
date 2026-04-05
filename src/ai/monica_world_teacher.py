"""
Monica AI - World Languages & Programming Teacher

Comprehensive teaching system for:
- Human languages: Spanish, French, Italian, Arabic, Mandarin, Russian, Haitian Creole, + more
- Programming languages: Python, JavaScript, C++, Java, Rust, Go, SQL, HTML/CSS, + more
- Developer tools: Git, Docker, Linux, AWS, databases, APIs, etc.

Each language has:
- Vocabulary with spaced repetition tracking
- Grammar rules and explanations
- Quiz system (multiple choice, fill-in-blank, translation)
- Pronunciation guides (human languages)
- Code challenges (programming languages)
- Progress persistence in data/user_profile/language_progress.json
"""

import json
import time
import random
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("Monica.WorldTeacher")


@dataclass
class LangWord:
    """A vocabulary word being tracked in any language."""
    word: str
    translation: str
    example: str
    pronunciation: str = ""
    language: str = ""
    category: str = ""
    times_correct: int = 0
    times_wrong: int = 0
    last_seen: float = 0.0
    mastered: bool = False


@dataclass
class LangQuizResult:
    """Result of a language quiz."""
    language: str
    timestamp: float
    total: int
    correct: int
    score_percent: float


# ============================================================
#  HUMAN LANGUAGE DATA
# ============================================================

LANGUAGE_VOCAB = {
    "spanish": {
        "info": {"name": "Spanish", "native": "Espanol", "difficulty": "Easy (600 hrs)"},
        "greetings": [
            ("Hola", "Hello", "Hola, como estas?", "OH-lah"),
            ("Buenos dias", "Good morning", "Buenos dias, senor.", "BWEH-nohs DEE-ahs"),
            ("Buenas noches", "Good night", "Buenas noches, hasta manana.", "BWEH-nahs NOH-chehs"),
            ("Adios", "Goodbye", "Adios, nos vemos!", "ah-dee-OHS"),
            ("Por favor", "Please", "Un cafe, por favor.", "por fah-VOR"),
            ("Gracias", "Thank you", "Muchas gracias por tu ayuda.", "GRAH-see-ahs"),
            ("De nada", "You're welcome", "De nada, fue un placer.", "deh NAH-dah"),
            ("Lo siento", "I'm sorry", "Lo siento, no lo sabia.", "loh see-EHN-toh"),
        ],
        "essentials": [
            ("Yo soy", "I am", "Yo soy estudiante.", "yoh soy"),
            ("Tu eres", "You are", "Tu eres muy amable.", "too EH-rehs"),
            ("El/Ella es", "He/She is", "Ella es mi amiga.", "ehl/EH-yah ehs"),
            ("Nosotros somos", "We are", "Nosotros somos amigos.", "noh-SOH-trohs SOH-mohs"),
            ("Donde esta", "Where is", "Donde esta el bano?", "DOHN-deh ehs-TAH"),
            ("Cuanto cuesta", "How much does it cost", "Cuanto cuesta esto?", "KWAHN-toh KWEHS-tah"),
            ("Necesito", "I need", "Necesito agua, por favor.", "neh-seh-SEE-toh"),
            ("Entiendo", "I understand", "No entiendo espanol.", "ehn-tee-EHN-doh"),
            ("Hablas ingles?", "Do you speak English?", "Disculpa, hablas ingles?", "AH-blahs een-GLEHS"),
            ("Me llamo", "My name is", "Me llamo Monica.", "meh YAH-moh"),
        ],
        "numbers": [
            ("Uno", "One", "Tengo uno.", "OO-noh"),
            ("Dos", "Two", "Dame dos, por favor.", "dohs"),
            ("Tres", "Three", "Son tres personas.", "trehs"),
            ("Diez", "Ten", "Cuesta diez dolares.", "dee-EHS"),
            ("Cien", "One hundred", "Hay cien estudiantes.", "see-EHN"),
        ],
        "grammar": [
            {"rule": "Gender agreement", "explanation": "Nouns are masculine (el) or feminine (la). Adjectives must match: el gato negro, la casa blanca."},
            {"rule": "Ser vs Estar", "explanation": "Ser = permanent (Soy alto = I am tall). Estar = temporary/location (Estoy cansado = I am tired)."},
            {"rule": "Verb conjugation -ar", "explanation": "hablar: yo hablo, tu hablas, el habla, nosotros hablamos, ellos hablan."},
            {"rule": "Verb conjugation -er", "explanation": "comer: yo como, tu comes, el come, nosotros comemos, ellos comen."},
            {"rule": "Verb conjugation -ir", "explanation": "vivir: yo vivo, tu vives, el vive, nosotros vivimos, ellos viven."},
        ],
    },
    "french": {
        "info": {"name": "French", "native": "Francais", "difficulty": "Easy (750 hrs)"},
        "greetings": [
            ("Bonjour", "Hello/Good day", "Bonjour, comment allez-vous?", "bohn-ZHOOR"),
            ("Bonsoir", "Good evening", "Bonsoir, madame.", "bohn-SWAHR"),
            ("Au revoir", "Goodbye", "Au revoir, a bientot!", "oh ruh-VWAHR"),
            ("Merci", "Thank you", "Merci beaucoup!", "mehr-SEE"),
            ("S'il vous plait", "Please", "Un cafe, s'il vous plait.", "seel voo PLEH"),
            ("Excusez-moi", "Excuse me", "Excusez-moi, ou est la gare?", "ehk-skew-ZAY mwah"),
            ("Oui", "Yes", "Oui, bien sur!", "wee"),
            ("Non", "No", "Non, merci.", "nohn"),
        ],
        "essentials": [
            ("Je suis", "I am", "Je suis etudiant.", "zhuh SWEE"),
            ("Parlez-vous anglais?", "Do you speak English?", "", "par-LAY voo ahn-GLEH"),
            ("Je ne comprends pas", "I don't understand", "", "zhuh nuh kohm-PRAHN pah"),
            ("Comment vous appelez-vous?", "What is your name?", "", "koh-MAHN voo zah-play VOO"),
            ("Combien ca coute?", "How much?", "Combien ca coute, ce livre?", "kohm-bee-EHN sah KOOT"),
            ("Ou est", "Where is", "Ou est la pharmacie?", "oo EH"),
            ("J'ai besoin de", "I need", "J'ai besoin d'aide.", "zhay buh-ZWAHN duh"),
            ("Je voudrais", "I would like", "Je voudrais un croissant.", "zhuh voo-DREH"),
        ],
        "grammar": [
            {"rule": "Gender articles", "explanation": "le (masc), la (fem), les (plural). Le livre (the book), la maison (the house)."},
            {"rule": "Negation", "explanation": "Wrap verb with ne...pas: Je ne parle pas francais (I don't speak French)."},
            {"rule": "Etre conjugation", "explanation": "je suis, tu es, il/elle est, nous sommes, vous etes, ils/elles sont."},
            {"rule": "Avoir conjugation", "explanation": "j'ai, tu as, il/elle a, nous avons, vous avez, ils/elles ont."},
        ],
    },
    "italian": {
        "info": {"name": "Italian", "native": "Italiano", "difficulty": "Easy (600 hrs)"},
        "greetings": [
            ("Ciao", "Hello/Bye (informal)", "Ciao, come stai?", "CHOW"),
            ("Buongiorno", "Good morning", "Buongiorno, signora.", "bwohn-JOHR-noh"),
            ("Buonasera", "Good evening", "Buonasera a tutti.", "bwoh-nah-SEH-rah"),
            ("Grazie", "Thank you", "Grazie mille!", "GRAHT-see-eh"),
            ("Prego", "You're welcome", "Prego, di niente.", "PREH-goh"),
            ("Scusa", "Excuse me", "Scusa, dove il bagno?", "SKOO-zah"),
            ("Per favore", "Please", "Un espresso, per favore.", "pehr fah-VOH-reh"),
        ],
        "essentials": [
            ("Io sono", "I am", "Io sono americano.", "EE-oh SOH-noh"),
            ("Quanto costa?", "How much?", "Quanto costa questo?", "KWAHN-toh KOH-stah"),
            ("Dove", "Where is", "Dove la stazione?", "DOH-veh"),
            ("Non capisco", "I don't understand", "", "nohn kah-PEE-skoh"),
            ("Parli inglese?", "Do you speak English?", "", "PAR-lee een-GLEH-zeh"),
            ("Mi chiamo", "My name is", "Mi chiamo Monica.", "mee kee-AH-moh"),
            ("Vorrei", "I would like", "Vorrei una pizza.", "vohr-RAY"),
        ],
        "grammar": [
            {"rule": "Articles", "explanation": "il/lo (masc), la (fem), i/gli (masc pl), le (fem pl)."},
            {"rule": "Verb -are", "explanation": "parlare: io parlo, tu parli, lui parla, noi parliamo, loro parlano."},
            {"rule": "Essere", "explanation": "io sono, tu sei, lui/lei e, noi siamo, voi siete, loro sono."},
        ],
    },
    "arabic": {
        "info": {"name": "Arabic", "native": "al-Arabiyyah", "difficulty": "Hard (2200 hrs)"},
        "greetings": [
            ("Marhaba", "Hello", "Marhaba, kayf halak?", "MAR-ha-ba"),
            ("As-salamu alaykum", "Peace be upon you", "As-salamu alaykum wa rahmatullah.", "as-sa-LA-mu a-LAY-kum"),
            ("Shukran", "Thank you", "Shukran jazilan!", "SHUK-ran"),
            ("Min fadlak/fadlik", "Please (m/f)", "Min fadlak, sa'idni.", "min FAD-lak"),
            ("Ma'a salama", "Goodbye", "Ma'a salama, ila al-liqa.", "MA-a sa-LA-ma"),
            ("Na'am", "Yes", "Na'am, sahih.", "NA-am"),
            ("La", "No", "La, shukran.", "la"),
            ("Afwan", "Excuse me", "Afwan, ayna al-funduq?", "AF-wan"),
        ],
        "essentials": [
            ("Ana", "I am", "Ana talib (I am a student).", "A-na"),
            ("Ayna", "Where", "Ayna al-hammam?", "AY-na"),
            ("Kam", "How much", "Kam hatha? (How much is this?)", "kam"),
            ("Uhibb", "I love", "Uhibb al-arabiyyah.", "u-HIBB"),
            ("La afham", "I don't understand", "", "la AF-ham"),
            ("Hal tatakallam al-ingliziyyah?", "Do you speak English?", "", "hal ta-ta-KAL-lam"),
        ],
        "grammar": [
            {"rule": "Right-to-left script", "explanation": "Arabic is written right-to-left. Letters connect in most cases."},
            {"rule": "Root system", "explanation": "Most words derive from 3-letter roots: k-t-b = write (kitab=book, katib=writer, maktaba=library)."},
            {"rule": "Gender", "explanation": "Nouns are masculine or feminine. Feminine usually ends in -a (ta marbuta)."},
        ],
    },
    "mandarin": {
        "info": {"name": "Mandarin Chinese", "native": "Putonghua", "difficulty": "Hard (2200 hrs)"},
        "greetings": [
            ("Ni hao", "Hello", "Ni hao, ni hao ma?", "nee HOW"),
            ("Zai jian", "Goodbye", "Zai jian, mingtian jian!", "dzai jee-EN"),
            ("Xie xie", "Thank you", "Xie xie ni de bangzhu.", "shee-eh shee-eh"),
            ("Bu keqi", "You're welcome", "", "boo kuh-chee"),
            ("Dui bu qi", "Sorry", "Dui bu qi, wo chi dao le.", "dway boo chee"),
            ("Qing", "Please", "Qing zuo.", "ching"),
            ("Shi", "Yes", "Shi de, meiyou wenti.", "shir"),
            ("Bu shi", "No", "Bu shi, wo bu zhidao.", "boo shir"),
        ],
        "essentials": [
            ("Wo shi", "I am", "Wo shi xuesheng (I am a student).", "woh shir"),
            ("Duo shao qian?", "How much?", "Zhe ge duo shao qian?", "dwoh shaow chee-EN"),
            ("Zai nar?", "Where is?", "Cesuo zai nar? (Where is the bathroom?)", "dzai nar"),
            ("Wo bu dong", "I don't understand", "", "woh boo dohng"),
            ("Ni hui shuo yingyu ma?", "Do you speak English?", "", "nee hway shwoh"),
            ("Wo jiao", "My name is", "Wo jiao Monica.", "woh jee-OW"),
        ],
        "grammar": [
            {"rule": "Tones", "explanation": "4 tones change meaning: ma(1)=mother, ma(2)=hemp, ma(3)=horse, ma(4)=scold."},
            {"rule": "SVO order", "explanation": "Subject-Verb-Object like English: Wo (I) chi (eat) fan (rice)."},
            {"rule": "Measure words", "explanation": "Numbers need classifiers: yi ge ren (one person), liang ben shu (two books)."},
            {"rule": "No conjugation", "explanation": "Verbs don't change form. Tense shown by time words: wo zuotian chi (I yesterday eat)."},
        ],
    },
    "russian": {
        "info": {"name": "Russian", "native": "Russkiy", "difficulty": "Hard (1100 hrs)"},
        "greetings": [
            ("Privet", "Hi (informal)", "Privet, kak dela?", "pree-VYET"),
            ("Zdravstvuyte", "Hello (formal)", "Zdravstvuyte, kak vy?", "ZDRAHST-vuy-tyeh"),
            ("Spasibo", "Thank you", "Spasibo bolshoye!", "spah-SEE-bah"),
            ("Pozhaluysta", "Please/You're welcome", "Pozhaluysta, pomogite.", "pah-ZHAH-luh-stah"),
            ("Da", "Yes", "Da, konechno.", "dah"),
            ("Nyet", "No", "Nyet, spasibo.", "nyet"),
            ("Do svidaniya", "Goodbye", "Do svidaniya, drug!", "dah svee-DAH-nee-yah"),
            ("Izvinite", "Excuse me", "Izvinite, gde vokzal?", "eez-vee-NEE-tyeh"),
        ],
        "essentials": [
            ("Ya", "I", "Ya student (I am a student).", "yah"),
            ("Skolko stoit?", "How much?", "Skolko stoit eto?", "SKOHL-kah STOH-eet"),
            ("Gde", "Where", "Gde tualet?", "gdyeh"),
            ("Ya ne ponimayu", "I don't understand", "", "yah nyeh pah-nee-MAH-yoo"),
            ("Vy govorite po-angliyski?", "Do you speak English?", "", "vih gah-vah-REE-tyeh"),
            ("Menya zovut", "My name is", "Menya zovut Monica.", "mee-NYAH zah-VOOT"),
        ],
        "grammar": [
            {"rule": "Cyrillic alphabet", "explanation": "33 letters. Some look like Latin but sound different: P=R, H=N, C=S."},
            {"rule": "6 cases", "explanation": "Nominative, Genitive, Dative, Accusative, Instrumental, Prepositional. Nouns change endings."},
            {"rule": "Gender", "explanation": "Masculine (consonant), Feminine (-a/-ya), Neuter (-o/-e). Affects adjective endings."},
        ],
    },
    "haitian_creole": {
        "info": {"name": "Haitian Creole", "native": "Kreyol Ayisyen", "difficulty": "Easy (600 hrs)"},
        "greetings": [
            ("Bonjou", "Hello/Good morning", "Bonjou, koman ou ye?", "bohn-ZHOO"),
            ("Bonswa", "Good evening", "Bonswa, zanmi.", "bohn-SWAH"),
            ("Mesi", "Thank you", "Mesi anpil!", "meh-SEE"),
            ("Souple", "Please", "Yon kafe, souple.", "SOO-pleh"),
            ("Wi", "Yes", "Wi, mwen dakò.", "wee"),
            ("Non", "No", "Non, mesi.", "nohn"),
            ("Orevwa", "Goodbye", "Orevwa, na we pita!", "oh-reh-VWAH"),
            ("Eskize m", "Excuse me", "Eskize m, ki kote...", "ehs-kee-ZAY m"),
        ],
        "essentials": [
            ("Mwen se", "I am", "Mwen se yon etidyan.", "mwehn seh"),
            ("Koman ou rele?", "What's your name?", "", "koh-MAHN oo reh-LEH"),
            ("Mwen rele", "My name is", "Mwen rele Monica.", "mwehn reh-LEH"),
            ("Mwen pa konprann", "I don't understand", "", "mwehn pah kohn-PRAHN"),
            ("Eske ou pale angle?", "Do you speak English?", "", "EHS-keh oo PAH-leh AHN-gleh"),
            ("Konbyen?", "How much?", "Konbyen sa koute?", "kohn-BYEHN"),
            ("Ki kote", "Where is", "Ki kote twalèt la?", "kee KOH-teh"),
            ("Mwen renmen", "I love", "Mwen renmen Ayiti.", "mwehn rehn-MEHN"),
        ],
        "grammar": [
            {"rule": "No conjugation", "explanation": "Verbs don't conjugate: mwen manje, ou manje, li manje (I/you/he eat)."},
            {"rule": "Tense markers", "explanation": "te (past), ap (present continuous), pral (future): Mwen te manje (I ate), Mwen ap manje (I'm eating)."},
            {"rule": "Articles after noun", "explanation": "Definite article comes AFTER: liv la (the book), kay la (the house)."},
            {"rule": "French-based", "explanation": "Many words from French but simplified grammar. Bonjou=Bonjour, mesi=merci."},
        ],
    },
}

# ============================================================
#  PROGRAMMING LANGUAGE DATA
# ============================================================

PROGRAMMING_LANGS = {
    "python": {
        "info": {"name": "Python", "type": "General-purpose", "difficulty": "Beginner-friendly", "paradigm": "Multi-paradigm"},
        "concepts": [
            ("Variables", "name = 'Monica'", "Store data in named containers", "basics"),
            ("Lists", "items = [1, 2, 3]", "Ordered mutable collections", "data_structures"),
            ("Dictionaries", "d = {'key': 'value'}", "Key-value pairs", "data_structures"),
            ("Functions", "def greet(name): return f'Hi {name}'", "Reusable code blocks", "basics"),
            ("Classes", "class Dog: def bark(self): print('Woof')", "Object-oriented blueprints", "oop"),
            ("List comprehension", "[x**2 for x in range(10)]", "Concise list creation", "intermediate"),
            ("Decorators", "@property, @staticmethod", "Modify function behavior", "advanced"),
            ("Context managers", "with open('f.txt') as f:", "Automatic resource management", "intermediate"),
            ("Generators", "def gen(): yield 1; yield 2", "Lazy iteration", "advanced"),
            ("Lambda", "square = lambda x: x**2", "Anonymous functions", "intermediate"),
        ],
        "challenges": [
            {"title": "FizzBuzz", "description": "Print 1-100, but 'Fizz' for multiples of 3, 'Buzz' for 5, 'FizzBuzz' for both.", "difficulty": "easy"},
            {"title": "Palindrome checker", "description": "Write a function that checks if a string is a palindrome.", "difficulty": "easy"},
            {"title": "Fibonacci", "description": "Generate the first N Fibonacci numbers using a generator.", "difficulty": "medium"},
            {"title": "File word counter", "description": "Read a file and count the frequency of each word.", "difficulty": "medium"},
        ],
    },
    "javascript": {
        "info": {"name": "JavaScript", "type": "Web/Full-stack", "difficulty": "Beginner-friendly", "paradigm": "Multi-paradigm"},
        "concepts": [
            ("let/const", "const name = 'Monica'; let age = 25;", "Variable declarations (prefer const)", "basics"),
            ("Arrow functions", "const add = (a, b) => a + b;", "Concise function syntax", "basics"),
            ("Promises", "fetch(url).then(r => r.json())", "Async operation handling", "intermediate"),
            ("async/await", "const data = await fetch(url);", "Cleaner async syntax", "intermediate"),
            ("Destructuring", "const {name, age} = person;", "Extract values from objects/arrays", "intermediate"),
            ("Spread operator", "const arr2 = [...arr1, 4, 5];", "Expand iterables", "intermediate"),
            ("Map/Filter/Reduce", "arr.map(x => x * 2).filter(x => x > 5)", "Functional array methods", "intermediate"),
            ("Classes", "class Animal { constructor(name) {} }", "ES6 class syntax", "oop"),
            ("Modules", "import { func } from './module.js';", "Code organization", "intermediate"),
            ("DOM manipulation", "document.querySelector('.btn').addEventListener('click', fn)", "Browser interaction", "web"),
        ],
        "challenges": [
            {"title": "Array flatten", "description": "Write a function that flattens a nested array: [1,[2,[3]]] -> [1,2,3].", "difficulty": "medium"},
            {"title": "Debounce", "description": "Implement a debounce function that delays execution until N ms of inactivity.", "difficulty": "medium"},
            {"title": "Promise.all", "description": "Implement your own version of Promise.all.", "difficulty": "hard"},
        ],
    },
    "cpp": {
        "info": {"name": "C++", "type": "Systems/Performance", "difficulty": "Advanced", "paradigm": "Multi-paradigm"},
        "concepts": [
            ("Pointers", "int* ptr = &value;", "Memory addresses", "basics"),
            ("References", "int& ref = value;", "Aliases to variables", "basics"),
            ("Classes", "class Vec { int x, y; public: Vec(int a, int b); };", "Object-oriented", "oop"),
            ("Templates", "template<typename T> T max(T a, T b)", "Generic programming", "advanced"),
            ("STL containers", "std::vector<int>, std::map<string,int>", "Standard library", "intermediate"),
            ("Smart pointers", "std::unique_ptr<T>, std::shared_ptr<T>", "Automatic memory management", "advanced"),
            ("RAII", "Resource Acquisition Is Initialization", "Deterministic cleanup", "advanced"),
            ("Move semantics", "std::move(obj)", "Efficient transfers", "advanced"),
        ],
    },
    "java": {
        "info": {"name": "Java", "type": "Enterprise/Android", "difficulty": "Intermediate", "paradigm": "Object-oriented"},
        "concepts": [
            ("Classes", "public class Main { public static void main(String[] args) {} }", "Everything is a class", "basics"),
            ("Interfaces", "interface Printable { void print(); }", "Contracts for classes", "oop"),
            ("Generics", "List<String> names = new ArrayList<>();", "Type-safe collections", "intermediate"),
            ("Streams", "list.stream().filter(x -> x > 5).collect(Collectors.toList())", "Functional pipeline", "intermediate"),
            ("Exceptions", "try { } catch (Exception e) { } finally { }", "Error handling", "basics"),
            ("Annotations", "@Override, @Autowired, @Test", "Metadata for code", "intermediate"),
        ],
    },
    "rust": {
        "info": {"name": "Rust", "type": "Systems/Safety", "difficulty": "Advanced", "paradigm": "Multi-paradigm"},
        "concepts": [
            ("Ownership", "let s1 = String::from('hi'); let s2 = s1;", "Memory safety without GC", "core"),
            ("Borrowing", "fn len(s: &String) -> usize", "References without ownership", "core"),
            ("Enums + match", "match color { Red => .., Blue => .. }", "Pattern matching", "basics"),
            ("Traits", "trait Display { fn fmt(&self) -> String; }", "Shared behavior", "intermediate"),
            ("Result/Option", "fn parse() -> Result<i32, Error>", "Error handling", "basics"),
            ("Lifetimes", "fn longest<'a>(s1: &'a str, s2: &'a str) -> &'a str", "Reference validity", "advanced"),
        ],
    },
    "go": {
        "info": {"name": "Go", "type": "Cloud/Backend", "difficulty": "Intermediate", "paradigm": "Concurrent"},
        "concepts": [
            ("Goroutines", "go func() { fmt.Println('async') }()", "Lightweight threads", "core"),
            ("Channels", "ch := make(chan int); ch <- 42", "Communication between goroutines", "core"),
            ("Interfaces", "type Writer interface { Write([]byte) error }", "Implicit implementation", "intermediate"),
            ("Structs", "type Person struct { Name string; Age int }", "Custom types", "basics"),
            ("Defer", "defer file.Close()", "Cleanup on function exit", "basics"),
            ("Error handling", "if err != nil { return err }", "Explicit error checks", "basics"),
        ],
    },
    "sql": {
        "info": {"name": "SQL", "type": "Database", "difficulty": "Beginner-friendly", "paradigm": "Declarative"},
        "concepts": [
            ("SELECT", "SELECT name, age FROM users WHERE age > 21;", "Query data", "basics"),
            ("JOIN", "SELECT * FROM orders JOIN users ON orders.user_id = users.id;", "Combine tables", "intermediate"),
            ("GROUP BY", "SELECT dept, COUNT(*) FROM emp GROUP BY dept;", "Aggregate data", "intermediate"),
            ("INDEX", "CREATE INDEX idx_name ON users(name);", "Speed up queries", "optimization"),
            ("Subqueries", "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);", "Nested queries", "intermediate"),
            ("Window functions", "ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC)", "Advanced analytics", "advanced"),
        ],
    },
    "html_css": {
        "info": {"name": "HTML/CSS", "type": "Web Frontend", "difficulty": "Beginner", "paradigm": "Markup/Styling"},
        "concepts": [
            ("Semantic HTML", "<header>, <nav>, <main>, <article>, <footer>", "Meaningful structure", "basics"),
            ("Flexbox", "display: flex; justify-content: center;", "1D layout", "layout"),
            ("Grid", "display: grid; grid-template-columns: 1fr 1fr;", "2D layout", "layout"),
            ("Responsive", "@media (max-width: 768px) { ... }", "Mobile-first design", "intermediate"),
            ("CSS Variables", "--primary: #007bff; color: var(--primary);", "Reusable values", "intermediate"),
            ("Animations", "@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }", "Motion", "intermediate"),
        ],
    },
}

DEV_TOOLS = {
    "git": {
        "info": {"name": "Git", "type": "Version Control"},
        "commands": [
            ("git init", "Initialize new repo", "basics"),
            ("git clone url", "Clone remote repo", "basics"),
            ("git add . && git commit -m 'msg'", "Stage and commit", "basics"),
            ("git branch feature && git checkout feature", "Create and switch branch", "branching"),
            ("git merge feature", "Merge branch", "branching"),
            ("git rebase main", "Rebase onto main", "advanced"),
            ("git stash && git stash pop", "Temporarily save changes", "intermediate"),
            ("git log --oneline --graph", "Visual commit history", "basics"),
        ],
    },
    "docker": {
        "info": {"name": "Docker", "type": "Containerization"},
        "commands": [
            ("docker build -t myapp .", "Build image from Dockerfile", "basics"),
            ("docker run -p 8080:80 myapp", "Run container with port mapping", "basics"),
            ("docker-compose up -d", "Start multi-container app", "intermediate"),
            ("docker exec -it container bash", "Shell into running container", "basics"),
            ("docker volume create mydata", "Create persistent storage", "intermediate"),
        ],
    },
    "linux": {
        "info": {"name": "Linux/Bash", "type": "Operating System"},
        "commands": [
            ("ls -la", "List all files with details", "basics"),
            ("grep -r 'pattern' /path", "Search files recursively", "basics"),
            ("find / -name '*.py' -type f", "Find files by name", "basics"),
            ("chmod 755 script.sh", "Set file permissions", "intermediate"),
            ("ps aux | grep python", "Find running processes", "intermediate"),
            ("ssh user@host", "Remote connection", "networking"),
            ("curl -X POST url -d 'data'", "HTTP requests", "networking"),
            ("awk '{print $1}' file.txt", "Text processing", "advanced"),
        ],
    },
}


class WorldTeacher:
    """
    Comprehensive world languages + programming teacher.
    Tracks vocabulary progress per language, generates quizzes, provides grammar help.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            try:
                from config.settings import config
                data_dir = Path(config.BASE_DIR) / "data" / "user_profile"
            except Exception:
                data_dir = Path("data/user_profile")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.data_dir / "language_progress.json"

        self.lang_vocab = LANGUAGE_VOCAB
        self.prog_langs = PROGRAMMING_LANGS
        self.dev_tools = DEV_TOOLS

        # Per-language progress: {lang: {word: LangWord}}
        self.progress: Dict[str, Dict[str, dict]] = {}
        self.quiz_history: List[LangQuizResult] = []
        self._load_progress()

        total_human = len(self.lang_vocab)
        total_prog = len(self.prog_langs)
        total_tools = len(self.dev_tools)
        logger.info(f"[WORLD_TEACHER] Initialized: {total_human} human languages, "
                     f"{total_prog} programming languages, {total_tools} dev tools")

    def _load_progress(self):
        if self.progress_file.exists():
            try:
                with open(str(self.progress_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.progress = data.get("progress", {})
                for qr in data.get("quiz_history", []):
                    self.quiz_history.append(LangQuizResult(**qr))
            except Exception as e:
                logger.debug(f"[WORLD_TEACHER] Could not load progress: {e}")

    def save_progress(self):
        try:
            data = {
                "progress": self.progress,
                "quiz_history": [asdict(q) for q in self.quiz_history[-200:]],
            }
            with open(str(self.progress_file), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WORLD_TEACHER] Save error: {e}")

    # ---- Language listing ----

    def list_human_languages(self) -> List[str]:
        return sorted(self.lang_vocab.keys())

    def list_programming_languages(self) -> List[str]:
        return sorted(self.prog_langs.keys())

    def list_dev_tools(self) -> List[str]:
        return sorted(self.dev_tools.keys())

    def list_all_subjects(self) -> Dict[str, List[str]]:
        return {
            "human_languages": self.list_human_languages(),
            "programming": self.list_programming_languages(),
            "dev_tools": self.list_dev_tools(),
        }

    # ---- Vocabulary & Lessons ----

    def get_lesson(self, language: str, category: str = "greetings") -> List[Dict]:
        """Get vocabulary lesson for a language."""
        lang = language.lower().replace(" ", "_")

        # Human language
        if lang in self.lang_vocab:
            data = self.lang_vocab[lang]
            words = data.get(category, data.get("greetings", []))
            return [{"word": w[0], "translation": w[1], "example": w[2],
                      "pronunciation": w[3] if len(w) > 3 else ""} for w in words]

        # Programming language
        if lang in self.prog_langs:
            data = self.prog_langs[lang]
            concepts = data.get("concepts", [])
            filtered = [c for c in concepts if category == "all" or c[3] == category]
            if not filtered:
                filtered = concepts
            return [{"concept": c[0], "syntax": c[1], "explanation": c[2],
                      "category": c[3]} for c in filtered]

        return []

    def get_grammar(self, language: str) -> List[Dict]:
        """Get grammar rules for a language."""
        lang = language.lower().replace(" ", "_")
        if lang in self.lang_vocab:
            return self.lang_vocab[lang].get("grammar", [])
        return []

    def get_challenges(self, language: str) -> List[Dict]:
        """Get coding challenges for a programming language."""
        lang = language.lower().replace(" ", "_")
        if lang in self.prog_langs:
            return self.prog_langs[lang].get("challenges", [])
        return []

    def get_tool_commands(self, tool: str) -> List[Dict]:
        """Get commands for a dev tool."""
        t = tool.lower().replace(" ", "_")
        if t in self.dev_tools:
            cmds = self.dev_tools[t].get("commands", [])
            return [{"command": c[0], "description": c[1], "category": c[2]} for c in cmds]
        return []

    # ---- Quiz System ----

    def generate_quiz(self, language: str, num_questions: int = 5) -> List[Dict]:
        """Generate a quiz for any language (human or programming)."""
        lang = language.lower().replace(" ", "_")

        if lang in self.lang_vocab:
            return self._human_lang_quiz(lang, num_questions)
        elif lang in self.prog_langs:
            return self._prog_lang_quiz(lang, num_questions)
        return []

    def _human_lang_quiz(self, lang: str, n: int) -> List[Dict]:
        data = self.lang_vocab[lang]
        all_words = []
        for cat_key, cat_val in data.items():
            if cat_key in ("info", "grammar"):
                continue
            for w in cat_val:
                all_words.append(w)

        random.shuffle(all_words)
        questions = []
        for w in all_words[:n]:
            # Translation quiz
            correct = w[1]
            distractors = []
            for other in all_words:
                if other[1] != correct:
                    distractors.append(other[1])
            random.shuffle(distractors)
            options = [correct] + distractors[:3]
            random.shuffle(options)

            questions.append({
                "type": "translation",
                "language": lang,
                "question": f"What does '{w[0]}' mean?",
                "word": w[0],
                "correct_answer": correct,
                "options": options,
                "correct_index": options.index(correct),
                "pronunciation": w[3] if len(w) > 3 else "",
            })
        return questions

    def _prog_lang_quiz(self, lang: str, n: int) -> List[Dict]:
        data = self.prog_langs[lang]
        concepts = list(data.get("concepts", []))
        random.shuffle(concepts)
        questions = []
        for c in concepts[:n]:
            correct = c[2]  # explanation
            distractors = [other[2] for other in concepts if other[0] != c[0]]
            random.shuffle(distractors)
            options = [correct] + distractors[:3]
            random.shuffle(options)

            questions.append({
                "type": "concept",
                "language": lang,
                "question": f"What does '{c[0]}' do in {lang}? (Syntax: {c[1]})",
                "word": c[0],
                "correct_answer": correct,
                "options": options,
                "correct_index": options.index(correct),
            })
        return questions

    def score_quiz(self, questions: List[Dict], answers: List[str]) -> LangQuizResult:
        """Score a quiz and track progress."""
        correct = 0
        lang = questions[0]["language"] if questions else "unknown"

        for q, a in zip(questions, answers):
            word = q["word"]
            is_correct = a.strip().lower() == q["correct_answer"].strip().lower()

            # Track per-word progress
            if lang not in self.progress:
                self.progress[lang] = {}
            if word not in self.progress[lang]:
                self.progress[lang][word] = {"correct": 0, "wrong": 0, "last_seen": 0}

            self.progress[lang][word]["last_seen"] = time.time()
            if is_correct:
                correct += 1
                self.progress[lang][word]["correct"] += 1
            else:
                self.progress[lang][word]["wrong"] += 1

        total = len(questions)
        score = (correct / total * 100) if total > 0 else 0
        result = LangQuizResult(language=lang, timestamp=time.time(),
                                 total=total, correct=correct, score_percent=score)
        self.quiz_history.append(result)
        self.save_progress()
        return result

    # ---- AI Prompt Context ----

    def get_teaching_context(self) -> str:
        """Get context string for AI system prompt."""
        parts = []
        parts.append(
            f"[WORLD TEACHER] You teach {len(self.lang_vocab)} human languages "
            f"(Spanish, French, Italian, Arabic, Mandarin, Russian, Haitian Creole, etc.) "
            f"and {len(self.prog_langs)} programming languages "
            f"(Python, JavaScript, C++, Java, Rust, Go, SQL, HTML/CSS).")

        # Show user's active languages
        if self.progress:
            active = list(self.progress.keys())[:5]
            parts.append(f"User is studying: {', '.join(active)}.")

        # Show struggling words
        for lang, words in list(self.progress.items())[:3]:
            struggling = [w for w, d in words.items()
                          if d.get("wrong", 0) > d.get("correct", 0)]
            if struggling:
                parts.append(f"Struggling in {lang}: {', '.join(struggling[:5])}")

        parts.append("Help the user learn languages and programming. "
                      "Quiz them, correct mistakes, teach grammar, and encourage practice.")
        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        stats = {"languages_studied": len(self.progress), "total_quizzes": len(self.quiz_history)}
        for lang, words in self.progress.items():
            total_c = sum(d.get("correct", 0) for d in words.values())
            total_w = sum(d.get("wrong", 0) for d in words.values())
            stats[lang] = {"words_tracked": len(words), "correct": total_c, "wrong": total_w}
        return stats


# Singleton
_world_teacher = None

def get_world_teacher() -> WorldTeacher:
    global _world_teacher
    if _world_teacher is None:
        _world_teacher = WorldTeacher()
    return _world_teacher
