
"""
 * -------------------------------------------- *
 * Important /!\                                *
 * Everything you will find in this             *
 * repository was either :                      *
 * - Found in the flipperzero-firmware          *
 *   repository (which means that you need      *
 *   to refer to this repo for any              *
 *   "is it legal" questions)                   *
 * - Made by me (which means that you don't     *
 *   need to give a shit about rights.          *
 *   Just don't do illegal stuff, i'me not      *
 *   responsible)                               *
 * Take that in account before looking at       *
 * this repo plz.                               *
 *                                              *
 * Thanks, enjoy <3                             *
 * -------------------------------------------- *
"""

from PIL import Image, ImageOps
import heatshrink2
import time
import sys
import io
import os

def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def unslice(img: Image, nb: int) -> Image:
    #don't ask, idk why its broken like that
    # My guess is version errors, but idk
    out = Image.new(img.mode, img.size)
    n = img.size[0]

    for x in range(img.width):
        for y in range(img.height):
            out.putpixel((x, y), img.getpixel((((nb * (x // nb)) + (nb - (x % nb) - 1)), y)))
    
    out2 = Image.new(out.mode, out.size)

    for x in range(out.width):
        for y in range(out.height):
            if ((x // (n // nb)) % 2):
                out2.putpixel((x, y), out.getpixel((x - (n // nb), y)))
            else:
                out2.putpixel((x, y), out.getpixel((x + (n // nb), y)))

    return out2

def png2xbm(file: str) -> bytes:
    with Image.open(file) as im:
        with io.BytesIO() as output:
            bw = im.convert("RGB")
            bw = ImageOps.invert(bw)
            bw.convert("1").save(output, format="XBM")
            return output.getvalue()

def xbm2png(data: bytes, size: tuple[int, int]) -> Image:
    with Image.frombytes("1", size, data, "raw") as im:
        bw = im.convert("RGB")
        bw = ImageOps.invert(bw)
        return bw

def xbm2hs(data: bytes) -> bytes:
    return heatshrink2.compress(data, window_sz2=8, lookahead_sz2=4)

def hs2xbm(data: bytes) -> bytes:
    return heatshrink2.decompress(data, window_sz2=8, lookahead_sz2=4)

def save_image(origin_fname, target_fname):
    output = png2xbm(origin_fname)
    f = io.StringIO(output.decode())
    f.readline()
    f.readline()
    data = f.read().strip().replace("\n", "").replace(" ", "").split("=")[1][:-1]
    data_str = data[1:-1].replace(",", " ").replace("0x", "")

    data_bin = bytearray.fromhex(data_str)

    encoded = xbm2hs(data_bin)

    enc = bytearray(encoded)
    enc = bytearray([len(enc) & 0xFF, len(enc) >> 8]) + enc

    if len(enc) + 1 < len(data_bin):
        data = b"\x01\x00" + enc
    else:
        data = b"\x00" + data_bin
    
    with open(target_fname, "wb+") as f:
        f.write(data)

def load_image(origin_fname, target_fname, w, h):
    with open(origin_fname, "rb") as f:
        data = bytearray(f.read())
    encoded = (data[0] == 1)
    if encoded:
        encoded_data = data[4:]
        decompressed_data = hs2xbm(encoded_data)
    else:
        decompressed_data = data[2:]
    
    unslice(xbm2png(decompressed_data, (w, h)), w // 8).save(target_fname)

def get_path(path):
    while path[-1] == '/' or path[-1] == '\\':
        path = path[:-1]
    if not os.path.isdir(path):
        return None
    return (os.path.dirname(path), os.path.basename(path))

def main(argv):
    if len(argv) == 1:
        print(f"""Usage : {argv[0]} [annimation_path]

Retreive PNG format from Flipper Zero .bm files (pass directory containing meta.txt and frames)""")
        return 1
    p = get_path(argv[1])
    if p is None:
        print("Path not found !")
        return 1
    if not os.path.isfile(os.path.join(argv[1], "meta.txt")):
        print("Missing \"meta.txt\" file !")
        return 1
    with open(os.path.join(argv[1], "meta.txt"), 'r') as f:
        meta = f.read()
    width = meta.split("Width: ")[-1].split('\n')[0]
    height = meta.split("Height: ")[-1].split('\n')[0]
    duration = meta.split("Duration: ")[-1].split('\n')[0]
    fps = meta.split("Frame rate: ")[-1].split('\n')[0]
    frames_order = meta.split("Frames order: ")[-1].split('\n')[0]
    if not height.isnumeric() or not width.isnumeric() or not duration.isnumeric() or not fps.isnumeric():
        print("Invalid Width / Height / Duration / Frame rate values in meta.txt !")
        return 1
    for e in frames_order.split(' '):
        if not e.isnumeric():
            print("Invalid number in frame order")
            return 1
    width = int(width)
    height = int(height)
    duration = int(duration)
    fps = int(fps)
    frames_order = [int(e) for e in frames_order.split(' ')]
    fms = 0
    while os.path.isfile(os.path.join(argv[1], f"frame_{fms}.bm")):
        fms += 1
    try:
        os.mkdir(os.path.join(p[0], p[1] + "_decoded"))
    except FileExistsError:
        print(f"A directory called \"{os.path.join(p[0], p[1] + '_decoded')}\" already exists !!")
        return 1
    frames = []
    for i in range(fms):
        load_image(os.path.join(argv[1], f"frame_{i}.bm"), os.path.join(os.path.join(p[0], p[1] + "_decoded"), f"frame_{i}.png"), width, height)
        frames.append(Image.open(os.path.join(os.path.join(p[0], p[1] + "_decoded"), f"frame_{i}.png")))
    out_frames = [frames[i] for i in frames_order]
    out_frames[0].save(os.path.join(os.path.join(os.path.join(p[0], p[1] + "_decoded"), "annimated_version.gif")), format="GIF", append_images=frames[1:], save_all=True, fps=fps, duration=1/fps)
    # 1 4
    # 2 5
    # 3 6
    # 7 8
    # x = hex(value).split('x')[-1]
    # while len(x) < 2:
    #     x = '0' + x
    # print(eval(f"\"\\u28{x}\""))

    v = [[0 for _ in range(width + (width % 2))] for _ in range(height + (height % 4))]
    for f in out_frames:
        for x in range(f.width):
            for y in range(f.height):
                v[y][x] = int(f.getpixel((x, y)) == (0, 0, 0))
        clear()
        for y in range(0, height - 4, 4):
            for x in range(0, width - 2, 2):
                value = 1 * v[y][x] + \
                        (2 << 0) * v[y + 1][x] + \
                        (2 << 1) * v[y + 2][x] + \
                        (2 << 2) * v[y][x + 1] + \
                        (2 << 3) * v[y + 1][x + 1] + \
                        (2 << 4) * v[y + 2][x + 1] + \
                        (2 << 5) * v[y + 3][x] + \
                        (2 << 6) * v[y + 3][x + 1]
                x = hex(value).split('x')[-1]
                while len(x) < 2:
                    x = '0' + x
                print(eval(f"\"\\u28{x}\""), end='')
            print()
        time.sleep(1 / fps)

if __name__ == "__main__":
    sys.exit(main(sys.argv))