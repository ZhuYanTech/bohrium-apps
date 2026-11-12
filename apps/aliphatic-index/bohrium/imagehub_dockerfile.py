"""Generate the context-free Dockerfile used by Bohrium's web builder."""

import argparse
from pathlib import Path
import re


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Full GitHub commit SHA")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-fA-F0-9]{40}", args.revision):
        parser.error("revision must be a full 40-character commit SHA")

    dockerfile = Path(__file__).resolve().parents[1].joinpath("Dockerfile").read_text()
    print(f"""ARG SOURCE_REVISION={args.revision}
FROM python:3.11-slim-bookworm AS source
ARG SOURCE_REVISION
ADD https://codeload.github.com/ZhuYanTech/bohrium-apps/tar.gz/${{SOURCE_REVISION}} /tmp/source.tar.gz
RUN mkdir -p /source && tar -xzf /tmp/source.tar.gz -C /source --strip-components=3 \\
    bohrium-apps-${{SOURCE_REVISION}}/apps/aliphatic-index
""")
    for line in dockerfile.splitlines():
        if line.startswith("COPY "):
            parts = line.split()
            sources = " ".join("/source/" + filename for filename in parts[1:-1])
            line = f"COPY --from=source {sources} {parts[-1]}"
        print(line)


if __name__ == "__main__":
    main()
