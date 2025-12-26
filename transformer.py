import logging
from pathlib import Path


level = logging.DEBUG
logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def transform_content(content: str) -> tuple[str, dict]:
    replacements = {
        "ENTRIES": "RESULTS",
        "ENTRY": "RESULT",
        "entrytime": "swimtime",
    }

    stats = {}
    for old, new in replacements.items():
        count = content.count(old)
        content = content.replace(old, new)
        stats[old] = count

    return content, stats


def process_file(input_path: Path, output_path: Path) -> None:
    logging.info("Reading input file: %s", input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    content = input_path.read_text(encoding="utf-8")
    logging.debug("Input file size: %d chars", len(content))

    transformed, stats = transform_content(content)

    for key, count in stats.items():
        logging.info("Replaced '%s' → %d times", key, count)

    output_path.write_text(transformed, encoding="utf-8")
    logging.info("Saved result to: %s", output_path)


def ask_path(prompt: str) -> Path:
    while True:
        value = input(prompt).strip().strip('"')
        if value:
            return Path(value)
        print("❌ Path cannot be empty")


def main() -> None:
    print("=== Lenex ENTRIES → RESULTS transformer ===")

    input_path = ask_path("Input file path: ")
    output_path = ask_path("Output file path: ")

    try:
        process_file(input_path, output_path)
        print("✅ Done")
    except Exception:
        logging.exception("Processing failed")
        print("❌ Error occurred, see logs")


if __name__ == "__main__":
    main()
