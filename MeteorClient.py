import time
import datetime
from DDPClient import DDPClient

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

class MeteorClient(object):
    def __init__(self, url, debug=False):
        self.collection_data = CollectionData()
        self.ddp_client = DDPClient(url, debug)
        self.ddp_client.on('connected', self.connected)
        self.ddp_client.on('socket_closed', self.closed)
        self.ddp_client.on('failed', self.failed)
        self.ddp_client.on('added', self.collection_data.add_data)
        self.ddp_client.on('changed', self.collection_data.change_data)
        self.ddp_client.on('removed', self.collection_data.remove_data)
        self.connected = False
        self.ddp_client.connect()
        self.subscriptions = {}

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
        start = datetime.datetime.now()
        while not self.connected and self._time_from_start(start).seconds < 5:
            time.sleep(0.1)

        if not self.connected:
            raise MeteorClientException('Could not subscribe because a connection has not been established')

        def subscribed(error, sub_id):
            if error:
                self._remove_sub_by_id(sub_id)
                callback(error.get('reason'))
                return
            callback(None)

        if name in self.subscriptions:
            raise MeteorClientException('Already subcribed to {}'.format(name))

        sub_id = self.ddp_client.subscribe(name, params, subscribed)
        self.subscriptions[name] = sub_id

    def unsubscribe(self, name):
        """Unsubscribe from a collection

        Arguments:
        name - the name of the publication"""
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
        print '* CONNECTION CLOSED {} {}'.format(code, reason)


    def failed(self, collection, code, reason):
        print '* FAILED - data: {}'.format(str(data))

    def _time_from_start(self, start):
        now = datetime.datetime.now()
        return now - start

    def _remove_sub_by_id(self, sub_id):
        for name, cur_sub_id in self.subscriptions.items():
            if cur_sub_id == sub_id:
                del self.subscriptions[name]
