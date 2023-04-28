# Engineering Notebook for Final Project:
Engineering notebook of our Proof for our mini-IPFS implementation. Final Project for CS 262 @ harvard.


## Introduction to IPFS
File sharing has traditionally been viewed as a centralized process. With the advent of the internet, the most popular method for online file sharing involved a central server holding the files and clients requesting the contents of the files whenever they needed access. Many simple systems rely on this method for file sharing. However, as discussed in class, this form of file management is vulnerable to failure since users will not be able to retrieve their files if the central server goes down. Companies have traditionally circumvented the server being the single point of failure by initializing many different servers. The centralized system for file sharing also faces issues such as security and version control. 

In 2015, InterPlanetary File System (IPFS) was launched as a decentralized alternative to sharing files. Rather than relying on a central server to store an entire file, IPFS works by splitting up a file into chunks and storing these chunks across many nodes. The overall file and chunks are then identified by their hashes, which are uniquely generated using the contents of the file and each chunk. Using these hashes, IPFS then constructs a Merkle Directed Acyclic Graph, and the user can simply provide the overall file hash to trigger the protocol to traverse this graph and retrieve all of the chunks from the other nodes. IPFS is now a widely-used peer-to-peer file-sharing protocol due to its fault tolerance, security, and simplicity for users. As we see more of a push to a decentralized world, IPFS can become the standard for file sharing in the future and is therefore an important protocol that should be studied further in distributed systems.


## Project Goal
For our CS 262 final project, we seek to recreate a mini-version of the IPFS protocol and then simulate a proof of concept with storing and retrieving a simple text file.



## User Experience Walthrough
For IPFS, we will launch a simple website that has two pages. The first will allow a user to upload a file and store it on the IPFS servers. This first page will return an overall hash for the file that the user can later use for file retrieval. The second page will take the overall hash for the file and then print the reconstructed file onto the webpage. Hence, all the user needs to do is have their file on their computer and keep track of their hash to retrieve the file.

## Implementation Methodology
To implement IPFS, we will need to spin up multiple servers, come up with a way to allocate file chunks across different servers, and implement a way to recreate files across different machines. The sections below detail the choices we made implementing all of the features needed for our user experience.


### Initialization


### Uploading Files


### File retrieval


### Web Development

