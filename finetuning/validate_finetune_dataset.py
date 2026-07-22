import json
from pathlib import Path
from typing import Any
from loguru import logger


DATASET_FILE = Path("finetune_data.jsonl")
EXPECTED_ROLES = ["system", "user", "assistant"]


def validate_message(message: Any, line_number: int, index: int) -> None:
    if not isinstance(message, dict):
        raise TypeError(f"Line {line_number}, message {index}: expected an object")

    role = message.get("role")
    content = message.get("content")

    if role not in {"system", "user", "assistant"}:
        raise ValueError(
            f"Line {line_number}, message {index}: invalid role {role!r}"
        )

    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            f"Line {line_number}, message {index}: content must be non-empty text"
        )


def validate_record(record: Any, line_number: int) -> None:
    if not isinstance(record, dict):
        raise TypeError(f"Line {line_number}: expected a JSON object")

    messages = record.get("messages")
    if not isinstance(messages, list):
        raise TypeError(f"Line {line_number}: 'messages' must be a list")

    if len(messages) != 3:
        raise ValueError(
            f"Line {line_number}: expected 3 messages, got {len(messages)}"
        )

    for index, message in enumerate(messages):
        validate_message(message, line_number, index)

    roles = [message["role"] for message in messages]
    if roles != EXPECTED_ROLES:
        raise ValueError(
            f"Line {line_number}: expected roles {EXPECTED_ROLES}, got {roles}"
        )

    assistant_content = messages[2]["content"]
    try:
        assistant_json = json.loads(assistant_content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Line {line_number}: assistant content is not valid JSON: {exc}"
        ) from exc

    if not isinstance(assistant_json, dict):
        raise TypeError(
            f"Line {line_number}: assistant content must decode to an object"
        )


def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {DATASET_FILE.resolve()}"
        )

    valid_count = 0

    with DATASET_FILE.open("r", encoding="utf-8") as infile:
        for line_number, line in enumerate(infile, start=1):
            if not line.strip():
                continue

            record = json.loads(line)
            validate_record(record, line_number)
            valid_count += 1

    if valid_count == 0:
        raise RuntimeError("The dataset contains no training examples")

    logger.info(f"Validated {valid_count} training examples successfully.")


if __name__ == "__main__":
    main()
