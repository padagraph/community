# api

### botapi.py

  simple bot api to post graph.   
  Contains api basics methods to create and manage graphs, nodes and edge from a remote server.    
  It handles connection and posts data.   

```

from botapi import Botagraph, BotApiError

host = "http://padagraph.io"
token = "< your identification token >"

graph = "mygraph"
schema = { 'description':"graph experiment \n  ",
           'image': "http://example.com/image.png",
           'tags': ['', 'sample']
         }

# connection
bot = Botagraph(host, token)
bot.create_graph(graph, schema)

# see botapy.py

```

### botio.py

botio is basically a sample that shows how to listen on specific events that occured in the graph.   
Making programs to be be able to react on a chosen event in conjunction with the botapi.   
For fact checking, page scraping, games or exercices.

```
from botio import Botio

host = "http://padagraph.io"
port = 80
graph = "mygraph"

io = Botio(host, port)
io.listenTo(args.gid)

def wrap(e):
  def log(*args):
    print e, args
  return log

for event in Botio.events:
  io.on(event, wrap(event) )

print( "botio is listening to %s @ %s:%s" % ( graph, host, port ) )

# then wait
io.socket.wait()
```


