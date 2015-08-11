#-*- coding:utf-8 -*-

import sys
import argparse
import igraph

from botapi import Botapi

def main():
    """ re-Index all the Proxteam corpus """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="path", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="key", default=None)
    parser.add_argument("--path", action='store', help="path", default=None)
    parser.add_argument("--gid", action='store', help="path", default=None)

    args = parser.parse_args()
    
    graph = igraph.read(args.path)
    print graph.summary()
    
    vs =  sorted( [ (v.index, v.degree() ) for v in  graph.vs ], key=lambda x: x[1], reverse = True )
    graph = graph.subgraph( [  v[0] for v in vs[:100]] )
    print graph.summary()

    return
    gid =  args.gid 

    botapi = Botapi(args.host, args.key)

    # create empty graph
    botapi.create_graph(gid, "no description")
    
    # post nodes
    idx = {}
    for v in graph.vs:
        payload = {
                    'node_type': 'word',
                    'name': v['label']
                }
        r = botapi.post_node(gid, payload)
        resp = r.json()
        idx[v['label']] = resp['uuid'] 
        print v['label'], r.status_code, resp['uuid'] 
        
    # post edges
    for e in graph.es:
        src = graph.vs[e.source]['label']
        tgt = graph.vs[e.target]['label']
        label = "is_syn"
        
        payload = {
            'edge_type': 'syn',
            'label': label,
            'source': idx[src],
            'target': idx[tgt],
        }
        print payload
        r = botapi.post_edge(gid, payload)
        print "%s [ %s -- %s --> %s ] " % (r.status_code, src, label , tgt )

    # save if needed
    print "saving"
    botapi.save()
    
if __name__ == '__main__':
    sys.exit(main())
