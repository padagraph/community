#-*- coding:utf-8 -*-

import sys
import time   
import argparse
from random import randint

import igraph

from reliure.types import * 


from botapi import Botagraph, BotApiError


def node_payload(vertex, nodetype):
    return {
            'nodetype': nodetype,
            'properties': { 
                'label': vertex['label'],
                'lang':'fr',
                
            }
          }

def edge_payload(edgetype, src, tgt, properties):
    return {
        'edgetype': edgetype,
        'source': src,
        'label' : "is_syn",
        'target': tgt,
        'properties': properties
    }

def gen_nodes(graph, nodetype):
    for vertex in graph.vs:
        yield node_payload(vertex, nodetype)

def gen_edges(graph, edgetype, idx):
    for edge in graph.es:
        src = graph.vs[edge.source]['label']
        src = idx[src]

        tgt = graph.vs[edge.target]['label']
        tgt = idx[tgt]
        
        yield edge_payload( edgetype, src, tgt, edge.attributes() )
        

def main():
    """ re-Index all the Proxteam corpus """
    from pprint import pprint
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")

    parser.add_argument("--key" , action='store', help="authentification token", default=None)
    parser.add_argument("--username" , action='store', help="user", default=None)
    parser.add_argument("--password" , action='store', help="pwd", default=None)

    parser.add_argument("--path", action='store', help="path", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)

    parser.add_argument("--infos", action='store_true', help="prints graph infos and exit" )
    

    parser.add_argument("--cut", action='store', help="cut threathold. 0 no cut ", default=0)
    parser.add_argument("--seed", action='store_true', help="seeds make beautiful flowers " )
    parser.add_argument("--wait", action='store_true', help="confirm node/edges importation " )
    parser.add_argument("--pause", action='store', help="pause time in ms between insert ", default=0, type=int )
    
    args = parser.parse_args()

    # Bot creation & login 
    print "\n * Connecting to graph %s @ %s \n  " % (args.gid, args.host)
    bot = Botagraph(args.host, args.key)
    gid =  args.gid

    if args.username and args.password:
        bot.authenticate(args.username, args.password)

    if args.infos:
        pprint( bot.get_graph(gid) )
        return 


    # read / parse graph
    print "\n * Reading %s" % args.path
    
    graph = igraph.read(args.path)
    vs = list( (v.index, v.degree() ) for v in  graph.vs )

    # subgraph
    if args.cut > 0:
        # cut method based on degree
        n = int(args.cut)
        print " ** cut %s" % args.cut
        vs = sorted( vs, key=lambda x: x[1], reverse = True )
        vs = vs[:n]
        
        graph = graph.subgraph( [  v[0] for v in vs ] )

    print graph.summary()
    graph.es['a'] = [ 1 for i in xrange(graph.vcount() ) ]


    
    if not bot.has_graph(gid) :
        print "\n * Create graph %s" % gid
        bot.create_graph(gid, { 'description':"Dicosyn experiment\n * ",
                                'image': "",
                                'tags': ['synonymes', 'dictionnaire']
                              }
                        )
                        
    print "\n * Get schema '%s'" % gid
    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print "\n nodetypes: ", nodetypes.keys()
    print "\n edgetypes: ", edgetypes.keys()

    if not "word" in nodetypes:
         
        print "\n\n * Creating node type %s" % "word"
        props = { "label" : Text(),
                  "lang"  : Text()
                }
        bot.post_nodetype(gid, "word",  "no description", props)

    if not "is_syn" in edgetypes:
        print "\n\n * Creating edge type %s" % "is_syn"
        bot.post_edgetype(gid, "is_syn", "no desc", {"a":Text()})

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print nodetypes
    print edgetypes

    idx = {}

    if args.wait :
        raw_input("press <enter> key to start edges and nodes importation") 

    if args.seed: 

        def set_node(v):
            if v['label'] not in idx:
               node = bot.post_node(gid, node_payload(v, nodetypes['word']['uuid']))
               idx[ v['label'] ] = node['uuid']
               print "inserting %s %s" % (v['label'] , node['uuid'])

        idx = {}
        v1 = None

        # seeds grow into beautiful flowers 
        
        while graph.vcount() > 0:
            
            v1 = graph.vs[0] if v1 is None else v1
            
            size = graph.vcount()

            nei = v1.neighbors()
            if not len(nei):
                graph.delete_vertices([v1.index])
                v1 = None
                continue

            for i in range( min([5,len(nei)]) ):

                nei = v1.neighbors()
                
                if i >= len(nei):
                    if graph.vcount():
                        r = randint(0,graph.vcount()-1)
                        v1 = graph.vs[r]
                    break
                
                r = randint(0,len(nei)-1)
                v2 = nei[r]
                
                print "inserting edge %s %s" % (v1['label'] , v2['label'])

                set_node(v1)
                set_node(v2)

                eid = graph.get_eid(v1.index, v2.index)
                src, tgt = idx[v1['label']], idx[v2['label']]
                
                uuid = bot.post_edge(gid, edge_payload(edgetypes['is_syn']['uuid'], src, tgt, {}))

                # delete  from graph
                # * inserted edges
                # * nodes with no more edges 
                
                graph.delete_edges([eid])

                delete_nodes =  [ v.index for v in (v1, v2) if len(graph.neighbors(v)) == 0 ]

                if len(delete_nodes):
                    graph.delete_vertices(delete_nodes)
                    
                    if graph.vcount():
                        r = randint(0,graph.vcount()-1)
                        # switch v1
                        v1 = graph.vs[r]

                    else: break

                    
            # wait sometimes
            pause(args.pause)

            
            
            
    else :

        print "posting nodes"
        count = 0
        fail = 0
        for node, uuid in bot.post_nodes( gid, gen_nodes(graph, nodetypes['word']['uuid']) ):
            if not uuid:
                fail += 1
            else :
                count += 1
                idx[node['properties']['label']] = uuid
            
        print "%s nodes inserted " % count
        
        #print "iterate over nodes"
        #for node in bot.find_all_nodes(gid, "word", {}):
            #pass

        # post edges
        print "posting edges"
        count = 0
        fail = 0

        inv_idx = { v:k for k,v in idx.iteritems() }
        
        for obj, uuid in bot.post_edges( gid, gen_edges(graph, edgetypes['is_syn']['uuid'], idx) ):
            if not uuid:
                fail += 1
            else :
                count += 1

            # wait sometimes    
            pause(args.pause)
            
        print "%s edges inserted, %s failed " % (count, fail)


def pause(waitms):
    if waitms > 0:
        if randint(1,12) == 1:
            # waiting time is given in ms
            time.sleep(waitms/1000)
    
if __name__ == '__main__':
    sys.exit(main())
