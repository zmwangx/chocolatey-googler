import hashlib
import os
import pathlib
import re
import xml.etree.ElementTree as ET
from distutils.version import StrictVersion as Version
from typing import Callable

import requests


ROOT = pathlib.Path(__file__).parent.parent
NUSPEC = ROOT / "googler.nuspec"
SCRIPT = ROOT / "tools/googler/googler.py"
VERIFICATION = ROOT / "legal/VERIFICATION.txt"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ns = {"nuspec": "http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd"}


def get_current_version() -> str:
    return ET.parse(NUSPEC).find("nuspec:metadata/nuspec:version", ns).text


def get_latest_version() -> str:
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    resp = requests.get(
        "https://api.github.com/repos/jarun/googler/releases/latest",
        headers=headers,
        timeout=5,
    ).json()
    tag = resp["tag_name"]
    return tag.lstrip("v")


def get_script(version: str) -> str:
    return requests.get(
        f"https://raw.githubusercontent.com/jarun/googler/v{version}/googler"
    ).text


def update_file_content(path: pathlib.Path, repl: Callable[..., str], *args, **kwargs):
    with path.open(encoding="utf-8") as fin:
        content = fin.read()
    content = repl(content, *args, **kwargs)
    with path.open("w", encoding="utf-8") as fout:
        fout.write(content)


def nuspec_repl(content: str, old_version: str, new_version: str) -> str:
    content = content.replace(
        f"<version>{old_version}</version>", f"<version>{new_version}</version>"
    )
    content = content.replace(f"v{old_version}", f"v{new_version}")
    return content


def script_repl(content: str, new_content: str) -> str:
    return new_content


def verification_repl(
    content: str, old_version: str, new_version: str, new_checksum: str
) -> str:
    content = content.replace(f"v{old_version}", f"v{new_version}")
    content = re.sub(r"checksum: \w+", f"checksum: {new_checksum}", content)
    return content


def main():
    current_version = get_current_version()
    latest_version = get_latest_version()
    if Version(latest_version) <= Version(current_version):
        return

    print(f"updating from {current_version} to {latest_version}")
    latest_script_content = get_script(latest_version)
    update_file_content(NUSPEC, nuspec_repl, current_version, latest_version)
    update_file_content(SCRIPT, script_repl, latest_script_content)
    update_file_content(
        VERIFICATION,
        verification_repl,
        current_version,
        latest_version,
        hashlib.sha256(latest_script_content.encode("utf-8")).hexdigest().upper(),
    )
    if os.getenv("GITHUB_WORKFLOW"):
        # Running in GitHub Actions; export env vars for future steps.
        print("::set-env name=UPDATED::true")
        print(f"::set-env name=NEW_VERSION::{latest_version}")


if __name__ == "__main__":
    main()
