"""
Application-wide constants.
"""

# Supported file types for upload
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx"}

# Default collection name in ChromaDB
DEFAULT_COLLECTION = "studypal_default"

# Text splitter defaults
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Retrieval
DEFAULT_TOP_K = 5

# LLM
DEFAULT_GROQ_MODEL = "llama3-8b-8192"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Summarization
SUMMARY_MAX_TOKENS = 2048

# YouTube
YOUTUBE_MAX_RESULTS = 3

# Chat
MAX_CHAT_HISTORY = 20
