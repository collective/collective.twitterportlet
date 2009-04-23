from zope.interface import implements
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from zope import schema
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.twitterportlet import TwitterPortletMessageFactory as _
from plone.memoize.instance import memoize
import twitter


class ITwitterPortlet(IPortletDataProvider):
    """A twitter portlet"""

    name = schema.TextLine(title=_(u"Title"),
                           description=_(u"The title of the portlet"))

    username = schema.TextLine(title=_(u"Username"),
                               description=_(u"The tweets of this user will be shown"))

    count = schema.Int(title=_(u'Number of items to display'),
                       description=_(u'How many items to list.'),
                       required=True,
                       default=5)


class Assignment(base.Assignment):
    """Portlet assignment"""

    implements(ITwitterPortlet)

    def __init__(self, name=u"", username=u"", count=5):
        self.name = name
        self.username = username
        self.count = 5


class Renderer(base.Renderer):
    """Portlet renderer"""

    render = ViewPageTemplateFile('portlet.pt')

    @property
    def title(self):
        return self.data.name or _(u"Latest tweets")
    
    @property
    def available(self):
        return len(self.get_tweets())
    
    @memoize
    def get_tweets(self):
        username = self.data.username
        limit = self.data.count
        twapi = twitter.Api()
        return twapi.GetUserTimeline(username)[:limit]


class AddForm(base.AddForm):
    """Portlet add form"""
    form_fields = form.Fields(ITwitterPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form"""
    form_fields = form.Fields(ITwitterPortlet)
