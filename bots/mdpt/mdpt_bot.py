#-*- coding:utf-8 -*-

import sys
import argparse
import igraph
from reliure.types import * 

from botapi import Botagraph, BotApiError

# nodetype: ('name' , 'desc', props {key,type} )
Nodetypes = [ ("Article",  "Mediapart article", {
                 'label'  : Text(),
                 'langue' : Text(),
                 'date' : Text(),
                 'url'  : Text(),
                 'cat'  : Text(),
                 'type' : Text(),
                 'image': Text(),
                 'title'  : Text(),
                 'chapeau': Text(),
                 'text'   : Text(),
                 'keyword': Text(),
                 'comments': Numeric(),
            }),

            ( "Author",  "Mediapart author", {
                 'label'  : Text(default=u"%name"),
                 'name' : Text(),
                 'url' : Text(),
            }), 

            ( "Related",  "article related source", {
                 'label'  : Text(),
                 'title' : Text(),
                 'url' : Text(),
            }),
            
            ("Keyword",  "article keyword", {
                 'label'  : Text(),
                 'tag'  : Text(),
            })
        ]

Edgetypes = [
    ( "has_keyword", "(article) -[has_keyword]-> (keyword)", {}),
    ( "has_rel", "(article) -[has_rel_to]-> (resource)", {}),
    ( "wrote", "(author) -[wrote]-> (article)", {})
]   


schema = None

    
def parse_dump(mdpt, bot, schema, gid):

    def post_node( nodetype, props):
        data =  {
            'nodetype': schema['nodetypes'][nodetype]['uuid'],
            'properties': props
          }
        print( "inserting %s %s " % (nodetype, props['label']) )
        return bot.post_node(gid, data)
        
    import pickle
    from pprint import pprint

    articles = {}
    authors  = {}
    rel_sources = {}
    keywords    = {}

    art_keys = ( 'date', 'langue', 'cat', 'type', 'title', 'img', 'url', 'chapeau','keyword', 'text', 'comments' )
    art_edges = {
     'has_keyword', 'lireaussi', 'wrote', 'cite'
    }

    count = 0
    for day, edition in mdpt['france'].iteritems():
        
        print( "france", day )

        for art in edition.values():
            count += 1
            
            art['cite'] = [ cite for cite in art['cite'] if cite is not None]
            art['lireaussi'] = [ k for k in art['lireaussi'] if k is not None]
            art['keyword'] = [ k for k in art['keyword'] if k is not None]
            art['img'] = [ k for k in art['img']  if k is not None]
                
            if type(art['author']) in (unicode, str) :
                art['author'] = [art['author']]
            art['author'] = [ k for k in art['author']  if k is not None]
            
            rels = []

            article = { k:art[k] for k in art_keys }
            article['label'] = article['title']
            article['keyword'] = [e for x in art['keyword'] for e in x]
            article['img'] = "%s" % art['img']

            article = post_node('Article', article)
            articles[article['uuid']] = article
                        
    
            for name in  art[ 'author']:
                author =  authors.get( name, None)
                if author is None:
                    author  = { 'label': name, 'name': name }
                    author  = post_node('Author', author) 
                    authors[name] = author

                rels.append( ( author, 'wrote', article, {}) ) 
                       

            #import pdb; pdb.set_trace()

            for aussi in  art[ 'lireaussi']:
                
                lireaussi =  rel_sources.get(aussi, None)
            
                if lireaussi is None:
                    lireaussi = {'label': aussi, 'url': aussi }
                    lireaussi  = post_node('Related', lireaussi)
                    rel_sources[aussi] = lireaussi

                rels.append(( article, "has_rel", lireaussi, {} ))


            for cite in art['cite']:
                node =  rel_sources.get(cite, None)
                if node is None:
                    node = {'label': cite, 'url': cite}
                    node  = post_node('Related', node)
                    rel_sources[cite] = node

                rels.append( (article, "has_rel", node, {} ) )


            for tag, label in art[ 'keyword']:

                keyword = keywords.get(tag, None)
                if keyword is None:
                    keyword = { 'tag': tag, 'label': label }
                    keyword = post_node('Keyword', keyword)
                    keywords[tag] = keyword
                    
                rels.append( (article, "has_keyword", keyword,  {} ) )

        
            edges = ({

                 'source': src['uuid'],
                 'edgetype': schema['edgetypes'][edgetype]['uuid'],
                 'target': tgt['uuid'],
                 'properties': props
                 
                } for src, edgetype, tgt, props in rels )

            res = list(bot.post_edges(gid , edges))
            print "  **    %s --> %s " % (count, len(res))
    

def main():
    """ re-Index all the Proxteam corpus """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="key", default=None)
    parser.add_argument("--path", action='store', help="path", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)
    
    args = parser.parse_args()

    print "* reading %s" % args.path
    import pickle
    mdpt = pickle.load(open(args.path, 'r'))

    gid =  args.gid

    # Bot creation & login 
    bot = Botagraph(args.host, args.key)

    if not bot.has_graph(gid) :
        print "create graph %s" % gid
        bot.create_graph(gid, { 'description':"mediapart corpus\n * ",
                                'image': "",
                                'tags': ['mediapart', 'journal', 'presse']
                              }
                        )

    # retrieve or create schema

    print "\n * Get schema '%s'" % gid

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    # add nodetypes if not present
    for label, desc, props in Nodetypes:
        if label not in nodetypes: 
            print " * Creating node type %s" % label
            bot.post_nodetype(gid, label, desc, props )
         
    # add edgetypes if not present
    for label, desc, props in Edgetypes:
        if label not in edgetypes:
            print " * Creating edge type %s" % label
            bot.post_edgetype(gid, label, desc, props)

    schema = bot.get_schema(gid)['schema']
    schema['nodetypes'] = { n['name']:n for n in schema['nodetypes'] }
    schema['edgetypes'] = { e['name']:e for e in schema['edgetypes'] }

    print schema['nodetypes']
    print schema['edgetypes']


    # parse & insert data
    parse_dump(mdpt, bot, schema, gid )
    

    
if __name__ == '__main__':
    sys.exit(main())
