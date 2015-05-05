# python-meteor

An event driven Meteor client

**Installation**

```bash
$ pip install python-meteor
```

**Table of Contents**

- [History](#history)
- [TODO](#TODO)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Example](#example)
- [Collaborators](#collaborators)

## History

**Latest Version** 0.1.5

- BUGFIX - unsubscribe was not unsubcribing (missing sub ID) (thanks [@tdamsma](https://github.com/tdamsma))
- examples and docs support python 3

**Latest** 0.1.4

- BUGFIX - update connected status when reconnecting (thanks [@ppettit](https://github.com/ppettit))
- BUGFIX - make sure `logged_in` callback get's fired (thanks [@pmgration](https://github.com/pmgration))
- NOTE: python-ddp library has been updated that addresses connection problems

**Version** 0.1.3

- Fixed a bug that was causing a crash while removing a field on a change event (thanks [@ppettit](https://github.com/ppettit))

**Version** 0.1.2

- Implemented auto reconnect (auto reconnect on by default) and reconnected event emitter

**Version** 0.1.1

- Fixed bug in setup, was including built in hashlib

**Version** 0.1.0

- Initial implementation, add ability to call, subscribe, unsubscribe, do basic queries and login
- Data is stored in a local python dictionary (in memory) and updated in real time as collection change events are received. This allows for very a basic find and find_one APIs to be implemented.

## TODO

- Full minimongo API for find and find_one
- CI unit testing with Travis

## Quick Start

### General Commands

**Create a Meteor client and connect**

```python
from MeteorClient import MeteorClient

client = MeteorClient('ws://127.0.0.1:3000/websocket')
client.connect()
```

**Establish A Connection Without Auto Reconnect**

```python
from MeteorClient import MeteorClient

client = MeteorClient('ws://127.0.0.1:3000/websocket', auto_reconnect=False)
client.connect()
```

**Establish A Connection And With Reconnect Different Frequency**

```python
from MeteorClient import MeteorClient
# try to reconnect every second
client = MeteorClient('ws://127.0.0.1:3000/websocket', auto_reconnect=True, auto_reconnect_timeout=1)
client.connect()
```

**Call a remote function**

```python
def callback_function(error, result):
    if error:
        print(error)
        return

    print(result)

client.call('someFunction', [1, 2, 3], callback_function)
```

**Subscribe and Unsubscribe**

```python
def subscription_callback(error):
    if error:
        print(error)

client.subscribe('posts', callback=subscription_callback)
client.unsubscribe('posts')
```

**Find All Data In a Collection**

```python
all_posts = client.find('posts')
```

**Find Data In a Collection With Selector**

```python
sacha_posts = client.find('posts', selector={'author': 'Sacha Greif'})
```

**Find One**

```python
one_post = client.find_one('posts')
```

**Fine One With Selector**

```python
one_post = client.find_one('posts', selector={'author': 'Sacha Greif'})
```

**Insert**

```python
def insert_callback(error, data):
    if error:
        print(error)
        return
    print(data)

client.insert('posts', {'title': 'Google', 'url': 'https://google.com', 'comments': 'Search'}, callback=insert_callback)
```

**Update**

```python
def update_callback(error, data):
    if error:
        print(error)
        return
    print(data)

client.update('posts', {'title': 'Google'}, {'comments': 'Google main page'}, callback=update_callback)
```

**Remove**

```python
def remove_callback(error, data):
    if error:
        print(error)
        return
    print(data)

client.remove('posts', {'title': 'Google'}, callback=remove_callback)
```
## Usage

### Class Init

####DDPClient(url, auto_reconnect=True, auto_reconnect_timeout=0.5, debug=False)

**Arguments**

_url_ - to connect to ddp server

**Keyword Arguments**

_auto_reconnect_ - automatic reconnect (default: True)  
_auto_reconnect_timeout_ - reconnect every X seconds (default: 0.5)  
_debug_ - print out lots of debug info (default: False)  

### Functions

####connect()

Connect to the meteor server

####login(user, password, token=token, callback=None)

Login with a username and password. If a token is provided it will be tried first, falling back to username and password if
the token is invalid.

**Arguments**

_user_ - username or email address  
_password_ - the password for the account  

**Keyword Arguments**

_token_ - meteor resume token
_callback_ - callback function containing error as first argument and login data  

####logout(callback=None)

Logout a user

**Keyword Arguments**

_callback_ - callback function called when the user has been logged out  

#### call(method, params, callback=None)

Call a remote method

**Arguments**

_method_ - remote method name  
_params_ - remote method parameters  

**Keyword Arguments**

_callback_ - callback function containing return data  

#### subscribe(name, params=[], callback=None)

Subscribe to a collection

**Arguments**

_name_ - the name of the publication  
_params_ - the subscription parameters  

**Keyword Arguments**

_callback_ - a function callback that returns an error (if exists)  

####unsubscribe(name)

Unsubscribe from a collection

**Arguments**

_name_ - the name of the publication  

####find(collection, selector={})

Find data in a collection

**Arguments**

_collection_ - collection to search  

**Keyword Arguments**

_selector_ - the query (default returns all items in a collection)  

####find_one(collection, selector={})

Return one item from a collection

**Arguments**

_collection_ - collection to search  

**Keyword Arguments**

_selector_ - the query (default returns first item found)  

####insert(collection, doc, callback=None)

Insert an item into a collection

**Arguments**

_collection_ - the collection to be modified  
_doc_ - The document to insert. May not yet have an _id attribute,  
in which case Meteor will generate one for you.  

**Keyword Arguments**

_callback_ - Optional. If present, called with an error object as the first argument and,  
if no error, the _id as the second.  

####update(collection, selector, modifier, callback=None)

Insert an item into a collection

**Arguments**

_collection_ - the collection to be modified  
_selector_ - specifies which documents to modify  
_modifier_ - Specifies how to modify the documents  

**Keyword Arguments**

_callback_ - Optional. If present, called with an error object as the first argument and,  
if no error, the number of affected documents as the second.  

####remove(collection, selector, callback=None)

Remove an item from a collection

**Arguments**

_collection_ - the collection to be modified  
_selector_ - Specifies which documents to remove  

**Keyword Arguments**

_callback_ - Optional. If present, called with an error object as its argument.  

### Events and Callback Arguments

When creating an instance of `MeteorClient` it is capable of emitting a few events with arguments. The documentation below assumes that you've instanciated a client with the following code:

```python
from MeteorClient import MeteorClient
client = MeteorClient('ws://127.0.0.1:3000/websocket')
```

#### connected

Register the event to a callback function

```python
def connected(self):
    print('* CONNECTED')

client.on('connected', connected)
```

The connected event callback takes no arguments

#### closed

Register the event to a callback function

```python
def closed(self, code, reason):
    print('* CONNECTION CLOSED {} {}'.format(code, reason))

client.on('closed', closed)
```

`closed` callback takes the following arguments

_code_ - the error code  
_reason_ - the error message  

### reconnected

```python
def reconnected(self):
    print('* RECONNECTED')

client.on('reconnected', reconnected)
```

`reconnected` call back takes no arguments

#### failed

Register the event to a callback function

```python
def failed(collection, data):
    print('* FAILED - data: {}'.format(str(data)))

client.on('failed', failed)
```

`failed` callback takes the following arguments

_data_ - the error data  

#### added

Register the event to a callback function

```python
def added(collection, id, fields):
    print('* ADDED {} {}'.format(collection, id))
    for key, value in fields.items():
        print('  - FIELD {} {}'.format(key, value))

client.on('added', added)
```

`added` callback takes the following arguments

_collection_ - the collection that has been modified  
_id_ - the collection item id
_fields_ - the fields for item

#### changed

Register the event to a callback function

```python
def changed(collection, id, fields, cleared):
    print('* CHANGED {} {}'.format(collection, id))
    for key, value in fields.items():
        print('  - FIELD {} {}'.format(key, value))
    for key, value in cleared.items():
        print('  - CLEARED {} {}'.format(key, value))

client.on('changed', changed)
```

`changed` callback takes the following arguments

_collection_ - the collection that has been modified  
_id_ - the collection item id
_fields_ - the fields for item  
_cleared_ - the fields for the item that have been removed

#### removed

Register the event to a callback function

```python
def removed(collection, id):
    print('* REMOVED {} {}'.format(collection, id))

client.on('removed', removed)
```

`removed` callback takes the following arguments

_collection_ - the collection that has been modified  
_id_ - the collection item id

#### subscribed

Register the event to a callback function

```python
def subscribed(subscription):
    print('* SUBSCRIBED {}'.format(subscription))

client.on('subscribed', subscribed)
```

`subscribed` callback takes the following arguments

_subscription_ - the name of the subscription

#### unsubscribed

Register the event to a callback function

```python
def unsubscribed(subscription):
    print('* UNSUBSCRIBED {}'.format(subscription))

client.on('unsubscribed', unsubscribed)
```

`unsubscribed` callback takes the following arguments

_subscription_ - the name of the subscription

#### logging_in

Register the event to a callback function

```python
def logging_in():
    print('* LOGGIN IN')

client.on('logging_in', logging_in)
```

`logging_in` callback takes no arguments

#### logged_in

Register the event to a callback function

```python
def logged_in(data):
    print('* LOGGED IN {}'.format(data))

client.on('logged_in', logged_in)
```

`logged_in` callback takes the following arguments

_data_ - login return data

#### logged_out

Register the event to a callback function

```python
def logged_out():
    print('* LOGGED OUT')

client.on('logged_out', logged_out)
```

`logged_out` callback takes no arguments

####All of the callbacks

For reference

```python
client.on('connected', connected)
client.on('socket_closed', closed)
client.on('reconnected', reconnected)
client.on('failed', failed)
client.on('added', added)
client.on('changed', changed)
client.on('removed', removed)
client.on('subscibed', subscibed)
client.on('unsubscribed', unsubscribed)
client.on('logging_in', logging_in)
client.on('logged_in', logged_in)
client.on('logged_out', logged_out)
```

##Example

There is an included `example.py` script to use with the `todo` sample app included with meteor

Create the sample meteor app and start it

```bash
$ meteor create --example todos
$ meteor
```

Then run example.py

```bash
$ python example.py
```

##Collaborators

- [@ppettit](https://github.com/ppettit)
- [@pmgration](https://github.com/pmgration)
- [@tdamsma](https://github.com/tdamsma)
