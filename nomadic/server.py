import threading

from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO

from nomadic.demon import logger
from nomadic import searcher

import sys, logging

class Server():
    def __init__(self, index):
        self.index = index;

        self.app = Flask(__name__,
                static_folder='static',
                static_url_path='',
                template_folder='templates')

        self.socketio = SocketIO(self.app)
        self.build_routes()

        # To log errors to stdout.
        # Can't really use Flask's debug w/ the websocket lib,
        # but this accomplishes the same thing.
        sh = logging.StreamHandler(sys.stdout)
        self.app.logger.addHandler(sh)

    def start(self):
        logger.debug('Starting the Nomadic server...')
        self.socketio.run(self.app, port=9137)

    def refresh_clients(self):
        self.socketio.emit('refresh')

    def build_routes(self):
        @self.app.route('/search', methods=['POST'])
        def search():
            q = request.form['query']
            results = searcher.search(q, self.index, html=True)
            return render_template('results.html', results=results)

        @self.socketio.on('connect')
        def on_connect():
            """
            This seems necessary to get
            the SocketIO emitting working properly...
            """
            logger.debug('User connected.')
