import hashlib
import json
import os
import socket
import threading
from threading import Thread
import sys
import time
import random

# Define constants
BLOCK_SIZE = 1024
# Define a class to keep track of uploaded files
class FileStorage:
    def __init__(self):
        self._files = {}

    def add_file(self, file_path):
        file_hash = self._calculate_file_hash(file_path)
        self._files[file_hash] = file_path
        return file_hash

    def get_file(self, file_hash):
        if file_hash in self._files:
            return self._files[file_hash]
        else:
            return None
    
    def has_file(self, file_hash):
        return file_hash in self._files

    def _calculate_file_hash(self, file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()
            return hashlib.sha256(file_data).hexdigest()

# Define a class to represent a node in the IPFS network
class IPFSNode:
    def __init__(self, file_storage, address):
        self._file_storage = file_storage
        self._peers = set()
        self._address =  address

    def add_peer(self, peer_address):
        self._peers.add(peer_address)

    def remove_peer(self, peer_address):
        self._peers.remove(peer_address)

    def upload_file(self, file_path):
        # Split the file into smaller chunks
        file_chunks = self._split_file(file_path)
        # Create a Merkle DAG for the file
        file_dag = self._create_file_dag(file_chunks)
        # Add the file to the local storage
        file_hash = self._file_storage.add_file(file_path)
        # Broadcast the file to peers
        self._broadcast_file(file_dag)
        return file_hash

    def download_file(self, file_hash, output_file_path):
        # Look up the peers that have the file
        peers_with_file = self._lookup_file_peers(file_hash)
        # Request the file from each peer until successful
        for peer_address in peers_with_file:
            success = self._request_file_from_peer(file_hash, peer_address, output_file_path)
            if success:
                return True
        return False

    def _split_file(self, file_path):
        with open(file_path) as f:
            chunks = []
            while True:
                block = f.read(BLOCK_SIZE)
                if not block:
                    break
                chunks.append(block)
            return chunks

    def _create_file_dag(self, chunks):
        node_list = []
        for chunk in chunks:
            chunk_hash = hashlib.sha256(chunk).hexdigest()
            node_list.append({'Data': chunk, 'Hash': chunk_hash, 'Links': []})
            # send chunk to a random peer
            self._send_file_to_peer(chunk, random.choice(list(self._peers)))
        while len(node_list) > 1:
            new_node_list = []
            for i in range(0, len(node_list), 2):
                left_node = node_list[i]
                right_node = node_list[i+1] if i+1 < len(node_list) else left_node
                combined_data = left_node['Data'] + right_node['Data']
                combined_hash = hashlib.sha256(combined_data).hexdigest()
                combined_node = {'Data': combined_data, 'Hash': combined_hash, 'Links': [
                    {'Name': 'left', 'Hash': left_node['Hash']},
                    {'Name': 'right', 'Hash': right_node['Hash']}
                ]}
                new_node_list.append(combined_node)
            node_list = new_node_list
        return node_list[0]

    def _broadcast_file(self, file_dag):
        file_dag_json = json.dumps(file_dag)
        for peer_address in self._peers:
            self._send_file_to_peer(file_dag_json, peer_address)

    def _send_file_to_peer(self, file_dag_json, peer_address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer_address)
                s.sendall(b'UPLOAD')
                s.sendall(bytes(file_dag_json, 'utf-8'))
                s.recv(BLOCK_SIZE)  # Wait for peer to acknowledge receipt
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
                s.sendall(b'LOOKUP')
                s.sendall(bytes(file_hash, 'utf-8'))
                response = s.recv(BLOCK_SIZE).decode('utf-8')
                if response == 'FOUND':
                    return True
                else:
                    return False
            except:
                return False

    def _request_file_from_peer(self, file_hash, peer_address, output_file_path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(peer_address)
                s.sendall(b'DOWNLOAD')
                s.sendall(bytes(file_hash, 'utf-8'))
                file_dag_json = b''
                while True:
                    block = s.recv(BLOCK_SIZE)
                    if not block:
                        break
                    file_dag_json += block
                file_dag = json.loads(file_dag_json.decode('utf-8'))
                self._retrieve_file_from_dag(file_dag, output_file_path)
                return True
            except:
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
    ## add logic for peers to do all of the requested actions

    def _handle_peer(self, conn, addr):
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(BLOCK_SIZE)
                if not data:
                    break
                print('Received', repr(data))
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
        filename = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if not block:
                break
            filename += block
        filename = filename.decode('utf-8')
        hash = self.upload_file(filename)
        conn.sendall(bytes(hash, 'utf-8'))
        
    
    def _handle_client_download(self, conn):
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if not block:
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        output_file_path = file_hash + '.txt'
        self.download_file(file_hash, output_file_path)
        conn.sendall(b'ACK')

    def _handle_upload(self, conn):
        file_dag_json = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if not block:
                break
            file_dag_json += block
        file_dag = json.loads(file_dag_json.decode('utf-8'))
        self._file_storage.add_file(file_dag)
        conn.sendall(b'ACK')
    
    def _handle_lookup(self, conn):
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if not block:
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        if self._file_storage.has_file(file_hash):
            conn.sendall(b'FOUND')
        else:
            conn.sendall(b'NOT_FOUND')
    
    def _handle_download(self, conn):
        file_hash = b''
        while True:
            block = conn.recv(BLOCK_SIZE)
            if not block:
                break
            file_hash += block
        file_hash = file_hash.decode('utf-8')
        file_dag = self._file_storage.get_file(file_hash)
        file_dag_json = json.dumps(file_dag)
        conn.sendall(bytes(file_dag_json, 'utf-8'))
    
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
    ipfs_node.add_peer(('127.0.0.1', ports[0]))
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
    # take the test.txt file in frontend/ and upload it to the network
    if port == 50051:
        file_hash = ipfs_node.upload_file('test.txt')
        print('Uploaded file with hash: {}'.format(file_hash))