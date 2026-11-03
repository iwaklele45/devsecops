import glob
import os
import re
import sys


def get_image_filename(assets_dir, img_id):
    for ext in ["png", "jpg", "jpeg", "webp"]:
        candidate = f"{img_id}.{ext}"
        if os.path.exists(os.path.join(assets_dir, candidate)):
            return candidate
    return f"{img_id}.png"


def update_markdown(md_path):
    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        return

    m = re.search(r"bab[-_](\d+)", os.path.basename(md_path), re.IGNORECASE)
    bab_name = f"bab-{m.group(1)}" if m else "misc"
    assets_dir = os.path.join("praktikum", "assets", bab_name)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    def replace_tag(match):
        alt = match.group(1).strip()
        img_num = match.group(2)
        img_id = f"image{img_num}"
        img_filename = get_image_filename(assets_dir, img_id)
        rel_path = f"./assets/{bab_name}/{img_filename}"
        if not alt:
            if img_num == "1":
                alt = "Logo PENS"
            else:
                alt = f"Screenshot {img_id}"
        return f"![{alt}]({rel_path})"

    # Replace ![][image1] or ![alt][image1]
    new_content = re.sub(
        r"!\[(.*?)\]\[image(\d+)\]",
        replace_tag,
        content,
    )

    # Strip trailing base64 definitions: [imageN]: <data:image/...>
    clean_lines = [
        line for line in new_content.splitlines()
        if not re.match(r"^\[image\d+\]:\s*<data:image/", line)
    ]

    result = "\n".join(clean_lines).rstrip() + "\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Successfully updated {md_path} -> references ./assets/{bab_name}/")


def main():
    targets = sys.argv[1:] or sorted(glob.glob("praktikum/laporan-prak-bab-*.md"))
    if not targets:
        print("No markdown files found.")
        return
    for t in targets:
        update_markdown(t)


if __name__ == "__main__":
    main()
