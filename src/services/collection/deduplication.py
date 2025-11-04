"""Content deduplication using Simhash algorithm."""

import re
import hashlib
from typing import Set, List


class ContentDeduplicator:
    """Advanced content deduplication using Simhash algorithm.

    Simhash provides fuzzy matching for near-duplicate detection,
    significantly more accurate than simple URL/title hashing.
    """

    def __init__(self, hash_bits: int = 64, hamming_threshold: int = 3):
        """Initialize deduplicator.

        Args:
            hash_bits: Number of bits in simhash (default 64)
            hamming_threshold: Maximum Hamming distance for duplicates (default 3)
        """
        self.hash_bits = hash_bits
        self.hamming_threshold = hamming_threshold

    def compute_simhash(self, text: str) -> int:
        """Compute Simhash fingerprint for text content.

        Algorithm:
        1. Tokenize text into features
        2. Hash each feature to hash_bits
        3. Weight each bit by feature frequency
        4. Generate final fingerprint by bit voting

        Args:
            text: Input text content

        Returns:
            Integer simhash fingerprint
        """
        if not text:
            return 0

        # Tokenize and normalize text
        tokens = self._tokenize(text)

        # Initialize bit vector for weighted voting
        v = [0] * self.hash_bits

        # Process each token
        for token in tokens:
            # Hash token to get bit pattern
            token_hash = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)

            # Weight each bit (+1 if bit is 1, -1 if bit is 0)
            for i in range(self.hash_bits):
                bit_mask = 1 << i
                if token_hash & bit_mask:
                    v[i] += 1
                else:
                    v[i] -= 1

        # Generate final fingerprint by majority voting
        fingerprint = 0
        for i in range(self.hash_bits):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return fingerprint

    def compute_url_title_hash(self, title: str, url: str) -> str:
        """Compute traditional hash for URL and title.

        This provides a fast first-pass filter before Simhash comparison.

        Args:
            title: Article title
            url: Article URL

        Returns:
            SHA256 hash string
        """
        # Normalize URL by removing query parameters and fragments
        normalized_url = self._normalize_url(url)

        # Normalize title by lowercasing and removing punctuation
        normalized_title = re.sub(r'[^\w\s]', '', title.lower()).strip()

        # Combine and hash
        combined = f"{normalized_title}|{normalized_url}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """Calculate Hamming distance between two hashes.

        Hamming distance = number of differing bits

        Args:
            hash1: First simhash
            hash2: Second simhash

        Returns:
            Number of different bits (0-64)
        """
        xor = hash1 ^ hash2
        distance = 0
        while xor:
            distance += 1
            xor &= xor - 1  # Remove rightmost set bit
        return distance

    def is_duplicate(self, hash1: int, hash2: int) -> bool:
        """Check if two simhashes represent duplicate content.

        Args:
            hash1: First simhash
            hash2: Second simhash

        Returns:
            True if Hamming distance <= threshold
        """
        return self.hamming_distance(hash1, hash2) <= self.hamming_threshold

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into features for simhash.

        Uses word-level tokenization with normalization:
        - Lowercase conversion
        - Remove punctuation
        - Filter short tokens (< 3 chars)
        - Remove stopwords

        Args:
            text: Input text

        Returns:
            List of normalized tokens
        """
        # Lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        # Filter short words and common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}

        tokens = [w for w in words if len(w) >= 3 and w not in stopwords]

        return tokens

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing variable components.

        Removes:
        - Query parameters (everything after '?')
        - Fragments (everything after '#')
        - Trailing slashes
        - Common tracking parameters

        Args:
            url: Input URL

        Returns:
            Normalized URL string
        """
        # Remove query parameters and fragments
        url = re.sub(r'[?#].*$', '', url)

        # Remove trailing slash
        url = url.rstrip('/')

        # Lowercase for consistency
        url = url.lower()

        return url
