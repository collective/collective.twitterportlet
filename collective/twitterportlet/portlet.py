import re
import socket
from urllib2 import URLError

import twitter
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from zope.formlib import form
from zope.interface import implements
from zope import schema
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.twitterportlet import TwitterPortletMessageFactory as _


TWITTER_URL = 'http://twitter.com/'

# Match and capture urls
urlsRegexp = re.compile(r"""
    (
    # Protocol
    http://
    # Alphanumeric, dash, slash or dot
    [A-Za-z0-9\-/.]*
    # Don't end with a dot
    [A-Za-z0-9\-/]+
    )
    """, re.VERBOSE)

# Match and capture #tags
hashRegexp = re.compile(r"""
    # Hash at start of string or after space, followed by at least one
    # alphanumeric or dash
    (?:^|(?<=\s))\#([A-Za-z0-9\-]+)
    """, re.VERBOSE)

# Match and capture @names
atRegexp = re.compile(r"""
    # At symbol at start of string or after space, followed by at least one
    # alphanumeric or dash
    (?:^|(?<=\s))@([A-Za-z0-9\-]+)
    """, re.VERBOSE)

# Match and capture email address
emailRegexp = re.compile(r"""
    # Email at start of string or after space
    (?:^|(?<=\s))([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})\b
    """, re.VERBOSE|re.IGNORECASE)

DEFAULT_TIMEOUT = socket.getdefaulttimeout()


def expand_tweet(str):
    """This method takes a string, parses it for URLs, hashtags and mentions
       and returns a hyperlinked string."""

    str = re.sub(urlsRegexp, '<a href="\g<1>">\g<1></a>', str)
    str = re.sub(hashRegexp,
        '<a href="http://twitter.com/search?q=%23\g<1>">#\g<1></a>', str)
    str = re.sub(atRegexp,
        '<a href="http://twitter.com/\g<1>">@\g<1></a>', str)
    str = re.sub(emailRegexp, '<a href="mailto:\g<1>">\g<1></a>', str)
    return str


class ITwitterPortlet(IPortletDataProvider):
    """A twitter portlet"""

    name = schema.TextLine(
        title=_(u"Title"),
        description=_(u"The title of the portlet"))

    username = schema.TextLine(
        title=_(u"Username"),
        description=_(u"The tweets of this user will be shown"))

    count = schema.Int(
        title=_(u'number of items to display'),
        description=_(u'how many items to list.'),
        required=True,
        default=5)

    link_to_profile_url = schema.Bool(
        title=_(u'Link to user\'s profile?'),
        description=_(u"If selected, portlet header will link to the "
                      u"user's Twitter page."),
        required=True,
        default=True)


class Assignment(base.Assignment):
    """Portlet assignment"""

    implements(ITwitterPortlet)

    def __init__(self, name=u"", username=u"", count=5,
                 link_to_profile_url=True):
        self.name = name
        self.username = username
        self.count = count
        self.link_to_profile_url = link_to_profile_url

    @property
    def title(self):
        return _(u"Twitter")


class Renderer(base.Renderer):
    """Portlet renderer"""

    render = ViewPageTemplateFile('portlet.pt')

    @property
    def title(self):
        return self.data.name or _(u"Latest tweets")

    @property
    def available(self):
        return True

    def expand(self, str):
        return expand_tweet(str)

    def get_tweets(self):
        username = self.data.username
        limit = self.data.count
        # Ugly workaround for a missing timeout handling in the
        # python-twitter library, see:
        # http://code.google.com/p/python-twitter/issues/detail?id=92
        timeout = socket.getdefaulttimeout()
        # Try to deal with multi-threading in some basic crude way.
        # If we get our own "marker timeout", this code is called in a
        # different thread before the timeout could be reset again. Fall
        # back on the global timeout at import time. Using a thread lock
        # won't help, as other code in other threads could change the same
        # global value
        if timeout == 61.3:
            timeout = DEFAULT_TIMEOUT
        try:
            socket.setdefaulttimeout(61.3) # seconds as floating point number
            twapi = twitter.Api()
            try:
                tweets = twapi.GetUserTimeline(username, count=limit)
            except (URLError, twitter.TwitterError, socket.timeout):
                tweets = None
        finally:
            socket.setdefaulttimeout(timeout)
        return tweets

    def profile_url(self):
        return TWITTER_URL + self.data.username


class AddForm(base.AddForm):
    """Portlet add form"""

    form_fields = form.Fields(ITwitterPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form"""

    form_fields = form.Fields(ITwitterPortlet)
