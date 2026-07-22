import json
import random
from pathlib import Path

from loguru import logger


SOURCE_FILE = Path("finetune_data.jsonl")
TRAIN_FILE = Path("finetune_train.jsonl")
VALIDATION_FILE = Path("finetune_validation.jsonl")
TEST_FILE = Path("finetune_test.jsonl")

TRAIN_RATIO = 0.80
VALIDATION_RATIO = 0.10
TEST_RATIO = 0.10
SEED = 42


def load_valid_lines(path: Path) -> list[str]:
    """Load non-empty JSONL records and verify that each line is a JSON object."""
    lines: list[str] = []

    with path.open("r", encoding="utf-8") as infile:
        for line_number, line in enumerate(infile, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            if not isinstance(parsed, dict):
                raise TypeError(
                    f"Line {line_number} must contain a JSON object"
                )

            lines.append(stripped)

    return lines


def write_jsonl(path: Path, lines: list[str]) -> None:
    """Write JSONL records with one trailing newline."""
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def validate_ratios() -> None:
    ratios = (TRAIN_RATIO, VALIDATION_RATIO, TEST_RATIO)

    if any(ratio <= 0 for ratio in ratios):
        raise ValueError("All split ratios must be greater than zero")

    if not abs(sum(ratios) - 1.0) < 1e-9:
        raise ValueError(
            "TRAIN_RATIO, VALIDATION_RATIO, and TEST_RATIO must sum to 1.0"
        )


def calculate_split_sizes(total: int) -> tuple[int, int, int]:
    """
    Calculate 80/10/10 split sizes while ensuring every split is non-empty.

    The test split receives any rounding remainder so that the three sizes
    always add up exactly to the total number of records.
    """
    if total < 3:
        raise RuntimeError(
            "At least 3 examples are required to create train, validation, and test splits"
        )

    train_size = round(total * TRAIN_RATIO)
    validation_size = round(total * VALIDATION_RATIO)
    test_size = total - train_size - validation_size

    # Protect very small datasets from rounding a split down to zero.
    train_size = max(1, train_size)
    validation_size = max(1, validation_size)
    test_size = max(1, test_size)

    # If minimum-size corrections caused an overflow, remove records from
    # the largest split until the total is correct.
    while train_size + validation_size + test_size > total:
        sizes = {
            "train": train_size,
            "validation": validation_size,
            "test": test_size,
        }
        largest = max(sizes, key=sizes.get)

        if largest == "train" and train_size > 1:
            train_size -= 1
        elif largest == "validation" and validation_size > 1:
            validation_size -= 1
        elif test_size > 1:
            test_size -= 1
        else:
            raise RuntimeError("Could not calculate valid split sizes")

    return train_size, validation_size, test_size


def main() -> None:
    validate_ratios()

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {SOURCE_FILE.resolve()}"
        )

    lines = load_valid_lines(SOURCE_FILE)

    if not lines:
        raise RuntimeError("The source dataset contains no examples")

    random.Random(SEED).shuffle(lines)

    train_size, validation_size, test_size = calculate_split_sizes(len(lines))

    train_end = train_size
    validation_end = train_end + validation_size

    train_lines = lines[:train_end]
    validation_lines = lines[train_end:validation_end]
    test_lines = lines[validation_end:]

    if len(test_lines) != test_size:
        raise RuntimeError(
            f"Internal split error: expected {test_size} test examples, "
            f"got {len(test_lines)}"
        )

    write_jsonl(TRAIN_FILE, train_lines)
    write_jsonl(VALIDATION_FILE, validation_lines)
    write_jsonl(TEST_FILE, test_lines)

    logger.success("Dataset split completed successfully")
    logger.info("Random seed: {}", SEED)
    logger.info("Total examples: {}", len(lines))
    logger.info(
        "Training examples: {} ({:.1%})",
        len(train_lines),
        len(train_lines) / len(lines),
    )
    logger.info(
        "Validation examples: {} ({:.1%})",
        len(validation_lines),
        len(validation_lines) / len(lines),
    )
    logger.info(
        "Test examples: {} ({:.1%})",
        len(test_lines),
        len(test_lines) / len(lines),
    )
    logger.info("Training file: {}", TRAIN_FILE.resolve())
    logger.info("Validation file: {}", VALIDATION_FILE.resolve())
    logger.info("Test file: {}", TEST_FILE.resolve())


if __name__ == "__main__":
    main()