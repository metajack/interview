# interview.tac
# -*- mode: python -*-
#
# This setups on the twisted.web site.
#
# Name vhosts are used to get to the different sites, and they are
# also available under /palin, /mccain, /obama, and /biden.

import signal

from twisted.web import server, resource, vhost, static
from twisted.application import service, internet

from interview import Interview

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

# about page
about = static.File('about.html')
root.default.putChild('about', about)

# palin
palin = Interview('palin')
palin.putChild('about', about)
root.default.putChild('palin', palin)
root.addHost('interviewpalin.com', palin)
root.addHost('www.interviewpalin.com', palin)

# mccain
mccain = Interview('mccain')
mccain.putChild('about', about)
root.default.putChild('mccain', mccain)
root.addHost('interviewmccain.com', mccain)
root.addHost('www.interviewmccain.com', mccain)

# biden
biden = Interview('biden')
biden.putChild('about', about)
root.default.putChild('biden', biden)
root.addHost('interviewbiden.com', biden)
root.addHost('www.interviewbiden.com', biden)

# obama
obama = Interview('obama')
obama.putChild('about', about)
root.default.putChild('obama', obama)
root.addHost('interviewobama.com', obama)
root.addHost('www.interviewobama.com', obama)

site = server.Site(root)

application = service.Application("interview")
internet.TCPServer(80, site).setServiceParent(application)


# setup signals

def onHup(*args):
    for persona in [palin, mccain, biden, obama]:
	persona.reload()

signal.signal(signal.SIGHUP, onHup)
    
    
