
# botapad

* import from file or URL
* csv like import format


## Installation

    $ pip install -r requirements.txt

## Format

We are using a csv like file format.
Some special characters are used at a begin line:

* '#' is used as commented line and will be ignored
* '@' Header for nodes :
* '_' Header for edges :
* '*' marker for starred nodes :

Headers refers to `nodetypes` or `edgetypes` in the padagraph database.
syntax is ```char name: prop; other``` with `char` in ( `@`,`_` )
`:` after  Nodetype name and `;` between properties
Properties are defined with a `Text` definition.

### Node header

(we may extends to control over property types if needed or PR proposed)

Creating a table for a nodetype

    @ Person:  label ; image 

We just defined a `Person` nodetype with `properties`.

`label` is always required and is used by padagraph to find nodes in the searchbox.
`image` is used by padagraph to render nodes in graph.

The first column will also be an `indexed column` to describe node relations later with `Edges`.
you can now use `num` in `Relations` for shorthand and pad maintenance and uniqness. 

    @ Person: num; label; image 

Next row is expecting data from this table.
Begining and ending space will be removed in each cell.    

    *0; François Fillon; https://infographics.mediapart.fr/2017/nodes-fillon/img/nodes/0.png
    3; Myriam Lévy; https://infographics.mediapart.fr/2017/nodes-fillon/img/nodes/3.png
    4; Delphine Burgaud; https://infographics.mediapart.fr/2017/nodes-fillon/img/nodes/4.png
    5; Delphine Peyrat-Stricker; https://infographics.mediapart.fr/2017/nodes-fillon/img/nodes/5.png
    15; Anne Méaux; https://infographics.mediapart.fr/2017/nodes-fillon/img/nodes/15.png

Mind the node 0 , starting with `*` is `starred` .


### Edge header

As a `nodetype`, an `edgetype` is described by properties.
`_` is the marker used to start a set of relation of a certain type.

    _ Knows: 

and the data we use the indexed culumn `num` to identify the nodes:

    0;4
    0;5
    15;3
    15;4
    
!!!! Warning you have to keep your uniq ids for the whole data !!!! 

## Usage

    $ python graphname url_or_path --key key 

    # exemple with framapad
    $ python botapad.py fillon https://mensuel.framapad.org/p/qzpH0qxHkM/export/txt --key `cat padagraph.key` -v

## Combine

    Combine import and screenshots

    $ python ../bots/botapad.py testcsv https://mensuel.framapad.org/p/qzpH0qxHkM/export/txt --host http://localhost:5000 --key `cat ../../key.local` -v \
    && python screenshot.py testcsv fin.png  --width 600 --height 600 --zoom 1000 --no-labels --vertex-size 1 --wait 4 --host http://localhost:5000 -d chromedriver \
    && feh fillon.png

