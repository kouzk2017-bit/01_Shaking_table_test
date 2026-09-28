"""Fixed-name result folders under 06_results/opensees/.

Each stage writes to ``<name>__running``.  On success it replaces ``<name>``;
on failure it becomes ``<name>__failed`` and the previous good ``<name>`` is
kept, so a failed rerun never destroys the last valid result.
"""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
EXPERIMENT_ROOT = PROJECT / '02_10-story_2015'
RESULTS = PROJECT / '06_results' / 'opensees'


def start(name: str) -> Path:
    work = RESULTS / f'{name}__running'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    return work


def finish(work: Path, name: str, succeeded: bool) -> Path:
    target = RESULTS / (name if succeeded else f'{name}__failed')
    if target.exists():
        shutil.rmtree(target)
    work.rename(target)
    if succeeded:
        stale = RESULTS / f'{name}__failed'
        if stale.exists():
            shutil.rmtree(stale)
    return target
