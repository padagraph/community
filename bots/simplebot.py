#-*- coding:utf-8 -*-

import sys
import argparse
import igraph


from botapi import Botagraph, BotApiError


def gen_nodes(graph):
    for v in graph.vs:
        payload = {
                    'node_type': 'word',
                    'properties': { 
                        'label': v['label'],
                        'lang':'fr'
                    }
                }
        yield payload

def gen_edges(graph, idx):
    for e in graph.es:
        src = graph.vs[e.source]['label']
        tgt = graph.vs[e.target]['label']
        label = "is_syn"
        
        payload = {
            'edge_type': 'is_syn',
            'source': idx[src],
            'target': idx[tgt],
            'properties':{
                'label': label,
            }
        }
        yield payload

    yield  {
            'edge_type': 'is_syn',
            'source': "mhldhfl",
            'target': "zjelahzrl",
            'properties':{
                'label': label,
            }
        }

def main():
    """ re-Index all the Proxteam corpus """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="key", default=None)
    parser.add_argument("--username" , action='store', help="user", default=None)
    parser.add_argument("--password" , action='store', help="pwd", default=None)
    parser.add_argument("--path", action='store', help="path", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)

    args = parser.parse_args()


    # Bot creation & login 
    bot = Botagraph(args.host, args.key)

    if args.username and args.password:
        bot.authenticate(args.username, args.password)

    # read / parse graph
    graph = igraph.read(args.path)

    vs =  sorted( [ (v.index, v.degree() ) for v in  graph.vs ], key=lambda x: x[1], reverse = True )
    graph = graph.subgraph( [  v[0] for v in vs[:]] )
    print graph.summary()

    # create empty graph
    gid =  args.gid


    if not bot.has_graph(gid) :
        print "create graph %s" % gid
        bot.create_graph(gid, "no description")
        print "create node type %s" % "word"
        bot.post_node_type(gid, "word", { "desc": "no description"})
        print "create edge type %s" % "is_syn"
        bot.post_edge_type(gid, "is_syn", { })

    print "Get schema '%s'" % gid
    print bot.get_schema(gid)
    
    idx = {}
    
    print "posting nodes"
    count = 0
    for node, uuid in bot.post_nodes( gid, gen_nodes(graph) ):
        idx[node['properties']['label']] = uuid
        count += 1
        #print ">>> ", node['properties']['label'], uuid 
    print "%s nodes inserted " % count

    
    #print "iterate over nodes"
    #for node in bot.find_all_nodes(gid, "word", {}):
        #pass#print node

    # post edges
    print "posting edges"
    count = 0
    fail = 0

    inv_idx = { v:k for k,v in idx.iteritems() }
    
    for obj, uuid in bot.post_edges( gid, gen_edges(graph, idx) ):
        if not uuid:
            fail += 1
        else :
            count += 1
        #print "%s [ %s -- %s --> %s ] " % ( uuid, inv_idx.get(obj['source'], None) , "syn", inv_idx.get(obj['target'], None) )
    print "%s edges inserted, %s failed " % (count, fail)

    
if __name__ == '__main__':
    sys.exit(main())
