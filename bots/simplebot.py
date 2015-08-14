#-*- coding:utf-8 -*-

import sys
import argparse
import igraph


from botapi import Botagraph, BotApiError


def gen_nodes(graph):
    for v in graph.vs:
        payload = {
                    'node_type': 'word',
                    'label': v['label'],
                    'lang':'fr'
                }
        yield payload

def gen_edges(graph, idx):
    for e in graph.es:
        src = graph.vs[e.source]['label']
        tgt = graph.vs[e.target]['label']
        label = "is_syn"
        
        payload = {
            'edge_type': 'is_syn',
            'label': label,
            'source': idx[src],
            'target': idx[tgt],
        }
        yield payload

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
    graph = graph.subgraph( [  v[0] for v in vs[:100]] )
    print graph.summary()

    # create empty graph
    gid =  args.gid

    print "create graph %s" % gid
    bot.create_graph(gid, "no description")
    print "create node type %s" % "word"
    bot.post_node_type(gid, "word", { "desc": "no description"})
    print "create edge type %s" % "is_syn"
    bot.post_edge_type(gid, "is_syn", { })
    
    idx = {}

    
    print "posting nodes"
    for res in bot.post_nodes( gid, gen_nodes(graph) ):
        idx[res['node']] = res['uuid']
        print res['node'], res['uuid'] 

    
    print "iterate over nodes"
    for node in bot.find_all_nodes(gid, "word", {}):
        print node

    # post edges
    inv_idx = { v:k for k,v in idx.iteritems() }
    for res in bot.post_edges( gid, gen_edges(graph, idx) ):
        print "%s [ %s -- %s --> %s ] " % ( res['uuid'], inv_idx[res['source']] , "syn", inv_idx[res['target']] )

    
if __name__ == '__main__':
    sys.exit(main())
