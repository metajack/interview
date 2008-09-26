from twisted.web import server, resource, static
from twisted.application import service, internet

import palin
import config

words, word_map = palin.setup()



root = palin.Interview(words, word_map, config.palin)
site = server.Site(root)

application = service.Application("interview")
internet.TCPServer(8000, site).setServiceParent(application)
