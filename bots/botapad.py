# -*- coding: utf-8 -*-

import sys
import argparse
from botapi import Botagraph, BotApiError
from reliure.types import Text 

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


def log(*args):
    if len(args) == 1 and type(args) in (tuple,list):
        args = args[0]
    if VERBOSE:
        print(args)

def debug(*args):
    if DEBUG:
        print "DEBUG:"
        pprint( args)

def norm_key(key):
    return re.sub('\W' , '', key)
   
def csv_rows(lines, start_col=None, end_col=None, separator=";"):
    
    log( "csv_rows %s %s [%s:%s]" % (separator , len(lines), start_col, end_col) )
    reader = csv.reader(lines, delimiter=separator)
    rows = [ r for r in reader]
    rows = [ r[start_col:end_col] for r in rows]
    rows = [ r for r in rows if len(r)]
    
    return rows
    
class Botapad(object):
    
    def __init__(self, host, key, gid, path, delete=False, separator='auto', start_col=None, end_col=None):
        """ Function doc
        :param : 
        """
        
        # Bot creation & login 
        log( "\n * Connecting to graph %s @ %s \n  " % (gid, host) )
        
        bot = Botagraph(host, key)

        self.bot = bot
        self.path = path
        self.gid = gid

        self.separator = separator
        self.start_col = 0 if start_col is None else start_col
        self.end_col = end_col

        self.idx = {}
        self.edgetypes = {}
        self.nodetypes = {}
        self.starred = set() # starred nodes

        self.projectors = []

        if bot.has_graph(gid) and delete:
            log( " * deleting graph %s" % gid )
            bot.delete_graph(gid)
             
        if not bot.has_graph(gid) :
            log( " * Create graph %s" % gid)
            bot.create_graph(gid, { 'description':"",
                                    'image': "",
                                    'tags': []
                                  }
                            )
        
    def read(self):
        
        if self.path[0:4] == 'http':

            log( " * Downloading %s \n" % self.path)
            content = requests.get(self.path).text
            lines = content.split('\n')
            
        else:
            with codecs.open(self.path, 'r', encoding='utf8' ) as fin:
                lines = [ line for line in fin]

        lines = [ line.strip() for line in lines ]
        lines = [ line.encode('utf8') for line in lines if len(line)]
        
        if self.separator == u'auto':
            line = lines[0]
            if line in ( '#;','#,','#%space','#%tab' ):
                if self.separator == '#%space': self.separator =  " "
                elif self.separator == '#%tab'  : self.separator = "\t"
                else: self.separator = line[1:]
        log(" * Reading %s with delimiter '%s'" % (self.path, self.separator))
        print lines
        return lines
            
    def parse(self):
        """ :param path : txt file path

        handles special lines starting with [# @ _]
        for comments, node type, property names
        
        """
        schema = self.bot.get_schema(self.gid)['schema']
        self.edgetypes = { e['name']:e for e in schema['edgetypes'] }
        self.nodetypes = { n['name']:n for n in schema['nodetypes'] }

        rows = []
        current = () # (VERTEX | EDGE, label, names, index_prop)

        lines = self.read()
        log( "* parsing %s lines with separator '%s'" % (len(lines), self.separator) )
        
        for line in lines:
            
            line = line.strip()

            if line == "" or line[:1] == "#":
                continue

            elif line[:1] in ("@", "_", "$"):
                if line[:1] in ("@", "_"):
                    self.post(current, rows)

                cols = re.sub(' ', '', line[1:]) # no space
                # @Politic: %Chamber; !First Name;!Last Name;%Party;%State;%Stance;Statement;
                cols = [e for e in re.split("[:;]", "%s" % cols) if len(e)]
                label = cols[0] # @Something
                
                # ( name, indexed, projection )
                props = [( norm_key(e), "!" in e, "%" in e ) for e in  cols[1:]]
                start = self.start_col
                end = self.end_col if self.end_col > 0 else len(props) 
                props = props[start: end]
                
                names = [ k[0] for k in props ]
                indexes = [ k[0] for k in props if k[1] ]
                projs = [ k[0] for k in props if k[2] ]

                typeprops = { k : Text() for k in names }
                    
                if line[:1] == "@":
                    rows = []
                    
                    current = (VERTEX, label, props)
                    if not label in self.nodetypes:
                        log( "* posting @ %s [%s]" % (label, ", ".join(names)) , indexes, projs)
                        self.nodetypes[label] = self.bot.post_nodetype(self.gid, label, label, typeprops)
                        
                elif line[:1] == "_":
                    rows = []
                    current = (EDGE, label, props)
                    if not label in self.edgetypes:                        
                        log( "* posting _ %s [%s]" % (label, ", ".join(names)) )
                        self.edgetypes[label] = self.bot.post_edgetype(self.gid, label, "", typeprops)
            else:
               rows.append(line)

        self.post( current, rows)

        log( " * Starring %s nodes" % len(list(self.starred)) )
        self.bot.star_nodes(self.gid, [ self.idx[e] for e in self.starred ])
        
    
                
    def post(self, current, lines):
        
        if not len(lines) or not len(lines): return
        
        mode, label, props = current
        names = [ k[0] for k in props ]

        rows = csv_rows(lines, start_col=self.start_col, end_col=self.end_col, separator=self.separator)

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

                if src in self.idx and tgt in self.idx:
                    edgeprops = dict(zip(names, values))
                    edgeprops['label'] = edgeprops.get('label', self.edgetypes[label]['name'])
                    
                    payload = {
                        'edgetype': self.edgetypes[label]['uuid'],
                        'source': self.idx[src],
                        'target': self.idx[tgt],
                        'properties': edgeprops
                    }
                    edges.append(payload)
                    
            log( "posting _ %s %s [%s]" % (len(edges), label , ", ".join(names)))
            for e in self.bot.post_edges(self.gid, iter(edges)) : 
                debug(e)
        
        # Vertex
        
        if mode == VERTEX:

            payload = []
            index_props = [ e for e,k in enumerate(props) if k[1] ]
            if len(index_props) == 0 : index_props = [0]
            
            for values in rows:
                if values[0][:1] == "*":
                    values[0] = values[0][1:]
                    self.starred.add(values[0])

                postdata = {
                    'nodetype': self.nodetypes[label]['uuid'],
                    'properties': dict(zip(names, values))
                  }
                if 'label' not in names:
                    key = " ".join([ values[i] for i in index_props ])
                    postdata['properties']['label'] = key
                
                payload.append( postdata)
            

                
            log( "posting @ %s %s" % (len(payload), label) , names, index_props) 
            for node, uuid in self.bot.post_nodes(self.gid, iter(payload)):
                key = "".join([ node['properties'][names[i]] for i in index_props  ])
                self.idx[ key ] = uuid
                debug(node)

            self.apply_projectors(rows , label, props, index_props)

    def apply_projectors(self, rows, label, props, index_props  ):
        """ property projector """

        projs = [p for p in props if p[2]]
        names = [ k[0] for k in props ]
        log( "projectors", projs )

        for p in projs :
            
            src = label
            tgt = p[0]
            
            iprop = names.index(tgt)
            Tgt = list( set( [ r[iprop] for r in rows ]) )

            log( "\n * Projector: %s(%s) -- %s(%s) (%s) %s" %( src , len(rows), tgt, len(Tgt), iprop, Tgt ) )

            nodeprops = { "label": Text() }
            self.nodetypes[tgt] = self.bot.post_nodetype(self.gid, tgt, tgt, nodeprops)

            etname = "%s_has_%s" % (src, tgt)
            self.edgetypes[etname] = self.bot.post_edgetype(self.gid, etname, etname, nodeprops)

            # create Tgt nodes
            payload = []
            for e in Tgt:
                #if values[0][:1] == "*":
                    #values[0] = values[0][1:]
                    #starred.add(values[0])
                payload.append( {
                    'nodetype': self.nodetypes[tgt]['uuid'],
                    'properties': dict(zip(['label'], [e] ))
                  })

            log( "posting @ %s %s " % (len(payload), tgt ))
            for node, uuid in self.bot.post_nodes(self.gid, iter(payload)):
                tgtid = '%s_%s' % (tgt,node['properties']['label'])
                self.idx[ tgtid ] = uuid
                log(node)

            # label -- property edge
            edges = []
            indexes = [ k[0] for k in props if k[1] ]
            projs = [ k[0] for k in props if k[2] ]
            iprop = names.index(tgt) 
            for r in rows:
                tgtid = '%s_%s' % (tgt,r[iprop])
                # index id node source (num or col1 or concat!
                #print "", index_props, [names[i] for i in index_props  ]
                srcid = "".join([ r[i] for i in index_props  ])
                edges.append( {
                    'edgetype': self.edgetypes[etname]['uuid'],
                    'source': self.idx[srcid],
                    'target': self.idx[tgtid],
                    'properties': {"label" : etname}
                } )
            log( "posting _ %s %s " % (len(edges), etname ) )
            #print edges
            for e in self.bot.post_edges(self.gid, iter(edges)) : 
                debug(e)
        

        
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
    parser.add_argument("--end-col" , action='store', help="", type=int, default=None)
    

    parser.add_argument("-d", "--debug" , action='store_true', help="", default=False)
    parser.add_argument("-v", "--verbose" , action='store_true', help="", default=False)

    args = parser.parse_args()

    global VERBOSE, DEBUG
    VERBOSE = args.verbose
    DEBUG = args.debug

    log( "VERBOSE", args.verbose, "DEBUG", args.debug )

    if args.host and args.key and args.name and args.path:
        pad = Botapad(args.host, args.key, args.name, args.path, delete=args.delete,
                start_col=args.start_col, end_col=args.end_col, separator=args.separator)
        pad.parse()
    
    log(" * Visit %s/graph/%s" % ( args.host, args.name) )
    
if __name__ == '__main__':
    sys.exit(main())
    