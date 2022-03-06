from typing import TypedDict, Optional, List, Dict, Union


class LoginInfo(TypedDict):
    """
    a dict holding a login and a password
    """
    login: str
    password: str


class Tag(TypedDict):
    """
    a dict representing a tag
    """
    description: Optional[str]
    translation: Optional[List[Dict]]
    original_term: Optional[str]

class Chapter(TypedDict):
    """
    a chapter
    """
    language: Optional[str]
    title: Optional[str]
    id: float
    source: Optional[str]
    raw_content: str # should be convertable into epub
    artefact: Dict # ex: images

class ArcChapter(TypedDict):
    """
    a collection of chapter which defines an arc/volume/etc..
    """
    chapters: List[Chapter]
    arc_id: int
    arc_title: Optional[str]

class NovelInstance(TypedDict):
    """
    an instancied novel
    """
    source: Optional[str]
    chapters: Optional[Union[List[Chapter]], List[ArcChapter]]
    extend: Optional[Dict]

class Novel(TypedDict):
    """
    a dict that stores all information for a novel
    """
    author: str
    tags: Optional[List[Tag]]
    description: Optional[str]
    instance: List[NovelInstance]
