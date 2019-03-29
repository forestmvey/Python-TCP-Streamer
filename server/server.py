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
    client.sendto(fileSizePacket, info)


port = int(sys.argv[1])
verbose = False

if sys.argv[-1] == '-v':
    verbose = True

# Create the socket object using STREAM
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to the port. Using "" for the interface so it binds to
# all known interfaces, including "localhost".
s.bind( ("", port) )

if verbose == True:
    print('waiting on port ' + str(port))
s.listen(0)
done = 'DONE'
ready = "READY"


# Servers stay open -- they handle a client, then loop back
# to wait for another client.
while True:
    client, info = s.accept()
    if verbose == True:
        print('server connected to client ' + info[0] + ':' + str(port))

    # Server is ready to send the file
    client.send(ready.encode('utf-8'))
    operation = client.recv(1024).decode('utf-8')
    # split operation off string to separate fileName
    fileName = operation.split()
    fileName = fileName[1]

    if operation.find("GET") != -1:

        if verbose == True:
            print('server receiving request: ' + fileName)

        client.send('OK'.encode('utf-8'))

        ready = ''
        while ready != 'READY':
            ready = ready + client.recv(1024).decode('utf-8')
        
        # Send file size to client as signed 32 bit integer
        fileSize = os.path.getsize(fileName)
        sendFileSize(fileSize)

        ok = ''
        while ok != 'OK':
            ok = ok + client.recv(1024).decode('utf-8')


        if os.path.exists(fileName):

            # Open file in binary format in preparation for sending
            f = open(fileName, 'rb')
        
            
            # send filesize as signed 8 byte integer
            try:
                # print('reading first 1024')
                packet = f.read(1024)
                if verbose == True:
                        print('server sending ' + str(fileSize) + ' bytes')
                while True:
                    client.send(packet)
                    packet = f.read(1024)
                    if not packet:
                        break
            finally:
                f.close()
                client.send(done.encode('utf-8'))
                client.close()
        else:
            client.send(('ERROR: ' + fileName + ' does not exist').encode('utf-8'))
            client.close()
        
    elif operation.find("PUT") != -1:

        if verbose == True:
            print('server receiving request: ' + fileName)


        try: 
            f = open(fileName, 'wb')
            # Create file and begin copying bytes from server
            if os.path.exists(fileName):

                client.send('OK'.encode('utf-8'))

                # receive file size from client as 8 byte integer
                fileSizeArray = client.recv(1024)
                fileSize = (int(fileSizeArray[0]) << 56 | int(fileSizeArray[1]) << 48 | 
                int(fileSizeArray[2]) << 40 | int(fileSizeArray[3]) << 32 | 
                int(fileSizeArray[4]) << 24 | int(fileSizeArray[5]) << 16 | 
                int(fileSizeArray[6]) << 8 | int(fileSizeArray[7])) 
            
                fileCheck = 0
                while int(fileCheck) < int(fileSize):
                    if (int(fileSize) - (fileCheck)) < 1024:
                        toWrite = client.recv(int(fileSize) - int(fileCheck))
                        if verbose == True:
                            print('server receiving ' + str(len(toWrite)) + ' bytes')
                    else:
                        toWrite = client.recv(1024)
                        if verbose == True:
                            print('server receiving ' + str(len(toWrite)) + ' bytes')
                    fileCheck += len(toWrite)
                    f.write(toWrite)

                client.send(done.encode('utf-8'))
                client.close()
                f.close()
        
        except IOError:
            client.send(('ERROR: unable to create file ' + fileName).encode('utf-8'))
            client.close()
    
    elif operation.find("DEL") != -1:

        if verbose == True:
            print('server receiving request: ' + fileName)

        if os.path.exists(fileName):
            if verbose == True:
                print('server deleting file ' + fileName)
            os.remove(fileName)
            client.send(done.encode('utf-8'))
            client.close()
        else:
            client.send(('ERROR: ' + fileName + ' does not exist').encode('utf-8'))
            client.close()

client.close()