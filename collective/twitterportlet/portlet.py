from zope.interface import implements
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from zope import schema
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.twitterportlet import TwitterPortletMessageFactory as _
from plone.memoize.instance import memoize
import twitter
import re

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
        

def expand_tweet(str):
    """This method takes a string, parses it for URLs, hashtags and mentions
       and returns a hyperlinked string."""
       
    str = re.sub(urlsRegexp, '<a href="\g<1>">\g<1></a>', str)
    str = re.sub(hashRegexp, '<a href="http://twitter.com/search?q=%23\g<1>">#\g<1></a>', str)
    str = re.sub(atRegexp, '<a href="http://twitter.com/\g<1>">@\g<1></a>', str) 
    str = re.sub(emailRegexp, '<a href="mailto:\g<1>">\g<1></a>', str) 
    return str

class ITwitterPortlet(IPortletDataProvider):
    """A twitter portlet"""

    name = schema.TextLine(
        title=_(u"Title"),
        description=_(u"The title of the portlet")
    )

    username = schema.TextLine(
        title=_(u"Username"),
        description=_(u"The tweets of this user will be shown")
    )

    count = schema.Int(
        title=_(u'Number of items to display'),
        description=_(u'How many items to list.'),
        required=True,
        default=5
    )


class Assignment(base.Assignment):
    """Portlet assignment"""

    implements(ITwitterPortlet)

    def __init__(self, name=u"", username=u"", count=5):
        self.name = name
        self.username = username
        self.count = 5

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
    
    @memoize
    def get_tweets(self):
        username = self.data.username
        limit = self.data.count
        twapi = twitter.Api()
        return twapi.GetUserTimeline(username, count=limit)

class AddForm(base.AddForm):
    """Portlet add form"""
    
    form_fields = form.Fields(ITwitterPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form"""
    
    form_fields = form.Fields(ITwitterPortlet)
