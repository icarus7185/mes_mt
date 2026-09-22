"""Archives received images into a bounded-size history folder."""

from pathlib import Path


class HistoryService:
    """Saves images into ``self.hist_dir``, keeping only the ``max_files`` newest."""

    def __init__(self, hist_dir: Path, max_files: int) -> None:
        self.hist_dir = hist_dir
        self.max_files = max_files

    def save(self, data: bytes, filename: str) -> Path:
        self.hist_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.hist_dir / filename
        out_path.write_bytes(data)
        self._enforce_limit()
        return out_path

    def list_files(self) -> list[Path]:
        """Return archived files, newest first."""
        if not self.hist_dir.is_dir():
            return []
        files = [p for p in self.hist_dir.iterdir() if p.is_file()]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _enforce_limit(self) -> None:
        for stale in self.list_files()[self.max_files:]:
            stale.unlink(missing_ok=True)
