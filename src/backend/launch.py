# do the ipfs serve() method on 7 differnet ports: 50051 - 50058. Do this in a separate process for each port.


from multiprocessing import Process
import ipfs
import sys

# launches 8 ipfs servers on ports 50051 - 50058
if __name__ == '__main__':
    ports = [50051, 50052, 50053, 50054, 50055, 50056, 50057, 50058]
    for i in range(8):
        p = Process(target=ipfs.serve, args=(ports[i],))
        p.start()