from flask import Flask, render_template, request
import socket
import os
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# retrieve page
@app.route('/ret', methods=['GET'])
def retrieve():
    return render_template('ret.html')

# upload file page
@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    # Save the file to disk
    uploaded_file.save(filename)
    # get path of the uploaded file
    path = os.path.abspath(filename)
    # connect to IPFS server and upload file
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # keep trying to connect to server until it is up
    while True:
        try:
            s.connect(('127.0.0.1', 50051))
            break
        except ConnectionRefusedError:
            continue

    s.sendall(b'CLIENTUPLOAD')
    s.settimeout(15)
    try:
        s.recv(1024)
    except socket.timeout:
        return 'Error: Could not connect to server'
    
    print(path)
    s.sendall(bytes(path, 'utf-8'))
    time.sleep(0.1)
    s.sendall(b'DONE')
    # wait for hash from server
    # print hash
    hash = s.recv(1024)
    hash = hash.decode('utf-8')
    s.close()
    return 'File uploaded successfully. Hash: ' + hash

# make the app route /retrieve + the value of hash
@app.route('/retrieve', methods=['GET'])
def retrieve_file():
    hash_value = request.args.get('hash')
    # connect to IPFS server and retrieve file
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # keep trying to connect to server until it is up
    while True:
        try:
            s.connect(('127.0.0.1', 50051))
            break
        except ConnectionRefusedError:
            continue
    
    s.sendall(b'CLIENTDOWNLOAD')
    s.settimeout(15)
    try:
        s.recv(1024)
    except socket.timeout:
        return 'Error: Could not connect to server'
    s.sendall(bytes(hash_value, 'utf-8'))
    time.sleep(0.1)
    s.sendall(b'DONE')

    # wait for path from server
    # print path
    path = s.recv(1024)
    path = path.decode('utf-8')
    # print the contents of the file onto the page
    path = '../backend/' + path
    with open(path, 'r') as f:
        contents = f.read()
    s.close()
    return contents

        

if __name__ == '__main__':
    app.run(debug=True)