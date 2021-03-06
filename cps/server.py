#!/usr/bin/env python
# -*- coding: utf-8 -*-


from socket import error as SocketError
import sys
import os
try:
    from gevent.pywsgi import WSGIServer
    from gevent import monkey
    from gevent.pool import Pool
    from gevent import __version__ as geventVersion
    gevent_present = True
except ImportError:
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    from tornado import version as tornadoVersion
    gevent_present = False

import web


class server:

    wsgiserver = None
    restart= False

    def __init__(self):
        pass

    def start_gevent(self):
        try:
            ssl_args = dict()
            if web.ub.config.get_config_certfile() and web.ub.config.get_config_keyfile():
                ssl_args = {"certfile": web.ub.config.get_config_certfile(),
                            "keyfile": web.ub.config.get_config_keyfile()}
            if os.name == 'nt':
                self.wsgiserver= WSGIServer(('0.0.0.0', web.ub.config.config_port), web.app, spawn=Pool(), **ssl_args)
            else:
                self.wsgiserver = WSGIServer(('', web.ub.config.config_port), web.app, spawn=Pool(), **ssl_args)
            self.wsgiserver.serve_forever()

        except SocketError:
            web.app.logger.info('Unable to listen on \'\', trying on IPv4 only...')
            self.wsgiserver = WSGIServer(('0.0.0.0', web.ub.config.config_port), web.app, spawn=Pool(), **ssl_args)
            self.wsgiserver.serve_forever()
        except:
            pass

    def startServer(self):
        if gevent_present:
            web.app.logger.info('Starting Gevent server')
            # leave subprocess out to allow forking for fetchers and processors
            monkey.patch_all(subprocess=False)
            self.start_gevent()
        else:
            web.app.logger.info('Starting Tornado server')
            if web.ub.config.get_config_certfile() and web.ub.config.get_config_keyfile():
                ssl={"certfile": web.ub.config.get_config_certfile(),
                     "keyfile": web.ub.config.get_config_keyfile()}
            else:
                ssl=None
            # Max Buffersize set to 200MB
            http_server = HTTPServer(WSGIContainer(web.app),
                        max_buffer_size = 209700000,
                        ssl_options=ssl)
            http_server.listen(web.ub.config.config_port)
            self.wsgiserver=IOLoop.instance()
            self.wsgiserver.start()     # wait for stop signal
            self.wsgiserver.close(True)

        if self.restart == True:
            web.app.logger.info("Performing restart of Calibre-web")
            if os.name == 'nt':
                arguments = ["\"" + sys.executable + "\""]
                for e in sys.argv:
                    arguments.append("\"" + e + "\"")
                os.execv(sys.executable, arguments)
            else:
                os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            web.app.logger.info("Performing shutdown of Calibre-web")
        sys.exit(0)

    def setRestartTyp(self,starttyp):
        self.restart=starttyp

    def stopServer(self):
        if gevent_present:
            self.wsgiserver.close()
        else:
            self.wsgiserver.add_callback(self.wsgiserver.stop)

    def getNameVersion(self):
        if gevent_present:
            return {'gevent':geventVersion}
        else:
            return {'tornado':tornadoVersion}


# Start Instance of Server
Server=server()
