#-*- coding:utf-8 -*-

import sys
import time   
import argparse
from random import randint

import igraph

from reliure.types import * 


from botapi import Botagraph, BotApiError

    


def main():
    parser = argparse.ArgumentParser()    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="authentification token", default=None)

    args = parser.parse_args()

    # Bot creation & login 

    gid = "test"

    print "\n * Connecting to graph %s @ %s \n  " % (gid, args.host)
    bot = Botagraph(args.host, args.key)

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print "\n nodetypes: ", nodetypes.keys()
    print "\n edgetypes: ", edgetypes.keys()

    if not "bottest" in nodetypes:
         
        print "\n\n * Creating node type %s" % "bottest"
        props = { "label" : Text(),
                  "time"  : Text()
                }
        bot.post_nodetype(gid, "bottest",  "", props)

    if not "botrel" in edgetypes:
        print "\n\n * Creating edge type %s" % "botrel"
        bot.post_edgetype(gid, "botrel", "no desc", {"value":Text()})

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    nodedata = lambda label: {
            'nodetype': nodetypes['bottest']['uuid'],
            'properties': { 
                'label': label,
                'time':  datetime.datetime.now().isoformat(),
            }
          }
          
    nodes = {}
    edges = []
    for l in ('foo', 'far', 'faz'):
        print "inserting", l
        node = bot.post_node(gid, nodedata(l))
        nodes[l] = node

    for s in nodes.values():
        for t in nodes.values():
            src = s['uuid']
            tgt = t['uuid']
            if src == tgt:
                continue

            data ={
                'edgetype': edgetypes['botrel']['uuid'] ,
                'source': src,
                'target': tgt,
                'properties': {}
            }
            
            print "inserting edge ", s['label'], t['label']
            edges.append( bot.post_edge(gid, data) )

    for n in nodes.values():
        print "deleting", n['uuid'], n['label']
        bot.delete_node(gid, n['uuid'])

if __name__ == '__main__':
    sys.exit(main())
