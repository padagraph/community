#-*- coding:utf-8 -*-

import requests
import json

""" simple botapi to post graph """

class Botapi:
    headers={'Content-Type': 'application/json'}
    
    def __init__(self, host, key):
        self.host = host
        self.key = key

    def authenticate(self, username, password):
        self.key = None
        self.username = username
        self.password = password
        url = "%s/auth/authenticate" % (self.host)
        payload = { 'username':username, 'password':password }
        resp = requests.post(url, data=json.dumps(payload), headers=self.headers)

        if 200 == resp.status_code:
            resp = resp.json()  
            self.key = resp.get('token')
        
        if self.key is None:
            raise ValueError('Login error')

    def create_graph(self, gid, desc=""):
        url = "%s/graphs/create?token=%s" % (self.host,self.key)
        payload = { "name": gid,
                    "desc": desc
                }
        return requests.post(url, data=json.dumps(payload), headers=self.headers)
        
        
    def _post_type(self, obj_type, gid, name, properties):
        url = "%s/graphs/g/%s/%s?token=%s" % (self.host, gid, obj_type, self.key)
        payload = { '%s' % obj_type: name,
                    'properties': properties
                   }
        return requests.post(url, data=json.dumps(payload), headers=self.headers)

    def post_node_type(self, gid, name, properties):
        return self._post_type( "node_type", gid, name, properties )

    def post_edge_type(self, gid, name, properties):
        return self._post_type( "edge_type", gid, name, properties )
        
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

      