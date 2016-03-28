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
        error = response.text
        print "!! ERROR !! ", error
        Exception.__init__(self, message) 
        
class BotLoginError(BotError):
    def __init__(self, message):
        super(BotLoginError, self).__init__(message)
    

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
        self.verbose = verbose

        self.key = None if key == "" else key
        # try to connect  
        if self.key:
            url = "account/me"
            resp = self.get(url)
            
    def _send(self, method, url, payload={}):
    
        if self.key is None:
            raise BotLoginError("I miss a valid authentification token")

        url = "%s/%s" %(self.host, url)
        headers = {"Authorization" : self.key}

        if method == "GET":
            resp = requests.get(url, headers=headers)
        if method == "DELETE":
            resp = requests.delete(url, headers=headers)
        if method == "POST":
            resp = requests.post(url, json=payload, headers=headers)
        if method == "PUT":
            resp = requests.put(url, data=payload, headers=headers)
        
        if 401 == resp.status_code:
            raise BotLoginError('Invalid credentials') 

        elif resp.status_code != 200:
            raise BotApiError(url, payload, resp)

        return resp
        
    def post(self, url, payload={}):
        return self._send("POST", url, payload)
        
    def put(self, url, payload={}):
        return self._send("PUT", url, payload)
        
    def get(self, url):
        return self._send("GET", url)

    def delete(self, url):
        return self._send("DELETE", url)

    def _post_one(self, obj_type, gid, payload):
        url = "graphs/g/%s/%s" % (gid, obj_type)
        resp = self.post(url, payload)
        
        return resp.json()

    def _post_multi(self, obj_type, gid, objs ):
        url = "graphs/g/%s/%s" % (gid, obj_type)
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
        
        
    def authenticate(self, email, password):
        self.key = None

        url = "account/authenticate"
        payload = { 'email':email, 'password':password }

        resp = self.post(url, payload)
        
        print url, payload, resp.text
            
        if 200 == resp.status_code:
            resp = resp.json()  
            self.key = resp.get('token')

        print ("Authentification OK ")



    def get_schema(self, gid):
        url = "graphs/g/%s/schema" % gid
        resp = self.post(url)
        return resp.json()
        
    def has_graph(self, gid):
        g = self.get_graph(gid)
        print "has graph " , g
        try : 
            g['name']
            return True
        except:
            return False

        
    def get_graph(self, gid):
        url = "graphs/g/%s" % (gid)
        try : 
            resp = self.get(url)
            g = resp.json()
            return g[gid]
        except  :
            return None

    def create_graph(self, gid, props):

        url = "graphs/create"
        payload = { "name": gid,
                    "description": props.get('description', ""),
                    "tags": props.get('tags', []),
                    "image": props.get('image', ""),
                }
        resp = self.post(url, payload)
        print url, resp.text
        return resp.json()

    def get_node_by_id(self, gid, uuid):
        url = "graphs/g/%s/node/%s" % (gid, uuid)
        resp = self.get(url)
        return resp.json()

    def get_node_by_name(self, gid, uuid):
        url = "graphs/g/%s/node/%s/by_name" % (gid, uuid)
        resp = self.get(url)
        return resp.json()
        
    def create_nodetype(self, gid, name, desc,  properties):
        return self.post_nodetype( gid, name, desc,  properties)
        

    def post_nodetype(self, gid, name, desc,  properties):
        payload = { 'name': name,
                    'description' : desc,
                    'properties': { k: v.as_dict() for k,v in properties.iteritems() }
                  }
        print payload
        resp = self._post_one( "nodetype", gid, payload )

        return resp['uuid']
        
    def post_edgetype(self, gid, name, desc,  properties):
        payload = { 'name' : name,
                    'description': desc,
                    'properties': { k: v.as_dict() for k,v in properties.iteritems() }
                  }
                   
        resp = self._post_one( "edgetype", gid, payload )
        
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

    
    def delete_edge(self, gid, eid):
        url = "graphs/g/%s/edge/%s" % (gid, eid)
        self.delete(url)
        
    def delete_node(self, gid, nid):
        url = "graphs/g/%s/node/%s" % (gid, nid)
        self.delete(url)

        
    def find_nodes(self, gid, nodetype_uuid, properties, start=0, size=100):
        """ iterate nodes of one type , filters on properties matching '==' 
        :param graph: graph name
        :param nodetype_name: nodetype name
        :param properties: dict of key:value node should match
        :param start: pagination start
        :param size:  resultset size ( may be shorten by server )

             
        """
        url = "graphs/g/%s/nodes/find" % (gid)
        payload = {
                "start": start,
                "size" : size,
                "nodetype" : nodetype_uuid,
                "properties" : properties
        }
        resp = self.post(url, payload)
        data = resp.json()

        for v in data['nodes']:
            yield v
        
    def find_all_nodes(self, gid, nodetype_uuid, properties, start=0, size=100):
        """
        like find nodes makes a complete iteration of the nodes matching node_type and properties
            :see: find_nodes
        """
        start =   0 if size < 0 else start
        size  = 100 if size > 100 else size

        while True:
            nodes = list( self.find_nodes(gid, nodetype_uuid, properties, start, size))
            if not len(nodes) :
                break
            start += size
            for node in nodes:
                yield node

    def iter_neighbors(self, gid, nodeuuid, start=0, size=100):
        """ return neighbors of a node
        :param graph: graph name  
        :param node: node uuid  
        """
        start =   0 if size < 0 else start
        size  = 100 if size > 100 else size

        url = "graphs/g/%s/node/%s/neighbors" % (gid, nodeuuid)

        while True:
            payload = {
                "start": start,
                "size" : size,
            }

            resp = self.post(url, payload)
            neighbors = resp.json()['neighbors']

            for v in neighbors:
                yield v
            
            if not len(neighbors) :
                break

            start += size
            
        
    def count_neighbors(self, gid, node ):
        """ Function doc
        :param : 
        """
        url = "graphs/g/%s/node/%s/neighbors/count" % (gid, node)
        resp = self.post(url, {})
        return resp.json()['neighbors']

    def prox(self, graph, pzeros, weights=[], filter_edges=[], filter_nodes=[], step=3, limit=100):
        url = "graphs/g/%s/proxemie" % graph
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

    def get_subgraph(gid, nodes_uuids):
        url = "graphs/g/%s/subgraph" % gid
        payload =  {
            'graph' : graph,
            'uuids': nodes_uuids,
        }
            
        resp = self.post(url, payload)
        return resp.json()
        