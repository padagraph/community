#-*- coding:utf-8 -*-

import sys
import argparse
import codecs
import re
from collections import defaultdict

from botapi import Botagraph


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
    bot.create_graph('Old Chinese', 'a graph of Old Chinese phonology')
    bot.post_node_type('Old Chinese', 'GSR', {}) 
    bot.post_node_type('Old Chinese', 'Initial', {}) 
    bot.post_edge_type('Old Chinese', 'Sinograms', {})

    Inidict = {}
    for  i, (_, uuid) in enumerate(bot.post_nodes('Old Chinese',
        ({'node_type':'Initial', 'properties':{'label':i}} for i in Initiales))): 
        Inidict[Initiales[i]] = uuid
    
    GSRdict = {}
    for  i, (_, uuid) in enumerate(bot.post_nodes('Old Chinese',({'node_type':'GSR', 'properties': {'label':s}} for s in GSR))): 
        GSRdict[GSR[i]] = uuid
    edges = [{'edge_type':'Sinograms',
              'properties':{'label': u",".join(sinos)},
              'source': GSRdict[gsr],
              'target': Inidict[i]} for (i, gsr), sinos in Matrix.iteritems()]
    #for e in edges:
    #    print e
    #    bot.post_edge('Old Chinese', e)
    for _ in bot.post_edges('Old Chinese', iter(edges)):
        pass


if __name__ == '__main__':
    sys.exit(main())

    
