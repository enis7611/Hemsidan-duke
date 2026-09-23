"""Tester för mall/verifiera.py. Kör: python mall/test/test_verifiera.py"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "mall"))
from verifiera import verifiera  # noqa: E402

fel_antal = 0


def ok(villkor, text):
    global fel_antal
    print(("OK   " if villkor else "FEL  ") + text)
    if not villkor:
        fel_antal += 1


def innehaller(fel, bit):
    return any(bit in f for f in fel)


# 1. En befintlig, korrekt sida passerar, inklusive inlänkning från index.html
with tempfile.TemporaryDirectory() as dumpar:
    fel = verifiera(ROT / "site", "extendmqtt.html", "index.html", Path(dumpar))
    ok(fel == [], f"extendmqtt.html passerar (fick: {fel})")
    ok((Path(dumpar) / "extendmqtt-sv-desktop.png").is_file(), "skärmdump SV desktop skapad")
    ok((Path(dumpar) / "extendmqtt-en-mobil.png").is_file(), "skärmdump EN mobil skapad")

# 2. Fixture med kända fel: varje fel ska rapporteras
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    shutil.copy(ROT / "site" / "index.html", tmp / "index.html")
    subprocess.run(
        ["pwsh", "-File", str(ROT / "mall" / "bygg-sida.ps1"),
         "-Innehall", str(ROT / "mall" / "test" / "fixtures" / "trasig.html"), "-Ut", str(tmp)],
        check=True, capture_output=True,
    )
    fel = verifiera(tmp, "trasig.html", "index.html", None)
    for f in fel:
        print("     rapporterat:", f)
    ok(innehaller(fel, "odefinieradFunktion"), "JS-fel rapporteras")
    ok(innehaller(fel, "Saknar data-en") and innehaller(fel, "Rubrik"), "saknad engelsk text rapporteras")
    ok(innehaller(fel, "inre markup") and innehaller(fel, "Text med"), "data-sv med inre markup rapporteras")
    ok(innehaller(fel, "finns-inte.html"), "trasig sidlänk rapporteras")
    ok(innehaller(fel, "#saknas"), "trasigt ankare rapporteras")
    ok(innehaller(fel, "index.html#finns-inte-heller"), "trasigt ankare på annan sida rapporteras")
    ok(innehaller(fel, "länkas inte från index.html"), "saknad inlänkning rapporteras")

print("Alla test OK" if fel_antal == 0 else f"{fel_antal} test fallerade")
sys.exit(1 if fel_antal else 0)
