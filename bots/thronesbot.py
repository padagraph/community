#-*- coding:utf-8 -*-
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--host", action='store', help="host", default="http://localhost:5000")
    parser.add_argument("--key" , action='store', help="authentification token", default=None)
    parser.add_argument("--gid", action='store', help="graph id", default=None)
    
    args = parser.parse_args()
    host, key, gid =  (args.host, args.key,args.gid)

    if None  in  (host, key, gid):
        parser.print_help()
        return

    # Setup schema
    
    from reliure.schema import Doc, Schema
    from reliure.types import Text, Numeric , Boolean, GenericType

    desc = """
        Game of thrones 
        %s
        """.replace("    ", "")

    g_attrs = {
        'description': desc % gid,
        
        #'image': "https://commons.wikimedia.org/wiki/File:Game_of_Thrones_2011_logo.svg?uselang=fr",
        #'tags': ['social-network', 'game-of-thrones']
    }

    # used for houses, sauvageons ...
    group_type = Schema(**{
                'label' : Text(),
                'url'  : Text(),
                'tags' : Text(multi=True, uniq=True),
                'image' : Text(),
                'color' : Text(),
                'shape' : Text(default=u"square"),
                "name" : Text(), 
            })

    # human like characters
    character_type = Schema(**{
                'label' : Text(),
                'url'  : Text(multi=True, uniq=True),
                'tags' : Text(multi=True, uniq=True),
                'image' : Text(),
                'shape' : Text(default=u"circle"),
                'description' : Text(),
                "name":Text(),
                "actor": Text(multi=True,uniq=True),
                "dubbling_vf": Text(multi=True,uniq=True),
                
                "bio_fr": Text(), 
                "bio_en": Text(), 
                "seasons": Text(), 
                "dead": Boolean(default=False),
            })

    # creaturs dragons, wolf, white walkers ?
    creatur_type = Schema(**{
                'label' : Text(),
                'url'  : Text(),
                'tags' : Text(multi=True, uniq=True),
                'image' : Text(),
                'shape' : Text(default=u"triangle"),
                'description' : Text(),
                "name" : Text(), 
                "bio_fr": Text(), 
                "bio_en": Text(), 
                "seasons": Text(), 
                "dead":  Boolean(default=False),
            })

    edgetypes = [
        # Characters or Creaturs -- rel --> Group
        # (name, desc , properties ),
        ("is_member_of", "Character is member of a Group", {"from_ep":Text(),} ),
        ("is_child_of", "character or creatur is child of another one", {} ),
        ("works_for", "character or creatur works for a character or a group", {"from_episode":Text(), "to_episode":Text()} ),
        ("is_friend_of", "character is friend of another one", {"from_ep":Text(),} ),
        
        ("married", "character meet another one", {"force": Numeric()} ),
        ("belongs_to", "character or creatur belongs to another one", {"from_episode":Text(), "to_episode":Text()} ),    
        ("kill", "character or creatur kill another one", { "episode":Text(), "method":Text() }),
        #("have_sex", "character or creatur have sex another one", { "episode":Text()} ),
        #("rape", "character or creatur rape another one", { "episode":Text()} ),
        #("meet", "character meet another one", { "episode":Text()}),
        #("loves", "character meet another one", {} ),
        
    ]


    # PARSING WK page

    from pyquery import PyQuery as pq
    import codecs

    root = "."
    path = "%s/pages/Personnages_de_Game_of_Thrones" % root
    graphmlz = "%s/got.graphml"  % root
                          
    def opengot():
        html = codecs.open(path, mode='r', encoding="utf8").read()
        html = pq(html)
        html = html(".mw-content-ltr")
        html(".mw-content-ltr h2:first").prevAll().remove()
        html(".mw-content-ltr h2:first").remove()
        html(".mw-content-ltr h2:first").nextAll().remove()

        html('.mw-editsection').remove()
        html('sup').remove()
        html = pq(".mw-content-ltr", html)
        return html


    def as_doc(ctype, cdata):
        d = Doc(ctype) 

        for k,v  in cdata.iteritems():
            if type(ctype[k]) == Text:
                d.set_field(k,v,True)
            else:
                d[k]= v
        return d.export()


    def _parse_color(e):
        color  = None    
        if "style" in e.attrib: 
            styles = dict ( pair.strip().split(':') for pair in  pq(e).attr("style").strip().lower().split(';') if len(pair))
            color = styles.get("background", None)
            
        if color and color in ( "black", "#000") : color = "#000000"
            
        return color
        
    def parse_belongs_legend(html):
        houses_map = {}
        legende = pq( "li", pq("table td ul", html)[:4])
        for e in legende:
            color = _parse_color(pq("span",e)[0])
            text = pq(e).text()#.replace("Maison ", "")
            houses_map[color] = text

        # removes legendes
        html(".mw-content-ltr h3:first").prevAll().remove()
        return houses_map


    def parse_creaturs_and_characters(html, houses):
        
        rel_belongs = []
        rel_member_of = []
        characters = []
        creaturs = []
        
        while True:
            # reading from end
            if len(html("h3:last")):
         
                ths = pq('th', html("h3:last").nextAll())
                tds = pq('td', html("h3:last").nextAll())

                title = html("h3:last").text()
                color = None
                flg = 0
                
                if len(ths)%5 == 0:
                    c = {}
                    member_of = []
                    for td in tds:
                        colspan = td.attrib.get('colspan', 0)
                        if colspan == "6": # table headers
                           color = _parse_color(td)
                           if color : 
                               member_of.append( houses[color] )
                           flg = 1 

                        elif colspan == 0: # table cells
                            if flg == 1:
                                actor_img = pq("img", td).attr("src")
                                if actor_img:
                                    c['image'] = "http:%s" %actor_img 
                            elif flg == 2: 
                                name = pq(td).text()
                                c['name'] = name ;
                                for e in member_of : 
                                    rel_member_of.append( (name, e) )
                            elif flg == 3:
                                c['actor'] = [pq(e).text() for e in pq("a", td)]

                            elif flg == 4:
                                c['dubbling_vf'] = [pq(e).text() for e in pq("a", td)]
                            elif flg == 5 :
                                c['seasons'] = pq(td).text()
                                c['dead'] = u"✝" in pq(td).text()
                            flg +=1
                            
                        elif colspan == "5": # table bio cell
                            c['bio_fr'] = pq(td).text() 
                            
                            characters.append(as_doc(character_type, c))
                            # reset 
                            c = {}
                            member_of = [] 
                            flg = 1

                if len(ths) == 2:
                    c = {}
                    belongs = [] 
                    for td in tds:
                        colspan = td.attrib.get('colspan', 0)
                        if colspan == "6":
                           color = _parse_color(td)
                           if color : 
                               belongs.append(houses[color])
                           flg = 1 

                        elif colspan == 0:
                            if flg == 1: 
                                name = pq(td).text().strip()
                                c['name'] = name 
                                for e in belongs : rel_belongs.append( (name, e))
                                flg = 2
                            if flg == 2:
                                c["seasons"] = pq(td).text()
                                c["dead"] = True # u"✝" in pq(td).text()

     
                        elif colspan == "5":
                           c['bio_fr'] = pq(td).text()
                           creaturs.append(as_doc(creatur_type, c))
                           c = {}
                           belongs = []  
                           flg = 0

                #removes section once parsed
                html("h3:last").nextAll().remove()
                html("h3:last").remove()

            else : break
                
        return characters, rel_member_of, creaturs, rel_belongs


    # In[ ]:

    from reliure.schema import Doc

    locations = [] # TODO

    html = opengot()
    houses_map = parse_belongs_legend(html)
    characters, rel_member_of, creaturs, rel_belongs = parse_creaturs_and_characters(html, houses_map)

    print "Groups   ", len(houses_map)
    print "Creaturs   ", len(creaturs)
    print "Characters ", len(characters)

    print "member_of", len(rel_member_of)
    print "belongs", len(rel_belongs)



    from botapi import Botagraph, BotApiError

    bot = Botagraph(host, key)

    if not bot.has_graph(gid) :
            
        print "\n * Creating graph %s" % gid
        bot.create_graph(gid, g_attrs)

        print "\n * Creating node type %s" % ""
        bot.post_nodetype(gid, "Character", "Character", character_type._fields)
        bot.post_nodetype(gid, "Creatur", "Creatur", creatur_type._fields)
        bot.post_nodetype(gid, "Group",  "Group", group_type._fields)
        
        for name, desc, props in edgetypes:
            bot.post_edgetype(gid, name, desc, props )


    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    idx = {} # (label, uuid)
    groups = []

    for k,v in houses_map.iteritems():
         g = as_doc(group_type, {'label': v,'name': v,'color':k })   
         groups.append( g )
            
    for name, els in [ ("Character", characters), 
                       ("Creatur", creaturs ) ,
                       ("Group", groups)
                     ]:
        
        print "Posting %s nodes %s" % (len(els), name)
        for c in els:
            payload = {
                    'nodetype': nodetypes[name]['uuid'],
                    'properties': { k:v for k,v in c.iteritems() }
                  }
            payload['properties']['label'] = payload['properties']['name']
            node = bot.post_node(gid, payload)
            idx[node['label']] = node['uuid']


    vids = set()
    for name, rels in [( "is_member_of", rel_member_of), 
                       ( "belongs_to",   rel_belongs) ]:
                
        print "Posting %s rels %s" % ( len(rels), name )
        for src, tgt in rels:
            if src in idx and tgt in idx:
                edge = {
                    'edgetype': edgetypes[name]['uuid'],
                    'source': idx[src],
                    'label' : name,
                    'target': idx[tgt],
                    'properties': {"from_ep":"",}
                }
                uuid = bot.post_edge(gid, edge)
                vids.add(src)
                vids.add(tgt)
            else:
                print src, tgt
                
    print "Starring %s nodes" % len(list(vids))
    bot.star_nodes(gid, list(vids))



if __name__ == '__main__':
    sys.exit(main())

