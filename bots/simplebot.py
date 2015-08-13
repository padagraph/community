#-*- coding:utf-8 -*-

import sys
import argparse
import igraph


from botapi import PadaBot


def gen_nodes(graph):
    for v in graph.vs:
        payload = {
                    'node_type': 'word',
                    'name': v['label']
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
    
    graph = igraph.read(args.path)
    print graph.summary()
    
    vs =  sorted( [ (v.index, v.degree() ) for v in  graph.vs ], key=lambda x: x[1], reverse = True )
    graph = graph.subgraph( [  v[0] for v in vs[:100]] )
    print graph.summary()

    gid =  args.gid 

    botapi = PadaBot(args.host, args.key)
    if args.username and args.password:
        botapi.authenticate(args.username, args.password)

    # create empty graph
    botapi.create_graph(gid, "no description")
    r = botapi.post_node_type(gid, "word", { "desc": "no description"})
    assert r.json().get('uuid')
    r = botapi.post_edge_type(gid, "is_syn", { })
    assert r.json().get('uuid')
    
    # post nodes
    idx = {}

    for res in botapi.post_nodes( gid, gen_nodes(graph) ):
        idx[res['node']] = res['uuid'] 
    
    # post edges
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
        #print payload
        r = botapi.post_edge(gid, payload)
        print "%s [ %s -- %s --> %s ] " % (r.status_code, src, label , tgt )

    ## save if needed
    #print "saving"
    #botapi.save()
    
if __name__ == '__main__':
    sys.exit(main())
