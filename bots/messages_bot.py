#-*- coding:utf-8 -*-

import sys
import argparse
from reliure.types import * 
import re
import codecs


from botapi import Botagraph, BotApiError


def gen_nodes(vs):
    for v in vs.values():
        payload = {
                    'nodetype': v['nodetype'],
                    'properties': { 
                        'label': v['label'],
                    }
                }
        yield payload

def gen_edges(es, idx):
    for e in es:
        (src, edgetype,tgt) = e
        payload = {
            'edgetype': edgetype,
            'source': idx[src],
            'target': idx[tgt],
            'properties':{
            }
        }
        yield payload

def main():
    """ re-Index all the Proxteam corpus """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="key", default=None)
    parser.add_argument("--username" , action='store', help="user", default=None)
    parser.add_argument("--password" , action='store', help="pwd", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)
    parser.add_argument("files", action='store', default=None, nargs='+')

    args = parser.parse_args()

    print " analysing {}".format("".join(args.files))

    # Bot creation & login 
    bot = Botagraph(args.host, args.key)

    if args.username and args.password:
        bot.authenticate(args.username, args.password)
    
    gid = args.gid
    if not bot.has_graph(gid) :
        print "create graph %s" % gid
        bot.create_graph(gid, "no description")
        print "create node type %s" % "file"
        props = { "label": Text()}
        bot.post_nodetype(gid, "file",  "no description", props)
        bot.post_nodetype(gid, "message",  "no description", props)
        print "create edge type %s" % "is_syn"
        bot.post_edgetype(gid, "listen", "no desc", {})
        bot.post_edgetype(gid, "trigger", "no desc", {})

    print "Get schema '%s'" % gid
    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }
    nodetype_file = nodetypes['file']['uuid']
    nodetype_message = nodetypes['message']['uuid']
    edgetype_listen = edgetypes['listen']['uuid']
    edgetype_trigger = edgetypes['trigger']['uuid']
   
    vs = {}
    es = []

    for js_file in args.files:
        if js_file.endswith('min.js'):
            #ignore minified js
            continue
        with codecs.open(js_file, 'r', 'utf8') as FILE:
            js_file = re.sub('^[./]+', '', js_file)
            vs[js_file] = {'label': js_file, 'nodetype': nodetype_file}

            for l in FILE:
                #remove comments:
                l = l.strip().split('//',1)[0]
                m = re.search(r'listenTo\([^"]*"([a-z-]+)"', l)
                if m:
                    message = m.group(1)
                    if message not in vs:
                        vs[message] = {'label': message, 'nodetype': nodetype_message}
                    es.append((js_file, edgetype_listen, message))
                m = re.search(r'trigger\([^"]*"([a-z-]+)"', l)
                if m:
                    message = m.group(1)
                    if message not in vs:
                        vs[message] = {'label': message, 'nodetype': nodetype_message}
                    es.append((js_file, edgetype_trigger, message))

    idx = {}
    print "posting nodes"
    count = 0
    fail = 0
    for node, uuid in bot.post_nodes( gid, gen_nodes(vs) ):
        if not uuid:
            fail += 1
        else :
            count += 1
            idx[node['properties']['label']] = uuid
        
    print "%s nodes inserted " % count

    
    #print "iterate over nodes"
    #for node in bot.find_all_nodes(gid, "word", {}):
        #pass#print node

    # post edges
    print "posting edges"
    count = 0
    fail = 0

    inv_idx = { v:k for k,v in idx.iteritems() }
    
    for _, uuid in bot.post_edges(gid, gen_edges(es, idx)):
        if not uuid:
            fail += 1
        else :
            count += 1
        #print "%s [ %s -- %s --> %s ] " % ( uuid, inv_idx.get(obj['source'], None) , "syn", inv_idx.get(obj['target'], None) )
    print "%s edges inserted, %s failed " % (count, fail)

    
if __name__ == '__main__':
    sys.exit(main())
