"""Atomic storage for recoverable control state, separate from installation data."""

import json
import os
from pathlib import Path
import tempfile


def read_document(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise RuntimeError(f'No se puede cargar {path}: {error}') from error
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise RuntimeError(f'{path}: formato o versión de estado inválidos')
    return data


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        self.last_saved = None

    def load(self):
        if not self.path.exists():
            return None
        data = read_document(self.path)
        self.last_saved = self.serialize(data)
        return data

    @staticmethod
    def serialize(data):
        return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n'

    def save(self, data):
        serialized = self.serialize(data)
        if serialized == self.last_saved:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                             prefix='.state-', suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                file.write(serialized)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        self.last_saved = serialized
        return True
