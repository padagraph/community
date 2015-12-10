#-*- coding:utf-8 -*-

import sys
import argparse
import py2neo
from reliure.types import * 



from botapi import Botagraph, BotApiError

"""
dictionnaire de label -> properties list à importer
"""
SCHEMA = {
        "description": "Synonymy graph from the Chinese Open Wordnet",
        "tags": ["synonyms", "Mandarin", "Chinese"],
        "key": "key", 
        "Nodes": [
            {
                "type": "Word",
                "key": "form", 
                "description": "wordform",
                "properties": {"label": Text(), "form": Text(), "key": Text()}
            },
            {
                "type": "Sinogram",
                "key": "form",
                "description": "sinogram",
                "properties": {"label": Text(), "form": Text(), "key": Text()}
            },
        ],
        "Links": [
            {
                "type": "Synonym",
                "description": "synonymy relation between two words",
                "properties": {}
            },
            {
                "type": "Contains",
                "description": "a (Word) -[Contains]-> (Sinogram)s",
                "properties": {}
            }
        ]
}


def buildType(infos):
    return [infos["type"], infos["description"], infos['properties']]

def gen_nodes(graph, nodetype, infos):
    for v in graph.cypher.execute("MATCH (n:%s) RETURN n" % infos['type']):
        props = {key: v.n[key] for key in infos["properties"].keys()}
        props["label"] = v.n[infos["key"]]
        payload = {
                'nodetype': nodetype,
                'properties': props     
                }
        yield payload

def gen_edges(graph, edgetype, idx, infos):
    for row in graph.cypher.execute("MATCH (src) -[link:%s]-> (tgt) RETURN  src,link,tgt" % infos['type']):
        src = row.src[SCHEMA['key']]
        tgt = row.tgt[SCHEMA['key']]
        label = infos['type']
        props = {key: row.link[key] for key in infos["properties"].keys()}
        payload = {
            'edgetype': edgetype,
            'source': idx[src],
            'target': idx[tgt],
            'properties': props
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
    graph = py2neo.Graph()

    # create empty graph
    gid =  args.gid


    if not bot.has_graph(gid) :
        print "create graph %s" % gid
        bot.create_graph(gid, { 'description': SCHEMA["description"],
                                'image': "",
                                'tags': SCHEMA['tags']
                              }
                        )
        for infos in SCHEMA["Nodes"]:
            print "create node type %s" % infos["type"]
            bot.post_nodetype(gid, *buildType(infos))
        for infos in SCHEMA["Links"]:
            print "create edge type %s" % infos["type"]
            bot.post_edgetype(gid, *buildType(infos))

    print "Get schema '%s'" % gid
    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print nodetypes
    print edgetypes

    idx = {}
    
    print "posting nodes"
    count = 0
    fail = 0
    for infos in SCHEMA['Nodes']:
        for node, uuid in bot.post_nodes( gid, gen_nodes(graph, nodetypes[infos['type']]['uuid'], infos) ):
            if not uuid:
                fail += 1
            else :
                count += 1
                idx[node['properties'][SCHEMA['key']]] = uuid
            
    print "%s nodes inserted " % count

    # post edges
    print "posting edges"
    count = 0
    fail = 0

    inv_idx = { v:k for k,v in idx.iteritems() }
    for infos in SCHEMA['Links']: 
        for obj, uuid in bot.post_edges( gid, gen_edges(graph, edgetypes[infos['type']]['uuid'], idx, infos) ):
            if not uuid:
                fail += 1
            else :
                count += 1
            #print "%s [ %s -- %s --> %s ] " % ( uuid, inv_idx.get(obj['source'], None) , "syn", inv_idx.get(obj['target'], None) )
    print "%s edges inserted, %s failed " % (count, fail)

    
if __name__ == '__main__':
    sys.exit(main())
