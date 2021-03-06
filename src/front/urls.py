import cyclone.web
import api_doc
from twisted.internet.tcp import _AbortingMixin
from wiapi import api_manager
from front.handlers import home
# from front.debug import gmprod
# from front.debug import gmaccount
from front.debug import gmhero
# from front.handlers import pay
from local_settings import DEBUG

url_patterns = [
    (r'/gm/', home.HomeHandler),
    (r'/', home.IndexHandler),
    # (r'/startup/', home.StartupHandler),
    # (r'/sync/', home.SyncHandler),
    # (r'/guide/', guide.GuideHandler),
    # (r'/syncdb/', home.SyncdbHandler),
    # (r'/flushdb/', home.FlushdbHandler),

    # gm tools
    # (r'/gm/account/edit/', gmaccount.EditHandler),
    # (r'/gm/prod/edit/', gmprod.EditProdHandler),


    (r'/crossdomain\.xml', home.CrossdomainHandler),
    (r'/crossdomain\.xml', cyclone.web.RedirectHandler,
     {'url': '/static/crossdmain.xml'}),
]
if DEBUG == True:
    apiurls = api_manager.get_urls() + url_patterns + [(r"/doc$", api_doc.ApiDocHandler), (r"/map$", api_doc.ApiMapHandler),]
else:
    apiurls = url_patterns