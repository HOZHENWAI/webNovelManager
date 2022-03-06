from typing import List, Optional, Union

import structlog
from config import settings

from ..data.format import LoginInfo, NovelInstance, Chapter
from .functions import resolve_url


log = structlog.getLogger(__name__)


class WebsitePlugin:
    """
    Base class for all website plugins
    """
    _HEADERS_ = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"}
    _DOMAIN_:str = None
    _SUBDOMAIN_: Optional[Union[List[str], str]] = None

    def __init__(self):
        self.require_login:Optional[bool] = None

    def _get_credentials(self)->Optional[LoginInfo]:
        """
        Fetch the login credentials from the environment/config using namespace
        :return: a dictionary containing the necessary credentials for login
        """
        try:
            return LoginInfo(login=settings[type(self).__name__]["login"], password=settings[type(self).__name__]["password"])
        except KeyError:
            log.error(f"Missing credentials in the secret file. Are you sure everything is properly setup?: {type(self).__name__}")
            return None

    def is_plugin_relevant(self, url: str) -> bool:
        """
        Given an url, return wheter or not this plugin should be used
        :param url: a website url
        :return:
        """
        extract_result = resolve_url(url)
        return extract_result.domain == self._DOMAIN_

    def login(self)->bool:
        """
        Log to the website using stored credentials
        all subclasses that requires a login need to implement this class
        :return: a bool which indicates whether the login was successful
        """
        raise NotImplementedError

    def fetch_novel(self, novel_link:str)->NovelInstance:
        """
        Try to fetch a novel given a link and process as needed
        :param novel_link:
        :return:
        """
        return self._fetch_novel(novel_link)

    def _fetch_novel(self, novel_link:str)->NovelInstance:
        """
        Try to fetch a novel given a link
        :param novel_link:
        :return:
        """
        raise NotImplementedError

    def fetch_chapter(self, link_url)->Chapter:
        """
        Try to fetch a chapter given the link
        :return:
        """
        return self._fetch_chapter(link_url)

    def _fetch_chapter(self, link)->Chapter:
        """
        Try to fetch a chapter given the link
        Should be implemented by the child classes
        :param link:
        :return:
        """
        raise NotImplementedError

    def _get_chapter_raw(self, url: str)->str:
        """
        Given the link, return the html string that can be parsed
        :param url:
        :return:
        """
        raise NotImplementedError

