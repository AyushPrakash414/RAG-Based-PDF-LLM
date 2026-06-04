"""
Spell correction service for typo-tolerant retrieval.

Uses a dictionary-based approach with RapidFuzz for fast fuzzy matching.
No C++ build tools required — pure Python + pre-compiled RapidFuzz wheels.
"""

import logging
import re
from typing import Optional

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# Technology and common terms dictionary
# These terms are used for fuzzy matching when users make typos
_DICTIONARY: set[str] = {
    # Programming languages & frameworks
    "spring", "boot", "spring boot", "springboot", "java", "javascript",
    "typescript", "python", "react", "angular", "vue", "nodejs", "node",
    "fastapi", "flask", "django", "express", "next", "nuxt", "svelte",
    "rust", "golang", "go", "scala", "kotlin", "swift", "ruby", "rails",
    "php", "laravel", "perl", "haskell", "elixir", "clojure", "dart",
    "flutter",

    # Databases
    "mongodb", "mongo", "postgresql", "postgres", "mysql", "sqlite",
    "redis", "elasticsearch", "cassandra", "dynamodb", "couchdb",
    "mariadb", "oracle", "mssql", "neo4j", "influxdb", "clickhouse",

    # Cloud & DevOps
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform",
    "ansible", "jenkins", "github", "gitlab", "bitbucket", "cicd",
    "devops", "serverless", "lambda", "heroku", "vercel", "netlify",

    # AI/ML
    "artificial", "intelligence", "artificial intelligence",
    "machine", "learning", "machine learning", "deep learning",
    "neural", "network", "neural network", "transformer", "transformers",
    "tensorflow", "pytorch", "keras", "scikit", "sklearn",
    "natural", "language", "processing", "nlp", "llm",
    "embedding", "embeddings", "vector", "rag", "retrieval",
    "classification", "regression", "clustering", "segmentation",
    "reinforcement", "supervised", "unsupervised", "generative",
    "discriminative", "convolutional", "recurrent", "attention",

    # Architecture & Patterns
    "microservice", "microservices", "monolith", "api", "rest", "restful",
    "graphql", "grpc", "websocket", "webhook", "oauth", "jwt",
    "authentication", "authorization", "middleware", "gateway",
    "loadbalancer", "load balancer", "proxy", "reverse proxy",
    "caching", "cache", "queue", "message queue", "event",
    "pub/sub", "pubsub", "kafka", "rabbitmq", "sqs",

    # Networking & Infrastructure
    "http", "https", "tcp", "udp", "dns", "cdn", "ssl", "tls",
    "nginx", "apache", "linux", "windows", "macos", "ubuntu",
    "container", "containerization", "orchestration", "helm",
    "prometheus", "grafana", "elk", "kibana", "logstash",

    # Data concepts
    "database", "schema", "index", "indexing", "query", "sql", "nosql",
    "sharding", "replication", "partitioning", "normalization",
    "denormalization", "transaction", "acid", "base", "cap",
    "serialization", "deserialization", "json", "xml", "yaml",
    "csv", "protobuf", "avro", "parquet",

    # Software engineering
    "algorithm", "data structure", "array", "linked list", "tree",
    "graph", "hash", "hashmap", "hashtable", "stack", "queue",
    "heap", "binary", "search", "sort", "recursion", "iteration",
    "concurrency", "parallelism", "thread", "threading", "async",
    "asynchronous", "synchronous", "mutex", "semaphore", "deadlock",
    "race condition", "design pattern", "singleton", "factory",
    "observer", "strategy", "decorator", "adapter", "facade",
    "mvc", "mvvm", "repository", "dependency injection",

    # Build tools
    "maven", "gradle", "webpack", "vite", "npm", "yarn", "pip",
    "conda", "poetry", "cargo", "cmake", "make", "bazel",

    # Version control
    "git", "github", "gitlab", "bitbucket", "merge", "branch",
    "commit", "pull request", "code review", "ci/cd",

    # Security
    "encryption", "hashing", "bcrypt", "sha", "md5", "rsa",
    "aes", "hmac", "certificate", "firewall", "vulnerability",
    "injection", "xss", "csrf", "cors",

    # General computing
    "computer", "software", "hardware", "memory", "cpu", "gpu",
    "storage", "network", "internet", "protocol", "interface",
    "framework", "library", "package", "module", "function",
    "class", "object", "variable", "constant", "parameter",
    "argument", "return", "exception", "error", "debug",
    "testing", "unit test", "integration test", "deployment",
    "production", "staging", "development", "environment",
    "configuration", "documentation", "performance", "optimization",
    "scalability", "reliability", "availability", "monitoring",
    "logging", "tracing", "observability", "metric", "alert",
}

# Word-level dictionary for individual word correction
_WORD_DICT: set[str] = set()
for term in _DICTIONARY:
    for word in term.split():
        _WORD_DICT.add(word.lower())


class SpellCorrector:
    """
    Typo-tolerant spell correction for search queries.

    Uses RapidFuzz for fast fuzzy string matching against
    a curated dictionary of technology and common terms.
    """

    def __init__(self, max_edit_distance: int = 2, min_score: int = 70) -> None:
        """
        Initialise the spell corrector.

        Args:
            max_edit_distance: Maximum edit distance for corrections
                              (used for filtering, not direct computation).
            min_score: Minimum RapidFuzz score (0-100) for a match.
        """
        self._max_edit_distance = max_edit_distance
        self._min_score = min_score
        self._word_list = list(_WORD_DICT)
        self._phrase_list = list(_DICTIONARY)

        logger.info(
            "SpellCorrector initialised: %d phrases, %d words, min_score=%d",
            len(self._phrase_list),
            len(self._word_list),
            min_score,
        )

    def correct_query(self, query: str) -> str:
        """
        Correct a search query for typos.

        Strategy:
        1. Try phrase-level matching first (for multi-word terms)
        2. Fall back to word-by-word correction

        Args:
            query: The raw user query (potentially with typos).

        Returns:
            The corrected query string.
        """
        if not query or not query.strip():
            return query

        original = query.strip()
        lower_query = original.lower()

        # Step 1: Check if the entire query matches a known phrase
        phrase_match = process.extractOne(
            lower_query,
            self._phrase_list,
            scorer=fuzz.ratio,
            score_cutoff=self._min_score,
        )
        if phrase_match and phrase_match[1] >= 85:
            # High confidence phrase match — use it directly
            corrected = phrase_match[0]
            if corrected != lower_query:
                logger.info(
                    "Phrase-level correction: '%s' → '%s' (score=%d)",
                    query, corrected, phrase_match[1],
                )
                return corrected

        # Step 2: Word-by-word correction
        words = lower_query.split()
        corrected_words = []
        changed = False

        for word in words:
            # Skip very short words (articles, prepositions)
            if len(word) <= 2:
                corrected_words.append(word)
                continue

            # Check if word is already in dictionary
            if word in _WORD_DICT:
                corrected_words.append(word)
                continue

            # Try fuzzy match
            match = process.extractOne(
                word,
                self._word_list,
                scorer=fuzz.ratio,
                score_cutoff=self._min_score,
            )

            if match:
                corrected_words.append(match[0])
                if match[0] != word:
                    changed = True
                    logger.debug(
                        "Word correction: '%s' → '%s' (score=%d)",
                        word, match[0], match[1],
                    )
            else:
                # No match found — keep original
                corrected_words.append(word)

        result = " ".join(corrected_words)

        if changed:
            logger.info(
                "Query spell-corrected: '%s' → '%s'",
                query, result,
            )

        return result

    def get_corrections(self, word: str, max_results: int = 5) -> list[str]:
        """
        Get correction candidates for a single word.

        Args:
            word: The word to find corrections for.
            max_results: Maximum number of suggestions.

        Returns:
            List of correction suggestions with scores.
        """
        matches = process.extract(
            word.lower(),
            self._word_list,
            scorer=fuzz.ratio,
            limit=max_results,
            score_cutoff=self._min_score,
        )
        return [m[0] for m in matches]
