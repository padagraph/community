#-*- coding:utf-8 -*-

import sys
import argparse
import codecs
import re
from collections import defaultdict

from botapi import Botagraph

GID = 'Old Chinese'

def load_OCR_file(path):
    with codecs.open(path, "r", "utf8") as F:
        data = F.readlines()
        data = [l.split("\t")[:3] for l in data]
    tableau = defaultdict(list)
    GSR = set()
    I = set()
    for fields in data:
        try:
            gsr, syl, sino = fields
            #i = i.replace('<r>','')
            i = re.sub('[aAeiouəә].*', '', syl)
            gsr = gsr[:4]
            sino = sino.strip()
            I.add(i)
            GSR.add(gsr)
            tableau[(i,gsr)].append(sino)
        except:
            pass
    return (list(I), list(GSR), tableau)

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
    
    bot = Botagraph(args.host, args.key)

    if args.username and args.password:
        bot.authenticate(args.username, args.password)

    (Initiales, GSR, Matrix) = load_OCR_file(args.path)
    if not bot.has_graph(GID):
        bot.create_graph(GID, {'description': 'a graph of Old Chinese phonology',
                                     'image': "",
                                     'tags': ['chinese','phonology']})
        bot.post_nodetype(GID, 'GSR', 'Karlgren', {}) 
        bot.post_nodetype(GID, 'Initial', '', {}) 
        bot.post_edgetype(GID, 'Sinograms', '',{})

    print "Get schema '%s'" % GID
    schema = bot.get_schema(GID)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }
    Inidict = {}
    for  i, (_, uuid) in enumerate(bot.post_nodes(GID,
        ({'nodetype':nodetypes['Initial']['uuid'], 'properties':{'label':i}} for i in Initiales))): 
        Inidict[Initiales[i]] = uuid
    
    GSRdict = {}
    for  i, (_, uuid) in enumerate(bot.post_nodes(GID,({'nodetype':nodetypes['GSR']['uuid'], 'properties': {'label':s}} for s in GSR))): 
        GSRdict[GSR[i]] = uuid
    edges = [{'edgetype':edgetypes['Sinograms']['uuid'],
              'properties':{'label': u",".join(sinos)},
              'source': GSRdict[gsr],
              'target': Inidict[i]} for (i, gsr), sinos in Matrix.iteritems()]
    #for e in edges:
    #    print e
    #    bot.post_edge(GID, e)
    for _ in bot.post_edges(GID, iter(edges)):
        pass


if __name__ == '__main__':
    sys.exit(main())

    
