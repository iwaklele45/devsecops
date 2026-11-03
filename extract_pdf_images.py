import glob
import os
import re
import struct
import sys
import zlib


def make_png(width, height, raw_pixels, has_alpha=False):
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data))
        )

    sig = b"\x89PNG\r\n\x1a\n"
    color_type = 6 if has_alpha else 2
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)

    bpp = 4 if has_alpha else 3
    stride = width * bpp
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(raw_pixels[y * stride : (y + 1) * stride])

    idat = chunk(b"IDAT", zlib.compress(bytes(scanlines), 9))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def extract_images_from_pdf(pdf_path, out_dir=None):
    if not out_dir:
        m = re.search(r"bab[-_](\d+)", pdf_path, re.IGNORECASE)
        bab_name = f"bab-{m.group(1)}" if m else "misc"
        out_dir = os.path.join("praktikum", "assets", bab_name)

    os.makedirs(out_dir, exist_ok=True)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    pos = 0
    img_streams = []
    while True:
        dict_start = pdf_data.find(b"<<", pos)
        if dict_start == -1:
            break
        dict_end = pdf_data.find(b">>", dict_start)
        if dict_end == -1:
            break

        header = pdf_data[dict_start + 2 : dict_end]
        stream_kw = pdf_data.find(b"stream", dict_end)
        if stream_kw != -1 and stream_kw - dict_end < 30:
            if pdf_data[stream_kw + 6 : stream_kw + 8] == b"\r\n":
                stream_start = stream_kw + 8
            elif pdf_data[stream_kw + 6 : stream_kw + 7] == b"\n":
                stream_start = stream_kw + 7
            else:
                stream_start = stream_kw + 6

            length_match = re.search(rb"/Length\s+(\d+)", header)
            if length_match:
                length = int(length_match.group(1))
                stream = pdf_data[stream_start : stream_start + length]
                pos = stream_start + length
            else:
                endstream_kw = pdf_data.find(b"endstream", stream_start)
                if endstream_kw != -1:
                    stream = pdf_data[stream_start : endstream_kw].rstrip(b"\r\n")
                    pos = endstream_kw + 9
                else:
                    pos = dict_end + 2
                    continue

            if b"/Subtype /Image" in header or b"/Subtype/Image" in header:
                img_streams.append((header, stream))
        else:
            pos = dict_end + 2

    saved_count = 0
    skip_next = False

    for i, (header, stream) in enumerate(img_streams):
        if skip_next:
            skip_next = False
            continue

        # Skip standalone alpha masks that are handled with previous image
        if b"/ColorSpace /DeviceGray" in header and b"/SMask" not in header:
            continue

        w_match = re.search(rb"/Width\s+(\d+)", header)
        h_match = re.search(rb"/Height\s+(\d+)", header)
        if not w_match or not h_match:
            continue

        width = int(w_match.group(1).decode())
        height = int(h_match.group(1).decode())
        has_smask = b"/SMask" in header

        saved_count += 1
        out_file = os.path.join(out_dir, f"image{saved_count}.png")

        try:
            if b"/Filter /FlateDecode" in header or b"/Filter/FlateDecode" in header:
                decomp_rgb = zlib.decompress(stream)
                if has_smask and i + 1 < len(img_streams):
                    next_header, next_stream = img_streams[i + 1]
                    if b"/ColorSpace /DeviceGray" in next_header:
                        decomp_alpha = zlib.decompress(next_stream)
                        rgba_data = bytearray(width * height * 4)
                        for p in range(width * height):
                            rgba_data[p * 4 : p * 4 + 3] = decomp_rgb[p * 3 : p * 3 + 3]
                            rgba_data[p * 4 + 3] = decomp_alpha[p]
                        png_bytes = make_png(width, height, rgba_data, has_alpha=True)
                        skip_next = True
                    else:
                        png_bytes = make_png(width, height, decomp_rgb, has_alpha=False)
                else:
                    png_bytes = make_png(width, height, decomp_rgb, has_alpha=False)

                with open(out_file, "wb") as f_out:
                    f_out.write(png_bytes)
                print(f"[{saved_count}] Extracted {width}x{height} -> {out_file}")

            elif b"/Filter /DCTDecode" in header or b"/Filter/DCTDecode" in header:
                jpg_file = os.path.join(out_dir, f"image{saved_count}.jpg")
                with open(jpg_file, "wb") as f_out:
                    f_out.write(stream)
                print(f"[{saved_count}] Extracted {width}x{height} JPEG -> {jpg_file}")
        except Exception as err:
            print(f"Error extracting image {saved_count} from {pdf_path}: {err}")

    print(f"Finished {pdf_path}: saved {saved_count} images to {out_dir}\n")


def main():
    targets = sys.argv[1:]
    if not targets:
        targets = sorted(
            glob.glob("praktikum/docker-lab/**/LAPORAN*.pdf", recursive=True)
        )

    if not targets:
        print("No PDF files found.")
        return

    for pdf in targets:
        extract_images_from_pdf(pdf)


if __name__ == "__main__":
    main()
