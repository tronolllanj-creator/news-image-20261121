import os
import shutil
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main():
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "entry.png")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, "entry.png")

    if not os.path.exists(source_path):
        print(f"error: source image not found at {source_path}")
        sys.exit(1)

    with open(source_path, "rb") as f:
        data = f.read()

    if not data.startswith(PNG_MAGIC):
        print(f"error: {source_path} does not start with PNG magic bytes")
        sys.exit(1)

    try:
        shutil.copy2(source_path, output_path)
    except OSError as e:
        print(f"error: failed to copy to {output_path}: {e}")
        sys.exit(1)

    try:
        out_size = os.path.getsize(output_path)
    except OSError as e:
        print(f"error: cannot stat output {output_path}: {e}")
        sys.exit(1)

    if out_size != len(data):
        print(f"error: output size mismatch ({out_size} != {len(data)})")
        sys.exit(1)

    print(output_path)
    print(len(data))


if __name__ == "__main__":
    main()
