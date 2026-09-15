import re
from typing import Dict
import html2text

def clean_text_content(text: str) -> str:
    """Removes excessive spaces, line breaks, and residual boilerplate code."""
    # Collapse multiple blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Strip spaces per line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = '\n'.join(lines)
    return cleaned

def convert_scraped_data_to_markdown(scraped_pages: Dict[str, str], max_char_limit: int = 20000) -> str:
    """
    Consolidates text/HTML scraped from multiple pages into structured, token-optimized Markdown.
    """
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = False
    h.body_width = 0

    markdown_sections = []

    for path, content in scraped_pages.items():
        if content.startswith("<") and ">" in content:
            # It's raw HTML, convert to markdown
            converted = h.handle(content)
        else:
            # It's already extracted DOM text
            converted = content

        cleaned = clean_text_content(converted)
        section = f"### Page Content: {path}\n{cleaned}\n"
        markdown_sections.append(section)

    combined_markdown = "\n---\n".join(markdown_sections)
    
    # Truncate if exceeding max character limit
    if len(combined_markdown) > max_char_limit:
        combined_markdown = combined_markdown[:max_char_limit] + "\n\n...[Content truncated for token optimization]"

    return combined_markdown
