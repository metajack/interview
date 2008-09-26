# interview.tac
# -*- mode: python -*-
#
# This setups on the twisted.web site.
#
# Name vhosts are used to get to the different sites, and they are
# also available under /palin, /mccain, /obama, and /biden.

from twisted.web import server, resource, vhost
from twisted.application import service, internet

import interview
import config

words, word_map = interview.setup()

root = vhost.NameVirtualHost()

class DefaultRoot(resource.Resource):
    isLeaf = False

    def getChild(self, name, request):
	if name == '':
	    return self

	return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
	return ""

# default
root.default = DefaultRoot()

# palin
palin = interview.Interview(words, word_map, config.palin)
root.default.putChild('palin', palin)
root.addHost('interviewpalin.com', palin)

# mccain
mccain = interview.Interview(words, word_map, None)
root.default.putChild('mccain', mccain)
root.addHost('interviewmccain.com', mccain)

# biden
biden = interview.Interview(words, word_map, None)
root.default.putChild('biden', biden)
root.addHost('interviewbiden.com', biden)

# obama
obama = interview.Interview(words, word_map, None)
root.default.putChild('obama', obama)
root.addHost('interviewobama.cmo', obama)

site = server.Site(root)

application = service.Application("interview")
internet.TCPServer(8000, site).setServiceParent(application)
