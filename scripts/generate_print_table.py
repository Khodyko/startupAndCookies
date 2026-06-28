#!/usr/bin/env python3
"""Генерация сводной таблицы карт для печати из markdown-источников."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CANDIDATE_CATEGORIES = [
    "Доменный бэкграунд",
    "Ключевой навык",
    "Достижение",
    "Сайд-проект",
    "Актив",
    "Личный факт",
]


def clean_cell(value: str) -> str:
    """Убирает markdown-разметку и лишние пробелы."""
    value = re.sub(r"\*\*", "", value)
    value = value.strip()
    return re.sub(r"\s+", " ", value)


def parse_table_row(line: str) -> list[str] | None:
    """Парсит строку markdown-таблицы."""
    if not line.startswith("|"):
        return None
    parts = [clean_cell(p) for p in line.strip().strip("|").split("|")]
    if not parts or parts[0] in ("#", "---", ""):
        return None
    if all(set(p) <= {"-"} for p in parts):
        return None
    return parts


CardRow = tuple[int, str, str, str]


def parse_candidates(path: Path) -> list[CardRow]:
    """Парсит candidates.md — 216 карт кандидата."""
    content = path.read_text(encoding="utf-8")
    cards: list[CardRow] = []
    current_category: str | None = None

    for line in content.splitlines():
        section_match = re.match(r"^## (.+)$", line)
        if section_match:
            name = section_match.group(1).strip()
            if name in CANDIDATE_CATEGORIES:
                current_category = name
            continue

        if current_category is None:
            continue

        row = parse_table_row(line)
        if row is None or not row[0].isdigit():
            continue

        deck_num = int(row[0])
        text = row[2] if len(row) >= 3 else ""
        cards.append((deck_num, current_category, current_category, text))

    return cards


def parse_pitch(path: Path) -> list[CardRow]:
    """Парсит context-examples.md — колода Питч."""
    content = path.read_text(encoding="utf-8")
    cards: list[CardRow] = []
    blocks = re.split(r"\n### (\d+)\. ", content)
    pitch_section = blocks[0]
    if "Питч" not in pitch_section:
        return cards

    for index in range(1, len(blocks), 2):
        deck_num = int(blocks[index])
        block = blocks[index + 1]
        if block.startswith("## "):
            break
        lines = block.strip().splitlines()
        if not lines:
            continue
        title = clean_cell(lines[0])
        scale = essence = ambition = ""
        for line in lines[1:]:
            if line.startswith("**Масштаб:**"):
                scale = clean_cell(line.split(":", 1)[1])
            elif line.startswith("**Суть:**"):
                essence = clean_cell(line.split(":", 1)[1])
            elif line.startswith("**Амбиция:**"):
                ambition = clean_cell(line.split(":", 1)[1])
        text = f"Масштаб: {scale}. Суть: {essence} Амбиция: {ambition}"
        cards.append((deck_num, "Питч", title, text))

    return cards


def parse_resources(path: Path) -> list[CardRow]:
    """Парсит decks.md — 30 карт условий работы."""
    content = path.read_text(encoding="utf-8")
    cards: list[CardRow] = []
    in_section = False

    for line in content.splitlines():
        if line.startswith("## Колода «Ресурс стартапа»"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue

        row = parse_table_row(line)
        if row is None or not row[0].isdigit():
            continue
        if len(row) < 4:
            continue
        deck_num = int(row[0])
        title = row[2]
        text = row[3]
        cards.append((deck_num, "Условие работы", title, text))

    return cards


def parse_risks(path: Path) -> list[CardRow]:
    """Парсит decks.md — 24 карты риска."""
    content = path.read_text(encoding="utf-8")
    cards: list[CardRow] = []
    in_section = False

    for line in content.splitlines():
        if line.startswith("## Колода «Риск»"):
            in_section = True
            continue
        if in_section and line.startswith("## ") and "Риск" not in line:
            break
        if not in_section:
            continue

        row = parse_table_row(line)
        if row is None or not row[0].isdigit():
            continue
        if len(row) < 4:
            continue
        deck_num = int(row[0])
        title = row[1]
        plot = row[2]
        business = row[3]
        text = f"{plot} Бизнес: {business}"
        cards.append((deck_num, "Риск", title, text))

    return cards


def parse_special(path: Path) -> list[CardRow]:
    """Парсит special-conditions.md — 24 особых условия."""
    content = path.read_text(encoding="utf-8")
    cards: list[CardRow] = []
    in_cards = False

    for line in content.splitlines():
        if line.startswith("## Все 24 карты"):
            in_cards = True
            continue
        if in_cards and line.startswith("## ") and "24 карты" not in line:
            if line.startswith("## Четыре новые"):
                break
            if not line.startswith("### "):
                continue

        if not in_cards:
            continue

        row = parse_table_row(line)
        if row is None or not row[0].isdigit():
            continue
        if len(row) < 3:
            continue
        deck_num = int(row[0])
        title = row[1]
        text = row[2]
        cards.append((deck_num, "Особое условие", title, text))

    return cards


def write_csv(path: Path, cards: list[CardRow]) -> None:
    """Записывает CSV для импорта в таблицы и макеты."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["№", "№ в колоде", "Тип карты", "Заголовок", "Текст"])
        for global_num, (deck_num, card_type, title, text) in enumerate(cards, start=1):
            writer.writerow([global_num, deck_num, card_type, title, text])


def write_markdown(path: Path, cards: list[CardRow]) -> None:
    """Записывает markdown-таблицу для просмотра и печати."""
    lines = [
        "# Таблица карт для печати",
        "",
        "Сводная таблица всех карт игры «Питч». Колонки соответствуют лицевой стороне карточки.",
        "",
        f"**Всего карт:** {len(cards)}",
        "",
        "| № | № в колоде | Тип карты | Заголовок | Текст |",
        "| --- | --- | --- | --- | --- |",
    ]
    for global_num, (deck_num, card_type, title, text) in enumerate(cards, start=1):
        safe_title = title.replace("|", "\\|")
        safe_text = text.replace("|", "\\|")
        lines.append(f"| {global_num} | {deck_num} | {card_type} | {safe_title} | {safe_text} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Источники",
            "",
            "- Кандидат: `cards/candidates.md`",
            "- Питч, условия, риски: `decks.md`, `cards/context-examples.md`",
            "- Особые условия: `cards/special-conditions.md`",
            "",
            "Файл сгенерирован скриптом `scripts/generate_print_table.py`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Собирает все карты и записывает файлы для печати."""
    all_cards: list[CardRow] = []
    all_cards.extend(parse_candidates(DOCS / "cards" / "candidates.md"))
    all_cards.extend(parse_pitch(DOCS / "cards" / "context-examples.md"))
    all_cards.extend(parse_resources(DOCS / "decks.md"))
    all_cards.extend(parse_risks(DOCS / "decks.md"))
    all_cards.extend(parse_special(DOCS / "cards" / "special-conditions.md"))

    out_dir = DOCS / "cards"
    write_markdown(out_dir / "cards-print.md", all_cards)
    write_csv(out_dir / "cards-print.csv", all_cards)

    counts: dict[str, int] = {}
    for _, card_type, _, _ in all_cards:
        counts[card_type] = counts.get(card_type, 0) + 1

    print(f"Сгенерировано {len(all_cards)} карт:")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
