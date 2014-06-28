import time
import datetime
from DDPClient import DDPClient

from pyee import EventEmitter

class MeteorClientException(Exception):
    """Custom Exception"""
    pass

class CollectionData(object):
    def __init__(self):
        self.data = {}

    def add_data(self, collection, id, fields):
        if collection not in self.data:
            self.data[collection] = {}
        if not id in self.data[collection]:
            self.data[collection][id] = {}
        for key, value in fields.items():
            self.data[collection][id][key] = value

    def change_data(self, collection, id, fields, cleared):
        for key, value in fields.items():
            self.data[collection][id][key] = value

        for key, value in cleared.items():
            del self.data[collection][id][key]

    def remove_data(self, collection, id):
        del self.data[collection][id]

class MeteorClient(EventEmitter):
    def __init__(self, url, debug=False):
        EventEmitter.__init__(self)
        self.collection_data = CollectionData()
        self.ddp_client = DDPClient(url, debug)
        self.ddp_client.on('connected', self.connected)
        self.ddp_client.on('socket_closed', self.closed)
        self.ddp_client.on('failed', self.failed)
        self.ddp_client.on('added', self.added)
        self.ddp_client.on('changed', self.changed)
        self.ddp_client.on('removed', self.removed)
        self.connected = False
        self.ddp_client.connect()
        self.subscriptions = {}

    #
    # Meteor Method Call
    #

    def call(self, method, params, callback=None):
        self._wait_for_connect()
        self.ddp_client.call(method, params, callback=callback)

    #
    # Subscription Management
    #

    def subscribe(self, name, params=[], callback=None):
        """Subscribe to a collection
        Arguments:
        name - the name of the publication
        params - the subscription parameters

        Keyword Arguments:
        callback - a function callback that returns an error (if exists)"""
        self._wait_for_connect()

        def subscribed(error, sub_id):
            if error:
                self._remove_sub_by_id(sub_id)
                if callback:
                    callback(error.get('reason'))
                return
            if callback:
                callback(None)

        if name in self.subscriptions:
            raise MeteorClientException('Already subcribed to {}'.format(name))

        sub_id = self.ddp_client.subscribe(name, params, subscribed)
        self.subscriptions[name] = sub_id

    def unsubscribe(self, name):
        """Unsubscribe from a collection

        Arguments:
        name - the name of the publication"""
        self._wait_for_connect()
        if name not in self.subscriptions:
            raise MeteorClientException('No subscription for {}'.format(name))
        self.ddp_client.unsubscribe(self.subscriptions[name])
        del self.subscriptions[name]

    #
    # Event Handlers
    #

    def connected(self):
        self.connected = True
        print '* CONNECTED'

    def closed(self, code, reason):
        self.connected = False
        print '* CONNECTION CLOSED {} {}'.format(code, reason)

    def failed(self, data):
        print '* FAILED - data: {}'.format(str(data))

    def added(self, collection, id, fields):
        self.collection_data.add_data(collection, id, fields)
        self.emit('added', collection, id, fields)

    def changed(self, collection, id, fields, cleared):
        self.collection_data.change_data(collection, id, fields, cleared)
        self.emit('changed', collection, id, fields, cleared)

    def removed(self, collection, id):
        self.collection_data.remove_data(collection, id)
        self.emit('removed', collection, id)

    #
    # Collection Management
    #

    def find(self, collection, selector={}):
        results = []
        for _id, doc in self.collection_data.data.get(collection, {}).items():
            doc.update({'_id': _id})
            if selector == {}:
                results.append(doc)
            for key, value in selector.items():
                if key in doc and doc[key] == value:
                    results.append(doc)
        return results

    def find_one(self, collection, selector={}):
        for _id, doc in self.collection_data.data.get(collection, {}).items():
            doc.update({'_id': _id})
            if selector == {}:
                return doc
            for key, value in selector.items():
                if key in doc and doc[key] == value:
                    return doc
        return None

    def insert(self, collection, data, callback=None):
        self.call("/" + collection + "/insert", [data], callback=callback)

    def update(self, collection, selector, data, callback=None):
        self.call("/" + collection + "/update", [selector, data], callback=callback)

    def remove(self, collection, selector, callback=None):
        self.call("/" + collection + "/remove", [selector], callback=callback)

    #
    # Helper functions
    #

    def _time_from_start(self, start):
        now = datetime.datetime.now()
        return now - start

    def _remove_sub_by_id(self, sub_id):
        for name, cur_sub_id in self.subscriptions.items():
            if cur_sub_id == sub_id:
                del self.subscriptions[name]

    def _wait_for_connect(self):
        start = datetime.datetime.now()
        while not self.connected and self._time_from_start(start).seconds < 5:
            time.sleep(0.1)

        if not self.connected:
            raise MeteorClientException('Could not subscribe because a connection has not been established')
