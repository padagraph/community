#-*- coding:utf-8 -*-

import requests
import json
from itertools import islice
""" simple botapi to post graph """

class BotError(Exception):
    pass
class BotLoginError(Exception):
    pass

def slice(gen, chunksize):
    while True:    
        chunks = list(islice(gen, chunksize))
        if chunks == []:
            break
        yield chunks

class PadaBot:
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
            return self.key is not None
            
        raise BotLoginError('Login error %s' % self.username)

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
         
    def post_nodes(self, gid, nodes ):
        url = "%s/graphs/g/%s/nodes?token=%s" % (self.host, gid, self.key)
        for chunks in slice(nodes, 100):
            payload = { "nodes":chunks }
            resp = requests.post(url, data=json.dumps(payload), headers=self.headers)

            if resp.status_code != 200:
                raise  BotError("%s" % resp.status_code)

            data = resp.json()
            for v in data['results']:
                yield v
         
    def post_edge(self, gid, payload):
        url = "%s/graphs/g/%s/edge?token=%s" % (self.host, gid, self.key)
        return requests.post(url, data=json.dumps(payload), headers=self.headers)

    def save(self):
        """ save the current data   """
        url = "%s/graphs/save?token=%s" % (self.host, self.key)
        return requests.get(url, headers=self.headers)

      