import sys
import socket
import csv

SEND_BUFFER_SIZE = 2048

def sender(server_ip, server_port, dataset, batch_size, message_count):
    #Open socket
    HOST = server_ip
    PORT = server_port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Check for connection, keep client up and continue checking if not
    connected = False
    while not connected:
        try:
            s.connect((HOST, PORT))
            connected = True
        except Exception as e:
            pass
    # When connected, open data set and send batches
    while True:
        # send data
        csvfile = open(dataset, newline='\n')
        csvreader = csv.reader(csvfile)
        # remove headers
        headers = csvreader.__next__()
        msgcounter = 0
        while msgcounter < message_count:
            message = ""
            batchcounter = 0
            while batchcounter < batch_size:
                message += ','.join(csvreader.__next__())+','
                batchcounter += 1
            s.send(message[0:len(message)-1])
            msgcounter += 1
        csvfile.close()
        break
    # close the socket when done sending
    s.close()

def printSendData(dataset, batch_size, message_count):
    csvfile = open(dataset, newline='\n')
    csvreader = csv.reader(csvfile)
    # remove headers
    headers = csvreader.__next__()
    msgcounter = 0
    while msgcounter < message_count:
        message = ""
        batchcounter = 0
        while batchcounter < batch_size:
            message += ','.join(csvreader.__next__())+','
            batchcounter += 1
        print(message[0:len(message)-1])
        msgcounter += 1
    csvfile.close()

def main():
    if len(sys.argv) != 6:
        sys.exit("Usage: data_sender.py [IP] [Port] [foo.csv] [Batch Size] [Msg Count]")
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    dataset = sys.argv[3]
    batch_size = int(sys.argv[4])
    message_count = int(sys.argv[5])
    sender(server_ip, server_port, dataset, batch_size, message_count)
    #printSendData(dataset, batch_size, message_count)

if __name__ == "__main__":
    main()
