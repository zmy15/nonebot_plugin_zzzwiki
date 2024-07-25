import os

from pydantic import BaseModel, Extra
from pathlib import Path

file_path = os.path.join(Path(__file__).parent, './resources/zzzwiki')


class Config(BaseModel, extra=Extra.ignore):
    resources_path: str = file_path
