#-*- coding:utf-8 -*-

import sys
import argparse
import igraph
from collections import namedtuple
from reliure.types import * 
from botapi import Botagraph, BotApiError

"""

parse and insert 

"""


g_attrs = {
  'description':open("./readme.md").read().replace("    ", ""),
  'image': "http://www.correlatesofwar.org/logo.png",
  'tags': ['correlatesofwar', 'war', 'alliance', "defense","pacts","treaties", "ententes"]
}

print g_attrs['description']

def Graph(gid=""):
    N = namedtuple('Graph', ['gid', 'vs', 'es',  'attrs'])
    g = N(gid, {}, {}, g_attrs)
    return g


def main():
    """  """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="key", default=None)
    parser.add_argument("--username" , action='store', help="user", default=None)
    parser.add_argument("--password" , action='store', help="pwd", default=None)
    parser.add_argument("--path", action='store', help="path", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)
    
    args = parser.parse_args()
    
    # Bot creation & login
    key = open(args.key, 'r').read().strip()
    print "\n * Connecting to %s \n  " % args.host 
    bot = Botagraph(args.host, key)

    # read / parse graph
    print "\n * Reading %s" % args.path
    g = Graph(args.gid)
    gid = g.gid

    if bot.has_graph(gid)  :
        bot.delete_graph(gid)
    
    if not bot.has_graph(gid) :
        print "\n * Create graph %s" % gid
        bot.create_graph(gid, g.attrs )
                        
        print "\n * Creating node type %s" % "Country"
        props = { "code" : Text(),
                  "label"  : Text()
                }
        bot.post_nodetype(gid, "Country",  "Country ", props)

        print "\n * Creating edge type %s" % "alliance"
        props = {
                  'id' : Numeric(),
                  'label' : Text(),
                  'starts' : Text(),
                  'ends'  : Text(),
                  'defense' : Numeric(),
                  'neutrality' : Numeric(),
                  'nonaggression' : Numeric(),
                  'entente' : Numeric(),
                }
        bot.post_edgetype(gid, "alliance", "alliance terms", props )
    

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }
    
    import csv
    with open(args.path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for i, row in enumerate(reader):
            # undirected
            if i == 0: continue
            if i % 2 != 0: continue
            
            node  = lambda x : {
                    'nodetype': nodetypes["Country"]['uuid'],
                    'properties': {
                        'code' : x[0],
                        'label': x[1]
                    }
                }

            g.vs[ row[1] ] = node( row[1:3] )
            g.vs[ row[3] ] = node( row[3:5] )

            left_censor, right_censor = row[11:13]

            alliances = "defense neutrality nonaggression entente".split()
            es = dict(zip(alliances,row[13:17]))
            es['starts'] = "/".join(row[5:8])
            es['ends'] = "/".join(row[8:11])
            es['id'] = row[0]
            es['label'] = " ".join([ a for a in alliances if es[a] in ( 1, "1") ])
            
            es.update()


            g.es[i] = {
                'edgetype': edgetypes["alliance"]['uuid'],
                'source': row[1],
                'target': row[3],
                'properties': es
            }

        print len(g.vs),  len(g.es)
            
    idx = {}
    for node, uuid in bot.post_nodes( gid, g.vs.itervalues() ):
        idx[ node['properties']['code']] =  uuid

    bot.star_nodes(gid, idx.values())
        
    print "%s nodes inserted . " % (len(idx))

    for edge in g.es.itervalues():
        edge['source'] = idx[edge['source']]
        edge['target'] = idx[edge['target']]

    fail = count = 0
    for edge, uuid in bot.post_edges( gid, g.es.itervalues() ):
        if not uuid:
            fail += 1
        else :
            count += 1

    print "%s edges inserted, %s failed " % (count, fail)

"""
version4id, ccode1, state_name1, ccode2, state_name2, dyad_st_day, dyad_st_month, dyad_st_year, dyad_end_day, dyad_end_month, dyad_end_year,
left_censor, right_censor, defense, neutrality, nonaggression, entente, version
"""
    
if __name__ == '__main__':
    sys.exit(main())