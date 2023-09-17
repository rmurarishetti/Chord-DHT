
## 🚀 What is Chord?
The Chord DHT protocol is a distributed hash table (DHT) protocol that was first proposed in 2001. It is a scalable and efficient way to store and retrieve data in a distributed network. Chord uses a ring topology to organize nodes, and each node maintains a small routing table that allows it to quickly locate other nodes in the ring.

## Chord DHT Architecture

Each node in a Chord DHT network is assigned a unique identifier (ID), which is a hash of the node's IP address and port number. The nodes are then arranged in a logical ring, with each node's predecessor and successor being the two nodes with the closest IDs.

Each node also maintains a finger table, which is a list of pointers to other nodes in the ring. The finger table is used to quickly locate nodes that are responsible for storing specific data keys.

## Chord DHT Operations

Chord DHT networks support a variety of operations, including:

Put: Stores a key-value pair in the DHT.
Get: Retrieves a value from the DHT, given its key.
Delete: Removes a key-value pair from the DHT.
To perform a put operation, a node first calculates the ID of the node that is responsible for storing the key. It then uses its finger table to locate that node and send it the key-value pair.

To perform a get operation, a node first calculates the ID of the node that is responsible for storing the key. It then uses its finger table to locate that node and send it a get request. The responsible node then returns the value to the requesting node.

To perform a delete operation, a node first calculates the ID of the node that is responsible for storing the key. It then uses its finger table to locate that node and send it a delete request. The responsible node then removes the key-value pair from its storage.

## Benefits of Chord DHT

Chord DHT networks offer a number of benefits, including:

Scalability: Chord DHT networks can scale to very large sizes, with millions or even billions of nodes.
Efficiency: Chord DHT networks are very efficient at storing and retrieving data.
Fault tolerance: Chord DHT networks are fault-tolerant, meaning that they can continue to operate even if some nodes fail.
Applications of Chord DHT

Chord DHT networks can be used for a variety of applications, including:

Distributed file sharing: Chord DHT networks can be used to implement distributed file sharing systems, such as BitTorrent.
Peer-to-peer networking: Chord DHT networks can be used to implement peer-to-peer networks, such as the Gnutella network.
Content distribution networks: Chord DHT networks can be used to implement content distribution networks (CDNs), which are used to deliver content, such as web pages and videos, to users around the world.

## Running this Program
To run this project first, 
```
make clean
make
```

Args:
* -p \<Number> The port that the Chord client will bind to and listen on. Represented as a base-10 integer. Must be specified.
* --sp \<Number> The time in deciseconds between invocations of 'stabilize'. Represented as a base-10 integer. Must be specified, with a value in the range of [1, 600].
* --ffp \<Number> The time in deciseconds between invocations of 'fix_fingers'. Represented as a base-10 integer. Must be specified, with a value in the range of [1, 600].
* --cpp \<Number> The time in deciseconds between invocations of 'check_predececssor'. Represented as a base-10 integer. Must be specified, with a value in the range of [1, 600].
* --ja \<String> The IP address of the machine running a Chord node. The Chord client will join this node’s ring. Represented as an ASCII string (e.g., 128.8.126.63). Must be specified if --jp is specified.
* --jp \<String> The port that an existing Chord node is bound to and listening on. The Chord client will join this node’s ring. Represented as a base-10 integer. Must be specified if --ja is specified.
* -r \<Number> The number of successors maintained by the Chord client. Represetned as a base-10 integer. Must be specified, with a value in the range of [1, 32]

An example usage to start a new Chord ring is:
```
chord -p 4170 --sp 5 --ffp 6 --cpp 7 -r 4
```

An example usage to join an existing Chord ring is:
```
chord -p 4171 --ja 128.8.126.63 --jp 4170 --sp 5 --ffp 6 --cpp 7 -r 4
```
