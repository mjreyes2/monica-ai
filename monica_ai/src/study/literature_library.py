"""
Monica Literature Library
Access to 70,000+ free classical ebooks from Project Gutenberg via Gutendex API.
Includes literature, poetry, language arts, and creative writing.

Author: Monica AI
Date: December 2025
"""

import json
import time
import requests
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache

# Gutendex API - Free Project Gutenberg API
GUTENDEX_API = "https://gutendex.com"

# Categories of classical literature
LITERATURE_CATEGORIES = {
    'fiction': ['Fiction', 'Adventure', 'Science Fiction', 'Fantasy', 'Mystery', 'Horror'],
    'literature': ['Literature', 'Drama', 'Tragedy', 'Comedy'],
    'poetry': ['Poetry', 'Verse', 'Sonnets', 'Epic Poetry'],
    'language_arts': ['Essays', 'Letters', 'Speeches', 'Rhetoric'],
    'creative_writing': ['Short Stories', 'Novels', 'Plays', 'Satire'],
    'philosophy': ['Philosophy', 'Ethics', 'Logic'],
    'history': ['History', 'Biography', 'Autobiography'],
    'education': ['Education', 'Textbooks', 'Reference'],
}

# Famous authors for classical literature
CLASSICAL_AUTHORS = [
    'Shakespeare', 'Dickens', 'Austen', 'Twain', 'Poe', 'Shelley',
    'Bronte', 'Dostoevsky', 'Tolstoy', 'Homer', 'Dante', 'Milton',
    'Chaucer', 'Wordsworth', 'Keats', 'Byron', 'Whitman', 'Emerson',
    'Thoreau', 'Hawthorne', 'Melville', 'Wilde', 'Joyce', 'Woolf',
    'Hemingway', 'Fitzgerald', 'Orwell', 'Kafka', 'Chekhov', 'Ibsen',
    'Shaw', 'Yeats', 'Frost', 'Eliot', 'Plato', 'Aristotle',
    'Cervantes', 'Hugo', 'Dumas', 'Verne', 'Wells', 'Doyle',
    'Christie', 'Carroll', 'Stevenson', 'Kipling', 'Conrad', 'Hardy'
]


@dataclass
class Book:
    """Represents a book from Project Gutenberg."""
    id: int
    title: str
    authors: List[str]
    subjects: List[str]
    bookshelves: List[str]
    languages: List[str]
    download_count: int
    text_url: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict) -> 'Book':
        """Create Book from Gutendex API response."""
        authors = [a.get('name', 'Unknown') for a in data.get('authors', [])]
        
        # Get text URL
        formats = data.get('formats', {})
        text_url = formats.get('text/plain; charset=utf-8') or formats.get('text/plain')
        html_url = formats.get('text/html; charset=utf-8') or formats.get('text/html')
        
        return cls(
            id=data.get('id', 0),
            title=data.get('title', 'Unknown'),
            authors=authors,
            subjects=data.get('subjects', []),
            bookshelves=data.get('bookshelves', []),
            languages=data.get('languages', []),
            download_count=data.get('download_count', 0),
            text_url=text_url,
            html_url=html_url
        )


class LiteratureLibrary:
    """
    Access to Project Gutenberg's 70,000+ free ebooks.
    """
    
    def __init__(self, cache_dir: Path = None):
        self.api_base = GUTENDEX_API
        
        # Cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "literature"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Book cache
        self.book_cache: Dict[int, Book] = {}
        self.text_cache: Dict[int, str] = {}
        
        # Curated reading lists
        self.reading_lists = self._init_reading_lists()
        
        print(f"[LITERATURE] Library initialized with {len(self.reading_lists)} reading lists")
    
    def _init_reading_lists(self) -> Dict[str, List[int]]:
        """Initialize curated reading lists with Project Gutenberg IDs."""
        return {
            # Classic Literature (novels)
            'classic_novels': [
                1342,   # Pride and Prejudice - Jane Austen
                84,     # Frankenstein - Mary Shelley
                1661,   # Sherlock Holmes - Arthur Conan Doyle
                11,     # Alice in Wonderland - Lewis Carroll
                98,     # A Tale of Two Cities - Charles Dickens
                1232,   # The Prince - Machiavelli
                74,     # Tom Sawyer - Mark Twain
                76,     # Huckleberry Finn - Mark Twain
                2701,   # Moby Dick - Herman Melville
                345,    # Dracula - Bram Stoker
                1400,   # Great Expectations - Charles Dickens
                16,     # Peter Pan - J.M. Barrie
                174,    # Picture of Dorian Gray - Oscar Wilde
                1952,   # The Yellow Wallpaper - Charlotte Perkins Gilman
                5200,   # Metamorphosis - Franz Kafka
                64317,  # The Great Gatsby - F. Scott Fitzgerald
                2591,   # Grimm's Fairy Tales
                1260,   # Jane Eyre - Charlotte Bronte
                768,    # Wuthering Heights - Emily Bronte
                2554,   # Crime and Punishment - Dostoevsky
            ],
            
            # Poetry Collections
            'poetry': [
                1041,   # Shakespeare's Sonnets
                1321,   # Paradise Lost - John Milton
                8800,   # Divine Comedy - Dante
                6130,   # The Iliad - Homer
                1727,   # The Odyssey - Homer
                4300,   # Ulysses - James Joyce
                996,    # Don Quixote - Cervantes
                2600,   # War and Peace - Tolstoy
                28054,  # The Brothers Karamazov - Dostoevsky
                135,    # Les Miserables - Victor Hugo
                1184,   # Count of Monte Cristo - Alexandre Dumas
                244,    # A Study in Scarlet - Doyle
                2852,   # The Hound of the Baskervilles - Doyle
                35,     # The Time Machine - H.G. Wells
                36,     # The War of the Worlds - H.G. Wells
                43,     # The Strange Case of Dr Jekyll and Mr Hyde
                219,    # Heart of Darkness - Joseph Conrad
                120,    # Treasure Island - Robert Louis Stevenson
                45,     # Anne of Green Gables - L.M. Montgomery
                1080,   # A Modest Proposal - Jonathan Swift
            ],
            
            # Short Stories
            'short_stories': [
                2148,   # The Works of Edgar Allan Poe
                1064,   # The Masque of the Red Death - Poe
                932,    # The Fall of the House of Usher - Poe
                2147,   # The Raven - Poe
                209,    # The Turn of the Screw - Henry James
                514,    # Little Women - Louisa May Alcott
                161,    # Sense and Sensibility - Jane Austen
                105,    # Persuasion - Jane Austen
                158,    # Emma - Jane Austen
                141,    # Mansfield Park - Jane Austen
                121,    # Northanger Abbey - Jane Austen
                1399,   # Anna Karenina - Leo Tolstoy
                600,    # Notes from Underground - Dostoevsky
                28,     # The Republic - Plato
                1497,   # The Meditations - Marcus Aurelius
                5827,   # The Problems of Philosophy - Bertrand Russell
                815,    # Democracy in America - Alexis de Tocqueville
                7370,   # Second Treatise of Government - John Locke
                3207,   # Leviathan - Thomas Hobbes
                4363,   # Beyond Good and Evil - Nietzsche
            ],
            
            # Essays and Non-Fiction
            'essays': [
                205,    # Walden - Henry David Thoreau
                1571,   # The Autobiography of Benjamin Franklin
                3600,   # Essays - Ralph Waldo Emerson
                7849,   # On Liberty - John Stuart Mill
                4705,   # A Vindication of the Rights of Woman - Wollstonecraft
                852,    # The Art of War - Sun Tzu
                1250,   # Anthem - Ayn Rand
                30254,  # The Communist Manifesto - Marx & Engels
                46,     # A Christmas Carol - Charles Dickens
                766,    # David Copperfield - Charles Dickens
                730,    # Oliver Twist - Charles Dickens
                580,    # The Pickwick Papers - Charles Dickens
                967,    # Bleak House - Charles Dickens
                1023,   # Hard Times - Charles Dickens
                883,    # Dombey and Son - Charles Dickens
                821,    # Dombey and Son - Charles Dickens
                564,    # The Old Curiosity Shop - Charles Dickens
                917,    # The Mystery of Edwin Drood - Charles Dickens
                700,    # Nicholas Nickleby - Charles Dickens
                653,    # Martin Chuzzlewit - Charles Dickens
            ],
            
            # Drama and Plays
            'drama': [
                1524,   # Hamlet - Shakespeare
                1533,   # Macbeth - Shakespeare
                1531,   # Romeo and Juliet - Shakespeare
                1519,   # A Midsummer Night's Dream - Shakespeare
                1526,   # Othello - Shakespeare
                1532,   # King Lear - Shakespeare
                1522,   # Julius Caesar - Shakespeare
                1539,   # The Tempest - Shakespeare
                1517,   # The Merchant of Venice - Shakespeare
                1520,   # Much Ado About Nothing - Shakespeare
                1529,   # Twelfth Night - Shakespeare
                1515,   # The Taming of the Shrew - Shakespeare
                1534,   # Richard III - Shakespeare
                1536,   # Henry V - Shakespeare
                1537,   # As You Like It - Shakespeare
                1514,   # The Comedy of Errors - Shakespeare
                1528,   # The Winter's Tale - Shakespeare
                1527,   # Antony and Cleopatra - Shakespeare
                1521,   # The Merry Wives of Windsor - Shakespeare
                2267,   # A Doll's House - Henrik Ibsen
            ],
            
            # Language Arts and Rhetoric
            'language_arts': [
                18269,  # The Elements of Style - Strunk
                37134,  # The King's English - Fowler
                22153,  # English Grammar - Murray
                15474,  # Practical English Grammar
                37090,  # A Handbook of the English Language
                36068,  # English Synonyms and Antonyms
                29765,  # Punctuation - A Primer
                21765,  # How to Speak and Write Correctly
                16317,  # The Art of Public Speaking
                39452,  # The Art of Writing & Speaking English
                36979,  # English Composition and Rhetoric
                37363,  # A Manual of the Art of Fiction
                35711,  # The Craft of Fiction
                37519,  # Practical Argumentation
                36098,  # The Principles of English Versification
                37725,  # English Verse
                38070,  # A Study of Poetry
                37516,  # The Technique of the Novel
                37134,  # The King's English
                39215,  # Composition-Rhetoric
            ],
        }
    
    def search_books(self, query: str, topic: str = None, language: str = 'en', 
                     max_results: int = 32) -> List[Book]:
        """
        Search for books in Project Gutenberg.
        
        Args:
            query: Search term (author name or title)
            topic: Optional topic filter
            language: Language code (default: English)
            max_results: Maximum number of results
        """
        params = {
            'search': query,
            'languages': language,
        }
        
        if topic:
            params['topic'] = topic
        
        try:
            response = requests.get(f"{self.api_base}/books", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get('results', [])[:max_results]:
                book = Book.from_api(item)
                self.book_cache[book.id] = book
                books.append(book)
            
            return books
        except Exception as e:
            print(f"[LITERATURE] Search error: {e}")
            return []
    
    def get_book(self, book_id: int) -> Optional[Book]:
        """Get a specific book by ID."""
        if book_id in self.book_cache:
            return self.book_cache[book_id]
        
        try:
            response = requests.get(f"{self.api_base}/books/{book_id}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            book = Book.from_api(data)
            self.book_cache[book_id] = book
            return book
        except Exception as e:
            print(f"[LITERATURE] Get book error: {e}")
            return None
    
    def get_book_text(self, book_id: int, max_chars: int = 50000) -> Optional[str]:
        """
        Get the full text of a book.
        
        Args:
            book_id: Project Gutenberg book ID
            max_chars: Maximum characters to return (for memory efficiency)
        """
        # Check cache
        if book_id in self.text_cache:
            return self.text_cache[book_id][:max_chars]
        
        # Check local file cache
        cache_file = self.cache_dir / f"{book_id}.txt"
        if cache_file.exists():
            text = cache_file.read_text(encoding='utf-8', errors='ignore')
            self.text_cache[book_id] = text
            return text[:max_chars]
        
        # Get book info
        book = self.get_book(book_id)
        if not book or not book.text_url:
            return None
        
        try:
            response = requests.get(book.text_url, timeout=30)
            response.raise_for_status()
            text = response.text
            
            # Cache locally
            cache_file.write_text(text, encoding='utf-8')
            self.text_cache[book_id] = text
            
            return text[:max_chars]
        except Exception as e:
            print(f"[LITERATURE] Get text error: {e}")
            return None
    
    def get_reading_list(self, category: str) -> List[Book]:
        """Get books from a curated reading list."""
        if category not in self.reading_lists:
            return []
        
        books = []
        for book_id in self.reading_lists[category]:
            book = self.get_book(book_id)
            if book:
                books.append(book)
        
        return books
    
    def get_random_passage(self, category: str = 'classic_novels', 
                          min_length: int = 200, max_length: int = 500) -> Dict[str, str]:
        """
        Get a random passage for reading practice.
        
        Returns:
            Dict with 'book', 'author', 'passage'
        """
        import random
        
        if category not in self.reading_lists:
            category = 'classic_novels'
        
        book_ids = self.reading_lists[category]
        random.shuffle(book_ids)
        
        for book_id in book_ids[:5]:  # Try up to 5 books
            text = self.get_book_text(book_id)
            if not text:
                continue
            
            book = self.get_book(book_id)
            if not book:
                continue
            
            # Find a good passage (paragraph)
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) >= min_length]
            
            if paragraphs:
                # Filter to reasonable length
                good_paragraphs = [p for p in paragraphs if min_length <= len(p) <= max_length * 2]
                
                if good_paragraphs:
                    passage = random.choice(good_paragraphs)
                    # Trim to max length at sentence boundary
                    if len(passage) > max_length:
                        sentences = passage.split('. ')
                        trimmed = ""
                        for s in sentences:
                            if len(trimmed) + len(s) < max_length:
                                trimmed += s + ". "
                            else:
                                break
                        passage = trimmed.strip()
                    
                    return {
                        'book': book.title,
                        'author': ', '.join(book.authors),
                        'passage': passage
                    }
        
        return {
            'book': 'Unknown',
            'author': 'Unknown',
            'passage': 'Could not find a suitable passage. Please try again.'
        }
    
    def get_vocabulary_from_book(self, book_id: int, difficulty: str = 'medium') -> List[Dict]:
        """
        Extract vocabulary words from a book for study.
        
        Args:
            book_id: Book ID
            difficulty: 'easy', 'medium', or 'hard'
        """
        text = self.get_book_text(book_id, max_chars=100000)
        if not text:
            return []
        
        import re
        from collections import Counter
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_counts = Counter(words)
        
        # Filter by difficulty (word length and frequency)
        if difficulty == 'easy':
            min_len, max_len = 4, 7
            min_freq = 5
        elif difficulty == 'hard':
            min_len, max_len = 9, 20
            min_freq = 1
        else:  # medium
            min_len, max_len = 6, 12
            min_freq = 2
        
        vocab = []
        for word, count in word_counts.most_common(500):
            if min_len <= len(word) <= max_len and count >= min_freq:
                vocab.append({
                    'word': word,
                    'frequency': count,
                    'length': len(word)
                })
                if len(vocab) >= 50:
                    break
        
        return vocab
    
    def get_all_categories(self) -> List[str]:
        """Get all available reading list categories."""
        return list(self.reading_lists.keys())
    
    def get_category_count(self, category: str) -> int:
        """Get number of books in a category."""
        return len(self.reading_lists.get(category, []))
    
    def get_total_books(self) -> int:
        """Get total number of curated books."""
        return sum(len(books) for books in self.reading_lists.values())


# Singleton instance
_library = None

def get_literature_library() -> LiteratureLibrary:
    """Get or create the literature library singleton."""
    global _library
    if _library is None:
        _library = LiteratureLibrary()
    return _library


# Test
if __name__ == "__main__":
    print("Testing Literature Library...")
    
    library = get_literature_library()
    
    print(f"\nTotal curated books: {library.get_total_books()}")
    print(f"Categories: {library.get_all_categories()}")
    
    # Test search
    print("\nSearching for Shakespeare...")
    books = library.search_books("Shakespeare", max_results=5)
    for book in books:
        print(f"  - {book.title} by {', '.join(book.authors)}")
    
    # Test random passage
    print("\nGetting random passage...")
    passage = library.get_random_passage('classic_novels')
    print(f"From: {passage['book']} by {passage['author']}")
    print(f"Passage: {passage['passage'][:200]}...")
    
    print("\nLiterature Library ready!")
