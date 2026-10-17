import shutil
import sys
import zipfile
from pathlib import Path

from ml.config import (
    TRAINING_AUDIO_DIR,
    AUDIO_EXTENSIONS,
)


def main():
    if len(sys.argv) != 2:
        print(
            'Usage: python training/00_extract_audio_zip.py "C:\\path\\to\\audios.zip"'
        )
        raise SystemExit(1)

    zip_path = Path(sys.argv[1]).expanduser().resolve()

    if not zip_path.exists():
        raise FileNotFoundError(
            f"ZIP file not found: {zip_path}"
        )

    extracted = 0

    with zipfile.ZipFile(zip_path, "r") as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue

            original_name = Path(item.filename).name

            if not original_name:
                continue

            suffix = Path(original_name).suffix.lower()

            if suffix not in AUDIO_EXTENSIONS:
                continue

            destination = (
                TRAINING_AUDIO_DIR /
                original_name
            )

            with archive.open(item) as source:
                with destination.open("wb") as target:
                    shutil.copyfileobj(
                        source,
                        target,
                    )

            extracted += 1

    print(
        f"Extracted {extracted} audio files to:"
    )
    print(TRAINING_AUDIO_DIR)


if __name__ == "__main__":
    main()
