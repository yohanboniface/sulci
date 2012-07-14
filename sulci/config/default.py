SULCI_CONTENT_PROPERTY = "content"
SULCI_KEYWORDS_PROPERTY = "keywords"
DEBUG = False
DATABASES = {
    "liberation": {
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "lemondediplo": {
        "host": "localhost",
        "port": 6379,
        "db": 1
    }
}
DEFAULT_DATABASE = "lemondediplo"