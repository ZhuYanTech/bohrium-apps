FROM python:3.13-slim

LABEL org.opencontainers.image.title="PoseBusters docking pose validator" \
      org.opencontainers.image.source="https://github.com/ZhuYanTech/bohrium-apps"

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libgomp1 libxrender1 libxext6 openssh-server supervisor net-tools ca-certificates \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*_key*

WORKDIR /app
COPY requirements-posebusters.txt requirements-launching.txt ./
RUN python -m pip install -r requirements-posebusters.txt -r requirements-launching.txt
COPY run_posebusters.py launching.py ./
COPY examples/make_bad_poses.py examples/test_run.sh ./examples/

RUN set -eu; \
    dataset="$(python -c 'import pathlib, posebusters; print(pathlib.Path(posebusters.__file__).parent / "datasets/pdb/1ia1")')"; \
    python /app/launching.py --mol_pred "$dataset/1ia1_ligand.sdf" \
      --mol_true "$dataset/1ia1_ligand.sdf" \
      --protein_file "$dataset/1ia1_protein_one_lig_removed.pdb" \
      --enable-full_report --output_dir /tmp/smoke; \
    python -c 'import csv; rows = list(csv.DictReader(open("/tmp/smoke/summary.csv", encoding="utf-8-sig"))); assert len(rows) == 1 and rows[0]["通过项数"] == rows[0]["检查项总数"] == "28" and rows[0]["PB_valid"] == "是", rows'; \
    rm -rf /tmp/smoke
