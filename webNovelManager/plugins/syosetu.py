from typing import Dict, List, Optional, TypedDict, Tuple
from datetime import datetime
import requests

from structlog import get_logger
from bs4 import BeautifulSoup

from .plugins import WebsitePlugin
from .constructs import NovelInstance, Chapter


log = get_logger(__name__)


class ShortNovel(TypedDict):
    """
    A typed dict representing a novel to use for updates or quick presentation
    """
    title: str
    author: str
    ref: str
    last_modified: datetime

def _get_novels_from_category_page(category_page: BeautifulSoup) -> List[ShortNovel]:
    """
    Given a beautiful soup which correspond to a page of favorit return a list of novels
    :param category_page:
    :return:
    """
    table_novels = category_page.find_all('table', {'class': 'favnovel'})
    return [
        {
            'title': novel_soup.find('a', {'class': 'title'}).text,
            'author': novel_soup.find('span', {'class': 'fn_name'}).text.strip('\n').lstrip('（').rstrip('）'),
            'ref': novel_soup.find('a', {'class': 'title'})['href'],
            'last_modified': datetime.strptime(
                novel_soup.find('td', {'class': 'info'}).find('p').next.strip('\n').split('：')[1],
                "%Y/%m/%d %H:%M"
            )
        }
        for novel_soup in table_novels
    ]

def _find_novel_info_page(novel_page:BeautifulSoup)->str:
    """
    find the link where all the info are for one novel
    :param novel_page:
    :return: a link
    """
    return novel_page.find('ul', id='head_nav').find_all('li')[1].next['href']

class Syosetu(WebsitePlugin):
    """

    """
    _DOMAIN_ = "syosetu"
    _DEFAULT_LINK = f"https://{_DOMAIN_}.com"
    _SUBDOMAIN_ = ["novel18", "ncode"]
    __FAVORITE_SUBDOMAIN__ = {
        "novel18" : f"{_DEFAULT_LINK}/favnovelmain18/list/",
        "ncode" : f"{_DEFAULT_LINK}/favnovelmain/list/"
    }
    __LOGIN__URL = "https://ssl.syosetu.com/login/login/"

    MAX_LOOP_ = 10 # max iteration loop for avoiding infinite loop
    def __init__(self):
        super().__init__()
        self.session = requests.session()

    def login(self)->bool:
        """
        Log into the session using the credentials stored
        :return: a boolean indicating whether the logging was successful or not
        """
        credentials = self._get_credentials()
        forms = {
            "narouid": credentials["login"],
            "pass": credentials["password"],
        }
        response = self.session.post(self.__LOGIN__URL, forms, headers = self._HEADERS_)

        if response.status_code == 200:
            return self.is_logged()
        log.warning(f"Status code:{response.status_code} on login. Is this expected?")
        return False

    def set_adult(self)->None:
        """
        Naru has an adult subdomain which requires a cookie to be set before access.
        This simply set the cookies in the session cookie jar
        :return: Nothing
        """
        self.session.cookies["over18"] = "yes"

    def is_adult(self)->bool:
        """
        Check if the cookie for adult is set.
        :return:
        """
        if 'over18' in self.session.cookies.keys():
            return self.session.cookies['over18'] == 'yes'
        return False

    def is_logged(self)->bool:
        """
        Check if the session is logged in
        :return:
        """
        return any("userl" in cookie for cookie in self.session.cookies.keys())

    def _get_favorite_page(self, subdomain:str)->Optional[BeautifulSoup]:
        """
        Given a subdomain, return a Beautiful soup object corresponding to this page
        :param subdomain: the name of the subdomain
        :return: a Beautiful Soup object
        """
        try:
            link = self.__FAVORITE_SUBDOMAIN__[subdomain]
            response = self.session.get(link, headers=self._HEADERS_)
            assert response.status_code == 200
            return BeautifulSoup(response.text, "lxml")
        except AssertionError:
            log.error("Are you sure you are logged in?")
            return None

    def _get_categories_from_favorite_page(self, favorite_page_response: BeautifulSoup)->List:
        """
        Given a beautiful soup which correspond to a subdomain, return a list of reference
        to the categories on the page
        :param favorite_page_response: BeautifulSoup
        :return: a list of reference
        """
        return [f"{self._DEFAULT_LINK}{a['href']}" for a in favorite_page_response.find("ul", {"class": "category_box"}).find_all('a')]

    def _get_novels_from_category_ref(self, category_link, subdomain)->List[ShortNovel]:
        """
        Given a category link, return a list of each novel along with the last modified date
        and the title
        :return: a list of dictionary
        """
        more_page = True
        novels_list = []
        index = 0
        try:
            while more_page & (index<self.MAX_LOOP_):
                response = self.session.get(category_link, headers= self._HEADERS_)
                assert response.status_code == 200
                category_soup = BeautifulSoup(response.text, "lxml")
                novels_list += _get_novels_from_category_page(category_soup)
                more_page, category_link = self._get_next_page(category_soup, subdomain)
                index+=1
        except AssertionError:
            log.error("Are you sure you are logged in?")
        return novels_list

    def _get_next_page(self, category_soup:BeautifulSoup, subdomain:str)->Tuple[bool, Optional[str]]:
        """
        for a favorite_page, this return a tuple which indicates if there is a next page
        and it true also return the link
        :param category_soup:
        :return:
        """
        next_page = category_soup.find('a', {'title':'next page'})
        return (next_page is not None,
        f"{self.__FAVORITE_SUBDOMAIN__[subdomain]}{next_page['href']}"
        if next_page is not None else None)

    def fetch_novels(self)->Dict[str:List[ShortNovel]]:
        """
        return for each subdomain
        :return:
        """
        novels_by_subdomain = {}
        try:
            assert self.is_logged()
        except AssertionError:
            log.error("Are you sure you are logged in?")
        for subdomain in self._SUBDOMAIN_:
            try:
                favorite_soup = self._get_favorite_page(subdomain)
                favorite_categories = self._get_categories_from_favorite_page(favorite_soup)
                novels_by_subdomain[subdomain] = []
                for category_link in favorite_categories:
                    novels_by_subdomain[subdomain] += self._get_novels_from_category_ref(category_link, subdomain)
            except Exception as e:
                log.exception(f"Exception while fetching novels on {subdomain}.")
        return novels_by_subdomain

    def get_novel_info(self, link:str)->Dict:
        """
        given a syotesu link, return a dictionary with detailed information
        :param link:
        :return:
        """
        response = self.session.get(link, headers=self._HEADERS_)
        soup = BeautifulSoup(response.text, 'lxml')
        novel_info = {
            'ncode' : soup.find('p', id='ncode').text,
            'title' : soup.find('div', id='contents_main').find_all('a')[0].text,
            'link': soup.find('div', id='contents_main').find_all('a')[0]['href']
        }

        info_tree = soup.find('div', id='infodata')

        # metadata
        metadata_tree = info_tree.find('div', id='pre_info')
        novel_info['age_limit'] = metadata_tree.find('span', id='age_limit') is not None
        novel_info['type'] = 'oneshot' if metadata_tree.find('span', id='noveltype').text == '短編' else 'webnovel'

        # novel_info
        info_table_1 = info_tree.find('table', id='noveltable1')
        rows = info_table_1.find_all('tr')
        novel_info['abstract'] = rows[0].find('td').text
        novel_info['author'] = rows[1].find('td').text
        novel_info['tags'] = rows[1].find('td').text.split(' ')

        return novel_info

    def _fetch_chapter(self, link:str) ->Chapter:
        chapter_cleaned_soup = self._get_chapter_raw(link)
        artefacts = self.resolve_artefact(chapter_cleaned_soup)
        chapter = {
            "language": "jp",
            "title": chapter_cleaned_soup.find("p", {'class':'novel_subtitle'}).text
            if chapter_cleaned_soup.find("p", {'class':'novel_subtitle'}) else "",
            "id": chapter_cleaned_soup.find("div", id="novel_no").text.split("/")[0],
            "source": link,
            "raw_content": chapter_cleaned_soup.text,
            "artefact": artefacts
        }
        return chapter

    def _split_chapter_soup_into_component(self, chapter_clean_soup)->Dict:
        return {
            "preface": chapter_clean_soup.find("div", id="novel_p"),
            "main": chapter_clean_soup.find('div', id="novel_honbun"),
            "appendix": chapter_clean_soup.find('div', id="novel_a")
        }

    def resolve_artefact(self, chapter_soup:BeautifulSoup)->Dict:
        """
        TODO
        :param chapter_soup:
        :return:
        """
        artefacts = {}
        split_chapter = self._split_chapter_soup_into_component(chapter_soup)
        list_of_images = split_chapter["main"].find_all("a")
        for image_soup in list_of_images:
            if ("href" in image_soup.keys()) & (image_soup.find("img") is not None):
                artefacts[image_soup['href']] = self.session.get(f"https{image_soup.find('img')['src']}").content
        return artefacts

    def _fetch_novel(self, novel_link:str) ->NovelInstance:
        """
        TODO
        :param url:
        :return:
        """
        # initialize output
        novel:NovelInstance = {"source": novel_link}

        # get html page
        response = self.session.get(novel_link, headers = self._HEADERS_)
        soup = BeautifulSoup(response.text, 'lxml')

        # parse novel content
        chapters = []
        index_tree = soup.find('div', {'class':'index_box'}).findChildren(recursive=False)
        if len(index_tree)>0: # serialization
            arc_id = 0
            chapter_arc = {"chapters": [], "arc_id":arc_id}
            for element in index_tree:
                if element['class'][0] == 'chapter_title':
                    if 'arc_title' in chapter_arc.keys(): #new arc
                        chapters.append(chapter_arc)
                        arc_id += 1
                        chapter_arc = {'arc_title': element.text, "chapters": [], "arc_id":arc_id}
                    else:
                        assert len(chapter_arc["chapters"]) == 0
                        chapter_arc["arc_title"] = element.text
                elif element['class'][0].startswith('novel_sublist2'):
                    chapter_link = element.find('a')['href']
                    chapter_arc['chapters'].append(self._fetch_chapter(chapter_link))

        else: # single chapter
            chapters = [self._fetch_chapter(novel_link)] # only one chapter and subchapter

        novel['chapters'] = chapters
        novel['extend'] = None
        return novel

    def _get_chapter_raw(self, url:str)->Optional[BeautifulSoup]:
        """
        return the raw soup corresponding to the chapter
        :param url:
        :return:
        """
        response = self.session.get(url, headers = self._HEADERS_)
        soup = BeautifulSoup(response.text, "lxml")
        return self._minimun_parse_raw_chapter(soup.find('div', id="novel_color"))

    def _minimun_parse_raw_chapter(self, raw_chapter:Optional[BeautifulSoup])->Optional[BeautifulSoup]:
        """
        remove the top and bottom next chapter link
        :param raw_chapter:
        :return:
        """
        for div in raw_chapter.find_all("div", {"class":"novel_bn"}):
            div.decompose()
        return raw_chapter