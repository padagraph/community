#-*- coding:utf-8 -*-

import argparse
from socketIO_client import SocketIO, BaseNamespace
"""  botio listen graph events. """


class BotIoError(Exception):
    pass

class Botio(object):
    events = [
                'new edge',         'new nodetype',       'new node',
                'edit edge',        'new edgetype',       'edit node',
                'new edge from',    'edit nodetype',      'delete node',
                'new edge to',      'edit edgetype',
                'delete edge',
            ];

    def __init__(self, url='http://localhost', port=3000 ):
        """  """
        self.socket =  SocketIO(url, port)

        def f(e):
            def log(*args):
                print e, args
            return log
            
        for event in Botio.events:
            self.on(event, f(event) )

    # on

    def on(self, event, callback):
        self.socket.on(event, callback)
        
    # emit
    
    def emit(self, event, uid):
        self.socket.emit(event, uid)
        self.socket.wait(1)
    
    # listen

    def listenTo(self,  uid):
        self.emit('listenTo', uid)

    def stopListeningTo(self, uid):
        self.emit('stopListeningTo', uid)
        
    def stopListening(self, uid):
        self.emit('stopListening', uid)

def main():
    """ 
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("gid", action='store', help="graph id", default=None)
    parser.add_argument("--host", action='store', help="host", default="http://localhost")
    parser.add_argument("--port", action='store', help="port", default="3000", type=int)


    args = parser.parse_args()

    # Bot creation 
    io = Botio(url=args.host, port=args.port)

    print "botio is listening to %s @ %s:%s" % ( args.gid, args.host, args.port )
    io.listenTo(args.gid)
    
    io.socket.wait()

import sys

if __name__ == '__main__':
    sys.exit(main())



