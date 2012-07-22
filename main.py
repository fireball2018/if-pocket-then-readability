#!/usr/bin/env python
# encoding: utf-8

from __future__ import division

import time
import logging
import math
import urllib
import json

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import urlfetch

import settings

class MainHandler(webapp.RequestHandler):
    """docstring for MainHandler"""
    
    def get(self):
        """docstring for get"""

        self.response.out.write("ok")

class SyncHandler(webapp.RequestHandler):
    """docstring for SyncHandler"""
    
    def get(self):
        """docstring for get"""

        assert settings.mail_sender
        assert settings.readability_mail
        assert settings.pocket_apikey
        assert settings.pocket_username
        assert settings.pocket_password

        since = memcache.get("last_sync")
        memcache.set("last_sync", int(time.time()))

        if not since:
            since = 0

        urls = self.pocket_get(since)

        if urls and len(urls) > 0:

            limit = 20
            slices = int(math.ceil(len(urls)/limit))

            for i in xrange(0, slices):

                items = urls[i*limit:(i+1)*limit]

                mail.send_mail(sender = settings.mail_sender,
                                to = settings.readability_mail,
                                subject = "add items",
                                body = "\n".join(items))

        self.response.out.write("synced %s items" % len(urls))

    def pocket_get(self, since=0):

        data = {
            "apikey":settings.pocket_apikey,
            "username":settings.pocket_username,
            "password":settings.pocket_password
        }

        if since > 0:
            data['since'] = since

        urls = []

        result = urlfetch.fetch("https://readitlaterlist.com/v2/get", 
                                payload = urllib.urlencode(data), 
                                method = urlfetch.POST)

        if result and result.status_code == 200 \
            and result.content:

            response = json.loads(result.content)

            if 'status' in response and response['status'] == 1 \
                and 'list' in response and type(response['list']) is dict:

                for (id, item) in response['list'].items():
                    urls.append(item['url'])

        return urls

def main():
    logging.getLogger().setLevel(logging.INFO)
    application = webapp.WSGIApplication([
                        ('/', MainHandler),
                        ('/sync', SyncHandler),
                    ], debug=True)

    webapp.util.run_wsgi_app(application)

if __name__ == '__main__':
    main()