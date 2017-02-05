# -*- coding: utf-8 -*-

import sys
import argparse
from botapi import Botagraph, BotApiError
from reliure.types import * 

import codecs
import requests
import re
import csv
from pprint import pprint

DIRECTIONS = ('<<','--','>>')
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
        print "DEBUG:"
        pprint( args)
    
def parse(bot, gid,  lines, start_col=None, end_col=None,  **kwargs):
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


    for line in lines:
        
        line = line.strip()

        if line == "" or line[:1] == "#":
            continue

        elif line[:1] in ("@", "_"):
            post(bot, gid, current, rows, **kwargs)
            rows = []
            current = ()

            cols = [e for e in re.split("\W+", "%s" % line[1:]) if len(e)]
            label = cols[0]
            names = [norm_key(e) for e in  cols[1:]]
            start = 0 if start_col is None else start_col
            end = end_col if end_col > 0 else len(names) 
            names = names[start: end]

            props = { k : Text() for k in names }
                
            if line[:1] == "@":
                index_prop = names[0]
                current = (VERTEX, label, names, index_prop)
                if not label in nodetypes:
                    log( "* posting @ %s" % label, names )
                    nodetypes[label] = bot.post_nodetype(gid, label, label, props)
                    
            elif line[:1] == "_":
                current = (EDGE, label, names, None)
                if not label in edgetypes:                        
                    log( "* posting _ %s" % label, names  )
                    edgetypes[label] = bot.post_edgetype(gid, label, "", props)

        else:
           rows.append(line)

    post(bot, gid, current, rows, **kwargs)

    log( "Starring %s nodes" % len(list(starred)) )
    bot.star_nodes(gid, [ idx[e] for e in starred ])
    
        
def norm_key(key):
    return re.sub('\W' , '', key)

def csv_rows(lines, start_col=None, end_col=None, separator=";"):

    table = [ e.encode('utf8') for e in lines ]
    reader = csv.reader(table, delimiter=separator)
    start = 0 if end_col is None else start_col
    #end = len(names) if end_col is None else end_col
    end =  end_col
    rows = [ r[start:end] for r in reader if len(r)]
    
    return rows
    
def post(bot, gid, current, lines,  start_col=None, end_col=None, **kwargs):

    
    if not len(lines) or not len(lines): return
    
    mode, label, names, index_prop = current
    
    rows = csv_rows(lines, **kwargs)

    print "lines", len(rows) , current

    if mode == EDGE:

        edges = []
        for row in rows:
            row = [r.strip() for r in row]
            src, direction, tgt = [ e.strip() for e in re.split("\s+", row[0])]
            if direction not in DIRECTIONS :
                raise ValueError('edge direction not in [%s]' % ", ".join(DIRECTIONS))
            
            if '<' in direction:
                tmp = src
                src = tgt
                tgt = tmp
            
            values = row[1:] if len(row)>1 else []

            if src in idx and tgt in idx:
                props = dict(zip(names, values))
                props['label'] = props.get('label', edgetypes[label]['name'])
                
                payload = {
                    'edgetype': edgetypes[label]['uuid'],
                    'source': idx[src],
                    'target': idx[tgt],
                    'properties': props
                }
                edges.append(payload)
                
        log( "posting _ %s %s" % (len(edges), label) , names)
        for e in bot.post_edges(gid, iter(edges)) : 
            debug(e)
    
    # Vertex
    
    if mode == VERTEX:

        payload = []
        for values in rows:
            #print "**RR", len(values), values
            if values[0][:1] == "*":
                values[0] = values[0][1:]
                starred.add(values[0])
                              
            payload.append( {
                'nodetype': nodetypes[label]['uuid'],
                'properties': dict(zip(names, values))
              })
        
        log( "posting @ %s %s" % (len(payload), label) , names) 
              
        for node, uuid in bot.post_nodes(gid, iter(payload)):
            idx[ node['properties'][index_prop] ] = uuid
            debug(node)
    
def main():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument("name" , action='store', help="graph name", default=None)
    parser.add_argument("path" , action='store', help="path  txt file to parse ", default=None)

    parser.add_argument("--host", action='store', help="host", default="http://padagraph.io")
    parser.add_argument("--key" , action='store', help="authentification token", default=None)
    parser.add_argument("--delete" , action='store_true', help="delete graph", default=False)

    parser.add_argument("--separator" , action='store', help="csv col separator [;]", default=";")
    parser.add_argument("--start-col" , action='store', help="", type=int, default=0)
    parser.add_argument("--end-col" , action='store', help="", type=int, default=0)
    

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
            lines = content.encode("utf8").split('\n')
        else:
            with codecs.open(args.path, 'r', encoding='utf8' ) as fin:
                lines = [ line for line in fin]

        lines = [ line.strip() for line in lines ]
        lines = [ line for line in lines if len(line)]
        
        separator = args.separator
        if separator == u'auto':
            line = lines[0]
            if line in ( '#;','#,','#%space','#%tab' ):
                if separator == '#%space': separator =  " "
                elif separator == '#%tab'  : separator = "\t"
                else: separator = line[1:]
        print "sep", "'%s'" % separator, line, line[1:] 

        log( "* parsing %s lines with separator '%s'" % (len(lines), separator) )
        parse(bot, gid, lines, start_col=args.start_col, end_col=args.end_col, separator=separator)
    
            
if __name__ == '__main__':
    sys.exit(main())
    