from pathlib import Path


class Solution:
    def simplifyPath(self, path: str) -> str:
        return str(Path(path).resolve())
