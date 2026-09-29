from __future__ import annotations

import re
from pathlib import Path
from ebooklib import epub
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
MANUSCRITO = ROOT / "manuscrito"
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

TITLE = "Mandaçaia — Melipona quadrifasciata"
AUTHOR = "Abel Barros de Carvalho"
LANG = "pt-BR"

# Marcadores internos de pesquisa/ChatGPT nunca podem chegar ao e-book.
TECHNICAL_MARKERS = [
    re.compile(r"[^]*", re.DOTALL),
    re.compile(r"turn\d+(?:search|news|image|youtube|product|business|fetch|view|file)\d+", re.IGNORECASE),
    re.compile(r"(?:cite|url|entity|image_group|video|navlist)\s*[□\u25a1]\s*", re.IGNORECASE),
    re.compile(r"[□\u25a1]\s*(?:cite|url|entity|image_group|video|navlist)\s*[□\u25a1]", re.IGNORECASE),
]


def chapter_key(path: Path):
    # Aceita nomes como 01-, 06-, 06a- e 06b-.
    m = re.match(r"(\d+)([a-z]?)-", path.name, re.IGNORECASE)
    if not m:
        return (9999, 999, path.name.lower())
    suffix = m.group(2).lower()
    suffix_order = (ord(suffix) - ord("a") + 1) if suffix else 0
    return (int(m.group(1)), suffix_order, path.name.lower())


def clean_markdown(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2].lstrip()

    for pattern in TECHNICAL_MARKERS:
        text = pattern.sub("", text)

    text = re.sub(r"□cite□[^\n]*□", "", text, flags=re.IGNORECASE)
    text = re.sub(r"□(?:url|entity|image_group|video|navlist)□[^\n]*□", "", text, flags=re.IGNORECASE)

    return text


def make_id(path: Path) -> str:
    return "cap-" + path.stem


def render_chapter(path: Path):
    raw = clean_markdown(path.read_text(encoding="utf-8"))
    html = markdown.markdown(
        raw,
        extensions=["extra", "sane_lists", "smarty"]
    )
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    body = str(soup)
    first_h1 = soup.find("h1")
    title = first_h1.get_text(" ", strip=True) if first_h1 else path.stem
    return title, body


def validate_epub_html(chapters):
    forbidden = re.compile(r"(?:||turn\d+(?:search|news|image|youtube|product|business|fetch|view|file)\d+|□cite□|□url□|□entity□)", re.IGNORECASE)
    errors = []
    for item in chapters:
        content = item.content.decode("utf-8", errors="replace") if isinstance(item.content, bytes) else str(item.content)
        if forbidden.search(content):
            errors.append(item.file_name)
    if errors:
        raise RuntimeError("Marcadores técnicos encontrados no EPUB: " + ", ".join(errors))


def main():
    files = sorted(MANUSCRITO.glob("*.md"), key=chapter_key)
    if not files:
        raise SystemExit("Nenhum capítulo Markdown encontrado em manuscrito/")

    book = epub.EpubBook()
    book.set_identifier("mandaçaia-melipona-quadrifasciata")
    book.set_title(TITLE)
    book.set_language(LANG)
    book.add_author(AUTHOR)
    book.add_metadata("DC", "description", "Obra de referência sobre a biologia, comportamento, organização social, ecologia e meliponicultura da mandaçaia (Melipona quadrifasciata).")

    css = epub.EpubItem(
        uid="style",
        file_name="styles/book.css",
        media_type="text/css",
        content="""
body { font-family: serif; line-height: 1.55; margin: 5%; }
h1 { page-break-before: always; margin-top: 0; }
h2, h3 { margin-top: 1.6em; }
p { text-align: justify; margin: 0 0 0.9em 0; }
a { text-decoration: none; }
blockquote { margin-left: 1.5em; margin-right: 1.5em; }
""".encode("utf-8")
    )
    book.add_item(css)

    chapters = []
    for path in files:
        title, body = render_chapter(path)
        item = epub.EpubHtml(
            title=title,
            file_name=f"text/{make_id(path)}.xhtml",
            lang=LANG,
        )
        item.content = f"<html><head><title>{title}</title></head><body>{body}</body></html>"
        item.add_item(css)
        book.add_item(item)
        chapters.append(item)

    validate_epub_html(chapters)

    book.toc = tuple(chapters)
    book.spine = ["nav", *chapters]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output = DIST / "mandaçaia-melipona-quadrifasciata.epub"
    epub.write_epub(str(output), book, {})
    print(f"EPUB criado: {output}")
    print(f"Capítulos incluídos: {len(chapters)}")
    print("Validação: nenhum marcador técnico encontrado no conteúdo EPUB.")


if __name__ == "__main__":
    main()
