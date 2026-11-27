"""Small, offline tools for the book reading planner."""

import csv
from pathlib import Path

from langchain_core.tools import tool

DATA_FILE = Path(__file__).parent / "data" / "books.csv"
MAX_CHARS = 600


def clip(text: str, limit: int = MAX_CHARS) -> str:
    """Keep tool results short enough to inspect easily."""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + " ...(cut)"


def _read_catalog() -> tuple[list[dict[str, str]] | None, str | None]:
    try:
        with DATA_FILE.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not {"title", "genre", "pages"}.issubset(reader.fieldnames):
                return None, "The catalog is missing a required column (title, genre, pages)."
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        return None, f"The catalog could not be read ({type(error).__name__}). Check data/books.csv."

    for row in rows:
        if not all(row.get(column, "").strip() for column in ("title", "genre", "pages")):
            return None, "The catalog contains a row with an empty title, genre, or page count."
        try:
            pages = int(row["pages"])
        except ValueError:
            return None, "The catalog contains a page count that is not a whole number."
        if pages <= 0:
            return None, "The catalog contains a page count that is not positive."
    return rows, None


def _pages_per_day(value: str) -> int | None:
    try:
        pages = int(value)
    except (TypeError, ValueError):
        return None
    return pages if pages > 0 else None


def _find_title(rows: list[dict[str, str]], title: str) -> dict[str, str] | None:
    wanted = title.strip().casefold()
    if not wanted:
        return None
    return next((row for row in rows if row["title"].strip().casefold() == wanted), None)


@tool
def find_books(genre: str) -> str:
    """List up to five books in a genre. Use it when the user asks to browse the catalog by genre."""
    wanted = genre.strip().casefold()
    if not wanted:
        return "Please provide a genre to search for."
    rows, error = _read_catalog()
    if error:
        return error
    matches = [row for row in rows if row["genre"].strip().casefold() == wanted]
    if not matches:
        return clip(f"No books were found for the genre '{genre.strip()}'.")
    result = "\n".join(f"- {row['title']} ({row['pages']} pages)" for row in matches[:5])
    return clip(result)


@tool
def reading_days(title: str, pages_per_day: str) -> str:
    """Estimate whole reading days for a catalog book at a daily page pace. Use it for reading-time calculations."""
    pace = _pages_per_day(pages_per_day)
    if pace is None:
        return "Please give a positive whole number of pages per day."
    if not title.strip():
        return "Please provide a book title."
    rows, error = _read_catalog()
    if error:
        return error
    book = _find_title(rows, title)
    if book is None:
        return clip(f"No catalog book was found with the title '{title.strip()}'.")
    days = (int(book["pages"]) + pace - 1) // pace
    return clip(f"{book['title']}: about {days} days at {pace} pages per day.")


@tool
def draft_reading_plan(title: str, pages_per_day: str) -> str:
    """Draft a simple reading plan for a catalog book. Use it when the user asks for a plan; it does not schedule or save anything."""
    pace = _pages_per_day(pages_per_day)
    if pace is None:
        return "Please give a positive whole number of pages per day."
    if not title.strip():
        return "Please provide a book title."
    rows, error = _read_catalog()
    if error:
        return error
    book = _find_title(rows, title)
    if book is None:
        return clip(f"No catalog book was found with the title '{title.strip()}'.")
    days = (int(book["pages"]) + pace - 1) // pace
    return clip(
        f"Draft: Read about {pace} pages of '{book['title']}' each day for {days} days. "
        "Adjust the pace to suit your schedule. This is only a suggestion; nothing has been scheduled."
    )


TOOLS = [find_books, reading_days, draft_reading_plan]
