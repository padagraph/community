# -*- coding: utf-8 -*-

import sys
import argparse
from botapi import Botagraph, BotApiError
from reliure.types import * 

import codecs
import requests
import re
from pprint import pprint

EDGE = 0  
VERTEX = 1

DEBUG = False
VERBOSE = False

idx = {}
starred = set() # starred nodes
edgetypes = {}
nodetypes = {}

def log(*args):
    if len(args) == 1 and type(args) in (tuple,list):
        args = args[0]
    if VERBOSE:
        print(args)

def debug(*args):
    if DEBUG:
        pprint(args)
    
def parse(bot, gid,  content):
    """ :param path : txt file path

    handles special lines starting with [# @ _]
    for comments, node type, property names
    
    """
    global edgetypes
    global nodetypes

    schema = bot.get_schema(gid)['schema']
    edgetypes = { e['name']:e for e in schema['edgetypes'] }
    nodetypes = { n['name']:n for n in schema['nodetypes'] }

    rows = []
    current = () # (VERTEX | EDGE, label, names, index_prop)


    for line in content:
        
        line = line.strip()
        debug( line )

        if line == "" or line[:1] == "#":
            continue

        elif line[:1] in ("@", "_"):

            post(bot, gid, current, rows)
            rows = []
            current = ()

            argz = [e for e in re.split("\W+"  , line[1:]) if len(e)]
            debug( argz )
            label = argz[0]
            names = argz[1:]
            props = { k : Text() for k in names }
                
            if line[:1] == "@":
                index_prop = names[0]
                current = (VERTEX, label, names, index_prop)
                if not label in nodetypes:
                    log( "* posting @ %s" % label, names )
                    nodetypes[label] = bot.post_nodetype(gid, label, "", props)
                    
            elif line[:1] == "_":
                current = (EDGE, label, names, None)
                if not label in edgetypes:                        
                    log( "* posting _ %s" % label, names  )
                    edgetypes[label] = bot.post_edgetype(gid, label, "", props)

        elif line[:1] == "*":
                          
            line = line[1:] 
            values = [ e.strip() for e in line.split(";") ]
            rows.append(values)
            starred.add(values[0])


        else:
            values = [ e.strip() for e in line.split(";") ]
            rows.append(values)

    post(bot, gid, current, rows)

    log( "Starring %s nodes" % len(list(starred)) )
    bot.star_nodes(gid, [ idx[e] for e in starred ])
        

def post(bot, gid, current, rows):
    
    if not len(rows): return
    
    mode, label, names, index_prop = current
    
    if mode == EDGE:
        edges = []
        for rel in rows:
            src, tgt = (rel[0],rel[1])
            values = rel[2:] if len(rel)>2 else []
            
            if src in idx and tgt in idx:
                payload = {
                    'edgetype': edgetypes[label]['uuid'],
                    'label' : edgetypes[label]['name'],
                    'source': idx[src],
                    'target': idx[tgt],
                    'properties': dict(zip(names, values))
                }
                edges.append(payload)
                
        log( "posting _ %s %s" % (len(edges), label) , names)
        for e in bot.post_edges(gid, iter(edges)) : 
            debug( e)
    
    # Vertex
    
    if mode == VERTEX:
        payload = [{
            'nodetype': nodetypes[label]['uuid'],
            'properties': dict(zip(names, values))
          } for values in rows  ]
        
        log( "posting @ %s %s" % (len(payload), label) , names) 
              
        for node, uuid in bot.post_nodes(gid, iter(payload)):
            debug(node)
            idx[ node['properties'][index_prop] ] = uuid
    
def main():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument("name" , action='store', help="graph name", default=None)
    parser.add_argument("path" , action='store', help="path  txt file to parse ", default=None)

    parser.add_argument("--host", action='store', help="host", default="http://padagraph.io")
    parser.add_argument("--key" , action='store', help="authentification token", default=None)
    parser.add_argument("--delete" , action='store_true', help="delete graph", default=False)

    parser.add_argument("-d", "--debug" , action='store_true', help="", default=False)
    parser.add_argument("-v", "--verbose" , action='store_true', help="", default=False)

    args = parser.parse_args()

    global VERBOSE, DEBUG
    VERBOSE = args.verbose
    DEBUG = args.debug

    log( "VERBOSE", args.verbose, "DEBUG", args.debug )

    if args.host and args.key and args.name and args.path:
        # Bot creation & login 
        log( "\n * Connecting to graph %s @ %s \n  " % (args.name, args.host) )
        
        gid = args.name
        bot = Botagraph(args.host, args.key)

        if bot.has_graph(gid) and args.delete:
            log( " * deleting graph %s" % gid )
            bot.delete_graph(gid)
             
        if not bot.has_graph(gid) :
            log( " * Create graph %s" % gid)
            bot.create_graph(gid, { 'description':"",
                                    'image': "",
                                    'tags': []
                                  }
                            )
        if args.path[0:4] == 'http':
            log( " * Downloading %s \n" % args.path)
            content = requests.get(args.path).text
            content = content.split('\n')
        else:
            with codecs.open(args.path, 'r', encoding='utf8' ) as fin:
                content = [line for line in fin if len(line)]

        parse(bot, gid, content)
    

            
if __name__ == '__main__':
    sys.exit(main())
    