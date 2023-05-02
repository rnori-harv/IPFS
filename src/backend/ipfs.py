import hashlib
import json
import os
import socket
import threading
from threading import Thread
import sys
import time
from merkletools import MerkleTools
import random

# Define constants
BLOCK_SIZE = 256
# Define a class to keep track of uploaded files
class FileStorage:
    def __init__(self):
        self._files = {}

    def add_file(self, file_content):
        file_hash = self._calculate_file_hash(file_content)
        self._files[file_hash] = file_content
        return file_hash

    def get_file(self, file_hash):
        return self._files[str(file_hash)]
    
    def has_file(self, file_hash):
       return str(file_hash) in list(self._files.keys())

    def _calculate_file_hash(self, file_content):
        file_data = file_content.encode('utf-8')
        return hashlib.sha256(file_data).hexdigest()

# Define a class to represent a node in the IPFS network
class IPFSNode:
    def __init__(self, file_storage, address):
        self._file_storage = file_storage
        self._peers = set()
        self._address =  address
        self.dags = {}

    def add_peer(self, peer_address):
        self._peers.add(peer_address)

    def remove_peer(self, peer_address):
        self._peers.remove(peer_address)

    def upload_file(self, file_path):
        # Split the file into smaller chunks
        file_chunks = self._split_file(file_path)
        # Create a Merkle DAG for the file
        file_dag = self._create_file_dag(file_chunks)

        file_hash = file_dag.get_merkle_root()
        # Add the file to the local storage
        # store the merkle DAG on primary server
        return file_hash

    def download_file(self, file_hash, output_file_path):
        mt = self.dags[file_hash]
        leaf_count = mt.get_leaf_count()
        file_content = b''
        for i in range(leaf_count):
            leaf_hash = mt.get_leaf(i)
            peers_w_hash = self._lookup_file_peers(leaf_hash)
            if len(peers_w_hash) == 0:
                print('File not found')
                return
            # download the file from a random peer
            file_content += self._request_file_from_peer(leaf_hash, random.choice(peers_w_hash))
        
        file_content = file_content.decode('utf-8')
        with open(output_file_path, 'w') as f:
            f.write(file_content)

        return output_file_path

            


    def _split_file(self, file_path):
        with open(file_path, 'rb') as f:
            chunks = []
            while True:
                block = f.read(BLOCK_SIZE)
                if not block:
                    break
                chunks.append(block)
            return chunks

    def _create_file_dag(self, chunks):
        for chunk in chunks:
            self._send_file_to_peer(chunk, random.choice(list(self._peers)))
        chunks = [chunk.decode('utf-8') for chunk in chunks]
        mt = MerkleTools(hash_type = 'sha256')
        mt.add_leaf(chunks, True)
        mt.make_tree()
        self.dags[mt.get_merkle_root()] = mt
        return mt

    def _send_file_to_peer(self, chunk, peer_address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer_address)
                s.settimeout(10)  # Set a timeout of 10 seconds
                s.sendall(b'UPLOAD')
                try:
                    s.recv(BLOCK_SIZE)  # Wait for peer to acknowledge upload
                except socket.timeout:
                    print("Timed out waiting for COMMAND CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
                try:
                    s.sendall(chunk)
                    time.sleep(0.1)
                    s.sendall(b'DONE')
                    s.recv(BLOCK_SIZE)  # Wait for peer to acknowledge receipt of chunk
                except socket.timeout:
                    print("Timed out waiting for UPLOAD CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
                finally:
                    s.close()
            except:
                print('Failed to send file to peer: {}'.format(peer_address))

    def _lookup_file_peers(self, file_hash):
        peers_with_file = []
        for peer_address in self._peers:
            if self._check_peer_for_file(file_hash, peer_address):
                peers_with_file.append(peer_address)
        return peers_with_file

    def _check_peer_for_file(self, file_hash, peer_address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer_address)
                s.settimeout(10)  # Set a timeout of 10 seconds
                s.sendall(b'LOOKUP')
                try:
                    s.recv(BLOCK_SIZE)  # Wait for peer to acknowledge lookup
                except socket.timeout:
                    print("Timed out waiting for LOOKUP CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
                try:
                    s.sendall(bytes(file_hash, 'utf-8'))
                    time.sleep(0.1)
                    s.sendall(b'DONE')
                    response = s.recv(BLOCK_SIZE)
                    if response == b'FOUND':
                        return True
                    else:
                        return False
                except socket.timeout:
                    print("Timed out waiting for LOOKUP CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
            except:
                print("FAILING LOOKUP")
                return False

    def _request_file_from_peer(self, file_hash, peer_address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer_address)
                s.sendall(b'DOWNLOAD')
                try:
                    s.recv(BLOCK_SIZE)  # Wait for peer to acknowledge download
                except socket.timeout:
                    print("Timed out waiting for DOWNLOAD CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
                try:
                    s.sendall(bytes(file_hash, 'utf-8'))
                    time.sleep(0.1)
                    s.sendall(b'DONE')
                    file_content = b''
                    while True:
                        block = s.recv(BLOCK_SIZE)
                        if block == b'DONE':
                            break
                        file_content += block
                    return file_content
                except socket.timeout:
                    print("Timed out waiting for DOWNLOAD CONFIRMATION from peer")
                    s.close()
                    sys.exit(1)
            except:
                print("FAILING DOWNLOAD")
                return False

    def _retrieve_file_from_dag(self, file_dag, output_file_path):
        chunks = []
        for link in file_dag['Links']:
            if link['Name'] == 'left':
                chunks.extend(self._retrieve_file_from_dag(link, output_file_path))
            elif link['Name'] == 'right':
                chunks.extend(self._retrieve_file_from_dag(link, output_file_path))
        chunks.append(file_dag['Data'])
        with open(output_file_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)

    def _handle_peer(self, conn, addr):
        with conn:
            while True:
                data = conn.recv(BLOCK_SIZE)
                if not data:
                    break
                if data == b'CLIENTUPLOAD':
                    self._handle_client_upload(conn)
                elif data == b'CLIENTDOWNLOAD':
                    self._handle_client_download(conn)
                elif data == b'UPLOAD':
                    self._handle_upload(conn)
                elif data == b'LOOKUP':
                    self._handle_lookup(conn)
                elif data == b'DOWNLOAD':
                    self._handle_download(conn)
                else:
                    print('Unknown command: {}'.format(data))
    
    
    def _handle_client_upload(self, conn):
        conn.sendall(b'ACK')
        filename = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if block == b'DONE':
                break
            filename += block
        filename = filename.decode('utf-8')
        print("SERVER RECEIVED FILENAME: {}".format(filename))
        hash = self.upload_file(filename)
        conn.sendall(bytes(hash, 'utf-8'))
        
    
    def _handle_client_download(self, conn):
        conn.sendall(b'ACK')
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if block == b'DONE':
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        output_file_path = file_hash + '.txt'
        print("starting download to " + str(output_file_path))
        self.download_file(file_hash, output_file_path)
        conn.sendall(output_file_path.encode('utf-8'))

    def _handle_upload(self, conn):
        time.sleep(0.5)
        conn.sendall(b'ACK')
        file_content = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if block == b'DONE':
                break
            file_content += block
        hash = self._file_storage.add_file(file_content.decode('utf-8'))
        print('File hash: {}'.format(hash))
        print(str(self._address) + ': File added to storage')
        #print(self._file_storage.get_file(hash))
        conn.sendall(b'DONE')
    
    def _handle_lookup(self, conn):
        conn.sendall(b'ACK')
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if block == b'DONE':
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        if self._file_storage.has_file(file_hash):
            conn.sendall(b'FOUND')
        else:
            conn.sendall(b'NOT_FOUND')
    
    def _handle_download(self, conn):
        conn.sendall(b'ACK')
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if block == b'DONE':
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        file_content = self._file_storage.get_file(file_hash)
        conn.sendall(file_content.encode('utf-8'))
        time.sleep(0.1)
        conn.sendall(b'DONE')
    
    def _start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self._address)
            s.listen()
            while True:
                conn, addr = s.accept()
                self._handle_peer(conn, addr)



def serve(port):
    file_storage = FileStorage()
    addr = ('127.0.0.1', port)
    ipfs_node = IPFSNode(file_storage, addr)
    ports = [50051, 50052, 50053, 50054, 50055, 50056, 50057, 50058]
    ipfs_node.add_peer(('127.0.0.1', ports[1]))
    ipfs_node.add_peer(('127.0.0.1', ports[2]))
    ipfs_node.add_peer(('127.0.0.1', ports[3]))
    ipfs_node.add_peer(('127.0.0.1', ports[4]))
    ipfs_node.add_peer(('127.0.0.1', ports[5]))
    ipfs_node.add_peer(('127.0.0.1', ports[6]))
    ipfs_node.add_peer(('127.0.0.1', ports[7]))

    t = Thread(target=ipfs_node._start_server)
    t.start()
    time.sleep(5)
    # take the test.txt file in frontend/ and upload it to the network using primary server (port 50051)
    '''
    if port == 50051:
        file_hash = ipfs_node.upload_file('test.txt')
        # hash the file with SHA-256 and print it
        filename = 'test.txt'
        with open(filename, 'rb') as f:
            # Create a SHA-256 hash object
            sha256 = hashlib.sha256()
            
            # Read the file in chunks and update the hash object
            while True:
                data = f.read(4096)
                if not data:
                    break
                sha256.update(data)

        # Print the SHA-256 hash as a hexadecimal string

        print('Uploaded file with hash: {}'.format(file_hash))
        # download the file from the network
        output_file_path = file_hash + '.txt'
        ipfs_node.download_file(file_hash, output_file_path)
    '''