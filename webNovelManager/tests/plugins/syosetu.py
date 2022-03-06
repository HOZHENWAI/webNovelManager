from webNovelManager.plugins.syosetu import Syosetu
import pytest



class Test_Syosetu():
    EXAMPLE_URL = [
        "https://ncode.syosetu.com/n9669bk/",
        "https://ncode.syosetu.com/n7975cr/",
        "https://novel18.syosetu.com/n3271bm/"
    ]

    plugin_instance = Syosetu()

    @pytest.mark.parametrize("url", EXAMPLE_URL)
    def test_url(self,url):
        assert self.plugin_instance.isPluginRelevant(url)

    def test_canfindlogin(self):
        assert self.plugin_instance._get_credentials() is not None

    def test_login(self):
        assert self.plugin_instance.login()