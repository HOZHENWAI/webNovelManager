from typing import List, Optional, Union

import structlog
from tinydb import TinyDB, Query
from config import settings
from dynaconf import ValidationError

log = structlog.getLogger(__name__)


class Database:
    """
    Base class for all website plugins
    """
    def __init__(self):
        try:
            self.db_location = settings[type(self).__name__]['path']
        except ValidationError:
            log.error(f"Couldn't set the path to: {settings[type(self).__name__]['path']}")
            self.db_location = "~/webnovelmanager/"

    def store_novel_instance(self,):
        raise NotImplementedError

    def store_chapter_instance(self):
        raise NotImplementedError

    def store_artefacts(self):
        raise NotImplementedError

    def get_artefacts(self):
        raise NotImplementedError

    def get_novel_instance(self):
        raise NotImplementedError

    def get_chapter_instance(self):
        raise NotImplementedError

    def delete_chapter(self):
        raise NotImplementedError

    def delete_novel(self):
        raise NotImplementedError