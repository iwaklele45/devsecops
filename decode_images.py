import base64
import glob
import os
import re
import sys


def process_file(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match bab number from filename, e.g. laporan-prak-bab-1.md -> bab-1
    m = re.search(r"bab-(\d+)", os.path.basename(md_path))
    bab_dir = f"bab-{m.group(1)}" if m else "misc"
    assets_dir = os.path.join("praktikum", "assets", bab_dir)
    os.makedirs(assets_dir, exist_ok=True)

    img_defs = re.findall(
        r"^\[(image\d+)\]:\s*<data:image/([^;]+);base64,([^>]+)>",
        content,
        re.MULTILINE,
    )
    if not img_defs:
        print(f"Skipping {md_path}: no base64 images found.")
        return

    for img_id, ext, b64_str in img_defs:
        img_name = f"{img_id}.{ext}"
        img_path = os.path.join(assets_dir, img_name)
        with open(img_path, "wb") as f_img:
            f_img.write(base64.b64decode(b64_str.strip()))
        print(f"Saved: {img_path}")

        rel_path = f"./assets/{bab_dir}/{img_name}"
        content = re.sub(
            rf"!\[(.*?)\]\[{img_id}\]",
            rf"![\1]({rel_path})",
            content,
        )

    # Strip trailing data uri definitions
    clean_lines = [
        line for line in content.splitlines()
        if not re.match(r"^\[image\d+\]:\s*<data:image/", line)
    ]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_lines).rstrip() + "\n")
    print(f"Updated: {md_path}")


def main():
    targets = sys.argv[1:] or glob.glob("praktikum/laporan-prak-bab-*.md")
    for target in targets:
        process_file(target)


if __name__ == "__main__":
    main()
