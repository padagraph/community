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

class Botagraph:
    headers={'Content-Type': 'application/json'}
    
    def __init__(self, host, key):
        self.host = host
        self.key = None if key == "" else key

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
                raise BotLoginError("I miss a valid authentification token user:'%s'" % self.username)

    def create_graph(self, gid, desc=""):
        url = "%s/graphs/create?token=%s" % (self.host,self.key)
        payload = { "name": gid,
                    "desc": desc
                }
        return requests.post(url, data=json.dumps(payload), headers=self.headers)
        
    def _post_one(self, obj_type, gid, payload):
        url = "%s/graphs/g/%s/%s?token=%s" % (self.host, gid, obj_type, self.key)
        return requests.post(url, data=json.dumps(payload), headers=self.headers)

    def post_node_type(self, gid, name, properties):
        payload = { 'node_type': name,
                    'properties': properties
                   }
        return self._post_one( "node_type", gid, payload )

    def post_node(self, gid, payload):
        return self._post_one( "node", gid, payload )
         
    def post_edge_type(self, gid, name, properties):
        payload = { 'edge_type' : name,
                    'properties': properties
                   }
        return self._post_one( "edge_type", gid, payload )
        
    def post_edge(self, gid, payload):
        return self._post_one( "edge", gid, payload )
        
    def _post_multi(self, obj_type, gid, objs ):
        url = "%s/graphs/g/%s/%s?token=%s" % (self.host, gid, obj_type, self.key)
        for chunks in slice(objs, 100):
            payload = { "%s" % obj_type:chunks }
            resp = requests.post(url, data=json.dumps(payload), headers=self.headers)

            if resp.status_code != 200:
                raise  BotError("%s" % resp.status_code)

            data = resp.json()
            for v in data['results']:
                yield v

    def post_nodes(self, gid, nodes ):
        for v in self._post_multi("nodes", gid, nodes ):
            yield v

    def post_edges(self, gid, edges ):
        for v in self._post_multi("edges", gid, edges ):
            yield v

    def save(self):
        """ save the current data   """
        url = "%s/graphs/save?token=%s" % (self.host, self.key)
        return requests.get(url, headers=self.headers)

      