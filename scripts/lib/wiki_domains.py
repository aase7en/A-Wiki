"""Shared wiki source-domain constants.

Single source of truth for VALID_DOMAINS + DOMAIN_TITLES used across the
wiki ingest pipeline. Previously duplicated inline in 4 files
(ingest-source.py, scrape-advanced.py, batch/prompt_template.py, gen-index.py).

Note: gen-index.py is intentionally NOT consolidated here because it uses
a structurally different set (DOMAIN_ORDER list, DOMAIN_FILE_SLUG dict,
and only 5 domains without "it"/"general"). See F8 commit message.

Imported via ``from lib.wiki_domains import VALID_DOMAINS, DOMAIN_TITLES``
after ``scripts/`` is on sys.path (conftest.py + each consumer inserts it).
"""

# Domains recognised by the wiki source-ingest pipeline.
# Adding a domain here automatically makes it usable in ingest-source.py,
# scrape-advanced.py, and batch/prompt_template.py.
VALID_DOMAINS: tuple[str, ...] = (
    "iot", "env", "ai-tools", "pharmacy", "it", "general", "trader",
)

# Display titles — used in source-entry rendering and overview generation.
DOMAIN_TITLES: dict[str, str] = {
    "iot": "IoT",
    "env": "Environmental Health",
    "ai-tools": "AI Tools",
    "pharmacy": "Pharmacy",
    "it": "IT",
    "general": "General",
    "trader": "Trading & Finance",
}
