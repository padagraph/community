#-*- coding:utf-8 -*-

import requests
import json
from itertools import islice
""" simple botapi to post graph """

class BotError(Exception):
    pass
    
class BotApiError(BotError):
    def __init__(self, url, data, response):
        """ Function doc
        :param : 
        """
        self.message ='Something is wrong, got response code %s' % response.status_code
        self.response = response
        self.url = url
        self.data = data
        #self.json = response.json()
        message = "\n".join( [self.message,  url, str(data)])
        
        Exception.__init__(self, message) 
        
class BotLoginError(BotError):
    pass

def gen_slice(gen, chunksize):
    while True:    
        chunks = list(islice(iter(gen), chunksize))
        if chunks == []:
            break
        yield chunks

class Botagraph:
    headers={'Content-Type': 'application/json'}
    
    def __init__(self, host="http://localhost:5000", key=None, verbose=False):
        self.host = host
        self.key = None if key == "" else key
        self.verbose = verbose


    def authenticate(self, username, password):
        self.key = None

        url = "%s/auth/authenticate" % (self.host)
        payload = { 'username':username, 'password':password }

        resp = self.post(url, payload)

        print url, payload, resp.text
        if 200 == resp.status_code:
            resp = resp.json()  
            self.key = resp.get('token')

        if self.key is None:
            raise BotLoginError("I miss a valid authentification token user:'%s'" % self.username)

        print "Authentification OK %s " % self.key
    
    def post(self, url, payload={}):

        resp = requests.post(url, data=json.dumps(payload), headers=self.headers)
        
        if resp.status_code != 200:
            raise BotApiError(url, payload, resp)

        return resp

    def get(self, url):
        resp = requests.get(url)
        
        if resp.status_code != 200:
            raise BotApiError(url, {}, resp)

        return resp

    def get_schema(self, gid):
        url = "%s/graphs/g/%s/schema?token=%s" % (self.host, gid, self.key)
        resp = self.post(url)
        return resp.json()
        
    def has_graph(self, gid):
        url = "%s/graphs/g/%s?token=%s" % (self.host, gid, self.key)
        try : 
            resp = self.post(url)
            return resp.status_code is 200
        except BotApiError :
            return False

    def create_graph(self, gid, desc=""):
        url = "%s/graphs/create?token=%s" % (self.host,self.key)
        payload = { "name": gid,
                    "desc": desc
                }
        resp = self.post(url, payload)
        return resp.json()

    def get_node_by_id(self, graph, uuid):
        url = "%s/graphs/g/%s/node/%s?token=%s" % (self.host, graph, uuid, self.key)
        resp = self.get(url)
        return resp.json()

    def get_node_by_name(self, graph, uuid):
        url = "%s/graphs/g/%s/node/%s/by_name?token=%s" % (self.host, graph, uuid, self.key)
        resp = self.get(url)
        return resp.json()
        
    def _post_one(self, obj_type, gid, payload):
        url = "%s/graphs/g/%s/%s?token=%s" % (self.host, gid, obj_type, self.key)
        resp = self.post(url, payload)
        
        return resp.json()

    def _post_multi(self, obj_type, gid, objs ):
        url = "%s/graphs/g/%s/%s?token=%s" % (self.host, gid, obj_type, self.key)
        for chunks in gen_slice(objs, 100):
            payload = { "%s" % obj_type: chunks }
            #
            if self.verbose:
                print "POST %s, %s " % (url,len(chunks))
            resp = self.post(url, payload)

            data = resp.json()
            results = { i:uuid for i, uuid in data['results'] }

            for i, obj in enumerate(chunks):
                yield obj, results.get(i, None) 
        
    def post_node_type(self, gid, name, properties):
        payload = { 'node_type': name,
                    'properties': properties
                   }
        resp = self._post_one( "node_type", gid, payload )
        return resp['uuid']
        
    def post_edge_type(self, gid, name, properties):
        payload = { 'edge_type' : name,
                    'properties': properties
                   }
        resp = self._post_one( "edge_type", gid, payload )
        
        return resp['uuid']
        
    def post_node(self, gid, payload):
        return self._post_one( "node", gid, payload )
         
    def post_edge(self, gid, payload):
        return self._post_one( "edge", gid, payload )
        

    def post_nodes(self, gid, nodes ):
        for v in self._post_multi("nodes", gid, nodes ):
            yield v

    def post_edges(self, gid, edges ):
        for v in self._post_multi("edges", gid, edges ):
            yield v

    
    def find_nodes(self, graph_name, nodetype_name, properties, start=0, size=100):
        """ iterate nodes of one type , filters on properties matching '==' 
        :param graph: graph name
        :param nodetype_name: node_type name
        :param properties: dict of key:value node should match
        :param start: pagination start
        :param size:  resultset size ( may be shorten by server )

             
        """
        url = "%s/graphs/g/%s/nodes/find?token=%s" % (self.host, graph_name, self.key)
        payload = {
                "start": start,
                "size" : size,
                "node_type" : nodetype_name,
                "properties" : properties
        }
        resp = self.post(url, payload)
        data = resp.json()

        for v in data['nodes']:
            yield v
        
    def find_all_nodes(self, graph_name, nodetype_name, properties):
        """
        like find nodes makes a complete iteration of the nodes matching node_type and properties
            :see: find_nodes
        """
        start=0
        size=100
        while True:
            nodes = list( self.find_nodes(graph_name, nodetype_name, properties, start, size))
            if not len(nodes) :
                break
            start += size
            for node in nodes:
                yield node

    def get_neighbors(self, graph, node ):
        """ return neighbors of a node
        :param graph: graph name  
        :param node: node uuid  
        """
        url = "%s/graphs/g/%s/node/%s/neighbors?token=%s" % (self.host, graph, node, self.key)
        resp = self.post(url, {})
        return resp.json()['neighbors']
        
    def count_neighbors(self, graph, node ):
        """ Function doc
        :param : 
        """
        url = "%s/graphs/g/%s/node/%s/neighbors/count?token=%s" % (self.host, graph, node, self.key)
        resp = self.post(url, {})
        return resp.json()['neighbors']

    def prox(self, graph, pzeros, weights=[], filter_edges=[], filter_nodes=[], step=3, limit=100):
        url = "%s/graphs/g/%s/proxemie?token=%s" % (self.host, graph, self.key)
        payload =  {
            'p0' : pzeros,
            'weights': weights, 
            'filter_nodes' : filter_nodes , 
            'filter_edges' : filter_edges , 
            'limit': limit, 
            'step':step, 
        }

        resp = self.post(url, payload)
        
        return resp.json()

    def get_subgraph(graph, nodes_uuids):
        url = "%s/graphs/g/%s/subgraph?token=%s" % (self.host, graph, self.key)
        payload =  {
            'graph' : graph,
            'uuids': nodes_uuids,
        }
            
        resp = self.post(url, payload)
        return resp.json()
        