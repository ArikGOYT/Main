#!/usr/bin/env python3
"""Bad Apple!! ASCII player — converts video.mp4 to ANSI-colored ASCII frames and plays in terminal."""
import os, sys, time, shutil, subprocess, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video.mp4")
CHARS = " .:-=+*#%@"  # dark -> bright

def get_ffmpeg():
    for c in ("ffmpeg",):
        p = shutil.which(c)
        if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found")

class Term:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        import termios, tty
        self.old = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        sys.stdout.write("\033[?1049h\033[?25l")  # alt screen, hide cursor
        sys.stdout.flush()
        return self
    def __exit__(self, *a):
        import termios
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        sys.stdout.write("\033[?25h\033[?1049l\033[H\033[2J")
        sys.stdout.flush()

def read_key():
    import select
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

def main():
    cols, rows = shutil.get_terminal_size((80, 24))
    fps = 30
    # ASCII chars are ~2x taller than wide; width = 2*height
    fh = max(10, rows - 1)
    fw = fh * 2
    fw = min(fw, cols)
    fh = fw // 2

    ffmpeg = get_ffmpeg()
    tmpdir = tempfile.mkdtemp(prefix="ba_frames_")
    print("Converting frames (one-time)...", flush=True)
    proc = subprocess.Popen(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", SRC,
         "-vf", f"fps=15,scale={fw}:{fh}:flags=lanczos,format=gray",
         "-start_number", "0", os.path.join(tmpdir, "f%05d.pgm")],
    )
    done_flag = os.path.join(tmpdir, ".done")

    def wait_frame(i):
        path = os.path.join(tmpdir, f"f{i:05d}.pgm")
        deadline = time.time() + 30
        while not os.path.exists(path):
            if proc.poll() is not None and not os.path.exists(path):
                return None
            if time.time() > deadline:
                return None
            time.sleep(0.01)
        return path

    with Term():
        i = 0
        frame_dur = 1 / 15.0
        paused = False
        while True:
            path = wait_frame(i)
            if path is None:
                break
            t0 = time.time()
            with open(path, "rb") as f:
                magic = f.readline(); dims = f.readline().split()
                maxv = int(f.readline())
                data = f.read()
            w, h = int(dims[0]), int(dims[1])
            out = ["\033[H"]
            for y in range(h):
                row = data[y*w:(y+1)*w]
                line = "".join(CHARS[min(len(CHARS)-1, (p * len(CHARS)) // (maxv+1))] for p in row)
                out.append(line + "\r\n")
            out.append(f"\033[2J\033[{h+1}]", )
            sys.stdout.write("".join(out))
            sys.stdout.flush()
            key = read_key()
            if key in ("q", "\x03"):
                break
            if key == " ":
                paused = not paused
            elapsed = time.time() - t0
            if not paused:
                # catch up if slow, otherwise pace
                if elapsed < frame_dur:
                    time.sleep(frame_dur - elapsed)
                i += 1
            else:
                # still advance ffmpeg reading? keep showing same frame
                pass
    shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
