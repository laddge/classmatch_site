import os
import shutil
import glob
import hashlib
import sass


def build():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    shutil.rmtree("css")
    sass.compile(
        dirname=("res/scss", "css"),
        output_style="compressed",
    )
    for fn in glob.glob("css/*"):
        with open(fn, "rb") as f:
            hashstr = hashlib.md5(f.read()).hexdigest()[:7]
        new_fn = (fn[::-1].replace(".", f".{hashstr[::-1]}-", 1))[::-1]
        shutil.move(fn, new_fn)


if __name__ == "__main__":
    build()
