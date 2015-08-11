#-*- coding:utf-8 -*-

import requests
import json

""" simple botapi to post graph """

class Botapi:
    headers={'Content-Type': 'application/json'}
    def __init__(self, host, key):
        self.host = host
        self.key = key

    def create_graph(self, gid, desc=""):
        url = "%s/graphs/create?token=%s" % (self.host,self.key)
        payload = { "name": gid,
                    "desc": desc
                }
        return requests.post(url, data=json.dumps(payload), headers=self.headers)
        
        
    def post_node(self, gid, payload):
        url = "%s/graphs/g/%s/node?token=%s" % (self.host, gid, self.key)
        return requests.post(url, data=json.dumps(payload), headers=self.headers)
         
    def post_edge(self, gid, payload):
        url = "%s/graphs/g/%s/edge?token=%s" % (self.host, gid, self.key)
        return requests.post(url, data=json.dumps(payload), headers=self.headers)

    def save(self):
        """ save the current data   """
        url = "%s/graphs/save?token=%s" % (self.host, self.key)
        return requests.get(url, headers=self.headers)

      