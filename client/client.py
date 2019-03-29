# Author Forest Vey
import socket, sys, os

def sendFileSize(fileSize):
    fileSizePacket = bytearray(8)
    fileSizePacket[0] = (fileSize >> 56) & 255
    fileSizePacket[1] = (fileSize >> 48) & 255
    fileSizePacket[2] = (fileSize >> 40) & 255
    fileSizePacket[3] = (fileSize >> 32) & 255
    fileSizePacket[4] = (fileSize >> 24) & 255
    fileSizePacket[5] = (fileSize >> 16) & 255
    fileSizePacket[6] = (fileSize >> 8) & 255
    fileSizePacket[7] = fileSize & 255
    s.send(fileSizePacket)


# 1. create the socket using STREAM
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. build the packet.
host = sys.argv[1]
port = int(sys.argv[2])
operation = sys.argv[3]
fileName = sys.argv[4]
done = 'done'

# connect to port/host requested in command line
s.connect( (host,port) )

if operation == 'GET':
    ready = ""
    
    # Receive ready signal to begin operations between client/server
    while ready != "READY":
        ready = ready + s.recv(1024).decode("utf-8")

    s.send(operation.encode('utf-8') + ' '.encode('utf-8') + fileName.encode('utf-8'))

    ok = ''
    while ok != 'OK' and ok != ('ERROR: ' + fileName + ' does not exist'):
        ok = ok + s.recv(1024).decode('utf-8')
    if ok != ('ERROR: ' + fileName + ' does not exist'):
        
        s.send(ready.encode('utf-8'))

        # receive file size from the client as 8 byte integer
        fileSizeArray = s.recv(1024)
        fileSize = (int(fileSizeArray[0]) << 56 | int(fileSizeArray[1]) << 48 
        | int(fileSizeArray[2]) << 40 | int(fileSizeArray[3]) << 32 
        | int(fileSizeArray[4]) << 24 | int(fileSizeArray[5]) << 16 
        | int(fileSizeArray[6]) << 8 | int(fileSizeArray[7])) 

        s.send('OK'.encode('utf-8'))

        # Create file and begin copying bytes from server
        f = open(fileName, 'wb')
        if not os.path.exists(fileName):
            print('client error: unable to create file' + fileName)
            s.close()
            sys.exit()

        print('client receiving file ' + fileName + ' (' + str(fileSize) + ' bytes)')
        fileCheck = 0
        while int(fileCheck) < int(fileSize):

            if (int(fileSize) - (fileCheck)) < 1024:
                toWrite = s.recv(int(fileSize) - int(fileCheck))
            else:
                toWrite = s.recv(1024)
            fileCheck += len(toWrite)
            f.write(toWrite)
         
        while not "DONE" in done:
            done = done + s.recv(1024).decode("utf-8")
        print('Complete')

        f.close()
        s.close()
    else:
        ok = ok.split('ERROR: ',1)
        ok = ok[1]
        print('server error: ' + ok)
        s.close()

    # Packet is sent over to be written to file
elif operation == 'PUT':
    ready = ""
    
    # Receive ready signal to begin operations between client/server
    while ready != "READY":
        ready = ready + s.recv(1024).decode("utf-8")

    # Server responds when ready for file
    s.send(operation.encode('utf-8') + ' '.encode('utf-8') + fileName.encode('utf-8'))

    ok = ''
    while ok != 'OK' and ok != ('ERROR: unable to create file ' + fileName):
        ok = ok + s.recv(1024).decode('utf-8')

    if ok == 'OK':

        # Open file in binary format in preparation for sending
        f = open(fileName, 'rb')
        
        # Send file size to client as signed 32 bit integer
        fileSize = os.path.getsize(fileName)
        sendFileSize(fileSize)

        # send filesize as signed 8 byte integer
        try:
            # print('reading first 1024')
            packet = f.read(1024)
            print('client sending file ' + fileName + ' (' + str(fileSize) + ' bytes)')
            while True:
                s.send(packet)
                packet = f.read(1024)
                # print('reading bytes')
                if not packet:
                    break
        finally:
            f.close()
            done = ""
            while not "DONE" in done:
                done = done + s.recv(1024).decode("utf-8")
            print('Complete')
            s.close()
    else:
        ok = ok.split('ERROR: ',1)
        ok = ok[1]
        print('server error: ' + ok)
        s.close()


elif operation == 'DEL':
    ready = ""
    
    # Receive ready signal to begin operations between client/server
    while ready != "READY":
        ready = ready + s.recv(1024).decode("utf-8")

    s.send(operation.encode('utf-8') + ' '.encode('utf-8') + fileName.encode('utf-8'))

    
    print('client deleting file ' + fileName)
    done = ""
    while done != 'DONE' and done != ('ERROR: ' + fileName + ' does not exist'):
        done = done + s.recv(1024).decode("utf-8")

    if done == 'DONE':
        # Server responds when ready for file
        print('Complete')
        s.close()
    else:
        done = done.split('ERROR: ',1)
        done = done[1]
        print('server error: ' + done)
        s.close()