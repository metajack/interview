from twisted.web import server, resource, static
from twisted.application import service, internet

import palin

words, word_map = palin.setup()


root = palin.PalinTalk(words, word_map)
site = server.Site(root)

application = service.Application("palin")
internet.TCPServer(8000, site).setServiceParent(application)
