# Engineering Notebook for Final Project:
Engineering notebook of our Proof for our mini-IPFS implementation. Final Project for CS 262 @ harvard.


## Introduction to IPFS
File sharing has traditionally been viewed as a centralized process. With the advent of the internet, the most popular method for online file sharing involved a central server holding the files and clients requesting the contents of the files whenever they needed access. Many simple systems rely on this method for file sharing. However, as discussed in class, this form of file management is vulnerable to failure since users will not be able to retrieve their files if the central server goes down. Companies have traditionally circumvented the server being the single point of failure by initializing many different servers. The centralized system for file sharing also faces issues such as security and version control. 

Launched in 2015, InterPlanetary File System (IPFS) served as a decentralized alternative for file-sharing. IPFS is a distributed, peer-to-peer file system that provides a more efficient and decentralized way to store and share data across the internet. Unlike traditional web technologies that rely on centralized servers, IPFS is designed to work without a central point of control, allowing anyone to participate in the network and contribute storage and bandwidth resources.

IPFS stores multiple copies of files across different nodes in the network, providing redundancy and ensuring data availability even if some nodes go offline. This means that files can be accessed and downloaded faster, and the network is more resilient to failures or attacks. In addition, IPFS can offload traffic from central servers, reduce latency, and improve download speeds, making it a more scalable and performant alternative to traditional web technologies.

To ensure data integrity, IPFS uses cryptographic hashing to create unique content identifiers (CIDs) for each file. This means that identical files will have the same CID, and any changes made to a file will result in a new CID. This ensures that files cannot be tampered with or altered without detection, providing a secure and reliable way to store and share data.

IPFS has many potential use cases, including decentralized web hosting, distributed databases, peer-to-peer content delivery, and more. Its open-source nature and community-driven development make it an exciting and rapidly evolving technology that is changing the way we think about data storage and sharing on the internet.


## Project Goal
For our CS 262 final project, we seek to recreate a mini-version of the IPFS protocol and then simulate a proof of concept with storing and retrieving a simple text file. That goal will involve the following: designing a data structure to represent files, implementing IPFS nodes that are capable of storing chunks of data, implementing communication between IPFS nodes, and building a web-based UI in which a user can upload files to receive a hash as well as input a hash to receive files. 

## Implementation Methodology
To implement IPFS, we will need to spin up multiple servers, come up with a way to allocate file chunks across different servers, and implement a way to recreate files across different machines. The sections below detail the choices we made implementing all of the features needed for our user experience.

## Creating an IPFS Node

### Splitting Files

Within our primary IPFS node, we need to split up a given file into chunks, create a merkle DAG out of the hashes of these chunks, and send the chunks to peer IPFS nodes for storage. 

To split our file into chunks, we first chose a standard block size (256 bytes). Then, when a client uploads a file to the primary IPFS node, it 

Next, for file storage we rely on the Merkle Directed Acyclic Graph Data structure (Merkle DAG). 

A Merkle DAG (Directed Acyclic Graph) is a data structure used by IPFS to efficiently store and retrieve files in a decentralized network. In a Merkle DAG, each node represents a piece of data, and each edge represents a cryptographic hash that links nodes together. The result is a tree-like structure where every node is uniquely identified by a hash of its contents and the hashes of its children.

Here is an illustration of the Merkle DAG that we will use:

![Merkle DAG illustration](merkle.png)


Merkle DAGs are well-suited for IPFS since they verify the integrity of files without relying on a centralized authority. That is, when a file is added to IPFS, its contents are hashed, and the resulting hash is used as the root of a Merkle DAG. Each chunk of the file is then hashed and linked together in a tree-like structure, with each node representing a unique piece of data. This means that any changes made to the file will result in a different Merkle DAG, making it easy to detect tampering or corruption. 

Using a Merkle DAG also allows IPFS to efficiently store and retrieve files by only requesting the specific pieces of data needed to reconstruct a file, rather than downloading the entire file from a central server. This reduces bandwidth usage and improves download speeds, making IPFS a more scalable and efficient alternative to traditional web technologies.

For us, the leafs of the merkle DAG will be the hashes of the chunks that we are sending to other peer IPFS nodes for storage. 

After this Merkle DAG is created, we will then have our primary server randomly assign chunks to different online peer IPFS nodes. 


### Handling Server-to-Server Communication



#### Sending Chunks

#### Retrieving Files / Chunks


### Handling Client-Server Requests



## User Experience Walthrough
For IPFS, we will launch a simple website that has two pages. The first will allow a user to upload a file and store it on the IPFS servers. This first page will return an overall hash for the file that the user can later use for file retrieval. The second page will take the overall hash for the file and then print the reconstructed file onto the webpage. Hence, all the user needs to do is have their file on their computer and keep track of their hash to retrieve the file.


## References
https://en.wikipedia.org/wiki/InterPlanetary_File_System
https://docs.ipfs.tech/concepts/how-ipfs-works/
https://docs.ipfs.tech/concepts/merkle-dag/
https://decrypt.co/resources/how-to-use-ipfs-the-backbone-of-web3
https://www.researchgate.net/figure/An-illustration-of-a-Merkle-Tree_fig4_339067478




