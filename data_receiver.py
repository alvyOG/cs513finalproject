import sys
import socket
import signal

RECV_BUFFER_SIZE = 4096
QUEUE_LENGTH = 10
isBreak = False

# Need a kill signal handler to prevent server from going down unless killed
def breakHandler(signum,frame):
    global isBreak
    isBreak = True

def server(server_port):
    # Open socket
    HOST = '127.0.0.1'
    PORT = server_port
    global isBreak
    signal.signal(signal.SIGINT, breakHandler)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind on port and listen for messages
    s.bind((HOST, PORT))
    s.listen(QUEUE_LENGTH)
    # While not receiving a kill signal do:
    while not isBreak:
        # Accept next connection
        (c, addr) = s.accept()
        # While connected
        while True:
            # Receive data on the socket until no data left or buffer full
            data = c.recv(RECV_BUFFER_SIZE)
            datasplit = data.split(',')
            if not data:
                break
            else:
                # If there is data write to stdout and flush
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
        # Close connection once all the data is read from that connection
        c.close()
    # Close the socket when server receives a kill signal
    s.close()
    
def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: server-python.py [Server Port]")
    server_port = int(sys.argv[1])
    server(server_port)

if __name__ == "__main__":
    main()
