from typing import Tuple, Optional

from tldextract.tldextract import ExtractResult, extract
import validators
import structlog
import difflib


log = structlog.getLogger(__name__)


def resolve_url(url_candidate: str) -> ExtractResult:
    """
    a function that check if the given text is an url and if it is, return the
    :param url:
    :return:
    """
    if validators.url(url_candidate):
        return extract(url_candidate)
    # TODO : raise a warning instead if malformed
    log.error(f"Expected a valid url: {url_candidate}")
    raise TypeError

def is_there_a_diff(old_chapter_text:str, new_chapter_text:str)->Tuple[bool, Optional[str]]:
    """
    TODO
    :param old_chapter_text:
    :param new_chapter_text:
    :return:
    """
    differ = difflib.Differ()
    difference_list = list(differ.compare(old_chapter_text.splitlines(), new_chapter_text.splitlines()))
    diff_bool = len([line for line in difference_list if not line.startswith("  ")])>0
    return (diff_bool,
            difflib.HtmlDiff().make_table(
                old_chapter_text.splitlines(),
                new_chapter_text.splitlines())
            if diff_bool else None)