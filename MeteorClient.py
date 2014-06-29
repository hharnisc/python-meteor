import time
import datetime

from DDPClient import DDPClient

from pyee import EventEmitter
import hashlib

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
        self.subscriptions = {}

    def connect(self):
        """Connect to the meteor server"""
        self.ddp_client.connect()

    #
    # Account Management
    #

    def login(self, user, password, callback=None):
        """Login with a username and password

        Arguments:
        user - username or email address
        password - the password for the account

        Keyword Arguments:
        callback - callback function containing error as first argument and login data"""
        # TODO: keep the login token, user_id and tokenExpires
        #       for reconnecting later
        self.emit('logging_in')
        def logged_in(error, data):
            if error:
                if callback:
                    callback(error, None)
                return
            if callback:
                callback(None, data)
            self.emit('logged_in', data)

        # hash the password
        hashed = hashlib.sha256(password).hexdigest()
        # handle username or email address
        if '@' in user:
            user_object = {
                'email': user
            }
        else:
            user_object = {
                'username': user
            }
        password_object = {
            'algorithm': 'sha-256',
            'digest': hashed
        }

        self.ddp_client.call('login',[{'user': user_object,
                             'password': password_object}],callback=callback)

    def logout(self, callback=None):
        """Logout a user

        Keyword Arguments:
        callback - callback function called when the user has been logged out"""
        self.ddp_client.call('logout', [], callback=callback)
        self.emit('logged_out')

    #
    # Meteor Method Call
    #

    def call(self, method, params, callback=None):
        """Call a remote method

        Arguments:
        method - remote method name
        params - remote method parameters

        Keyword Arguments:
        callback - callback function containing return data"""
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
            self.emit('subscribed', name)

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
        self.emit('unsubscribed', name)

    #
    # Collection Management
    #

    def find(self, collection, selector={}):
        """Find data in a collection

        Arguments:
        collection - collection to search

        Keyword Arguments:
        selector - the query (default returns all items in a collection)"""
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
        """Return one item from a collection

        Arguments:
        collection - collection to search

        Keyword Arguments:
        selector - the query (default returns first item found)"""
        for _id, doc in self.collection_data.data.get(collection, {}).items():
            doc.update({'_id': _id})
            if selector == {}:
                return doc
            for key, value in selector.items():
                if key in doc and doc[key] == value:
                    return doc
        return None

    def insert(self, collection, doc, callback=None):
        """Insert an item into a collection

        Arguments:
        collection - the collection to be modified
        doc - The document to insert. May not yet have an _id attribute,
        in which case Meteor will generate one for you.

        Keyword Arguments:
        callback - Optional. If present, called with an error object as the first argument and,
        if no error, the _id as the second."""
        self.call("/" + collection + "/insert", [doc], callback=callback)

    def update(self, collection, selector, modifier, callback=None):
        """Insert an item into a collection

        Arguments:
        collection - the collection to be modified
        selector - specifies which documents to modify
        modifier - Specifies how to modify the documents

        Keyword Arguments:
        callback - Optional. If present, called with an error object as the first argument and,
        if no error, the number of affected documents as the second."""
        self.call("/" + collection + "/update", [selector, modifier], callback=callback)

    def remove(self, collection, selector, callback=None):
        """Remove an item from a collection

        Arguments:
        collection - the collection to be modified
        selector - Specifies which documents to remove

        Keyword Arguments:
        callback - Optional. If present, called with an error object as its argument."""
        self.call("/" + collection + "/remove", [selector], callback=callback)

    #
    # Event Handlers
    #

    def connected(self):
        self.connected = True
        self.emit('connected')

    def closed(self, code, reason):
        self.connected = False
        self.emit('closed', code, reason)

    def failed(self, data):
        self.emit('failed', str(data))

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
