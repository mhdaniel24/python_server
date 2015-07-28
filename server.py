
import socket
import os
from threading import Thread
import sys


class handleConnection:
	def __init__(self, conn):
		self.conn = conn
		self.uname = ''
		self.type = 'A'#initial mode set to ascii
		self.passw = ''
		self.orig_path = os.getcwd()#used to reset path to initial path when user finishes connection
	
	def command_user(self, un):#receives username and saves it in order to be compared with password to see if they are equal
		self.uname = un
		self.conn.send('331 User name okay, need password.\n')
		
	def command_pass(self, passw):#receiving password and comparing it with username	
		self.passw = passw
		if self.uname == self.passw:
			self.conn.send('230 User logged in, proceed.\n')
		else:
			self.conn.send('530 Login incorrect\n')
	
	def command_syst(self):#command received after logged in asking server type
		self.conn.send('215 UNIX type\n')
		
	def command_pwd(self):#getting current working directory
		self.conn.send(os.getcwd() +'\n')
		
	def command_quit(self):#closing connection and setting path to the original path
		self.conn.send('221 Service closing control connection.\n')
		self.conn.close()
		os.chdir(self.orig_path) 
	
	def command_mkd(self, path):#creating directory or telling the client if the path is incorrect
            try:
		        os.mkdir(path)
		        self.conn.send('257 ' + path + ' created.\n')
            except OSError:
                self.conn.send('501 Syntax error in parameters or arguments.\n')
                pass
		
	def command_cwd(self, path):#changing directory or telling the client if the directory he specified does not exist
            try:
		        os.chdir(path)
		        self.conn.send('250 Requested file action okay, completed.\n')
            except OSError:
                    self.conn.send('501 Syntax error in parameters or arguments.\n')
                    pass
		
	def command_dele(self, path):#deleting the file or telling the ftp server that there is an error in the arguments since the file does not exist
            if os.path.exists(path):
		        os.remove(path)
		        self.conn.send('250 Requested file action okay, completed.\n')
            else:
                self.conn.send('501 Syntax error in parameters or arguments.\n')
	
	def command_type(self, t):#command received in the middle of starting receiving a file (data transfer)
		#print 'the type is' + t
		self.type = t
		self.conn.send('200 Command okay.\n')
		
	def command_port(self,port):#receiving command PORT and calculating the port for data transfer
		temp = port.split(',')
		self.data_addr = temp[0]+'.'+temp[1]+'.'+temp[2]+'.'+temp[3]
		self.data_port = (int(temp[4]) << 8) + int(temp[5])#8 right shift of the bits of the first number and then append at the end the second number(+ which stands for addition but since the number was shifted by 8 bits it only has 0s at the begining so + behaves as append)			
		self.conn.send('200 Command okay.\n')
		
	def command_retr(self, path):#sending file
            if os.path.exists(path):
            	if self.type == 'I':
            		f = open(path, 'rb')
            	else:
            		f = open(path, 'r')
            	
            	self.conn.send('150 File status okay; about to open data connection.\n')
            	toBeSent = f.read(1024)
            	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            	s.connect((self.data_addr, self.data_port))
            	while toBeSent:
            		s.send(toBeSent)
            		toBeSent = f.read(1024)
            	s.close()
            	f.close()
            	self.conn.send('226 Closing data connection. File transfer successful.\n')
                    	

            else:
                self.conn.send('501 Syntax error in parameters or arguments.\n')
		
	def command_stor(self, filename):#receiving file
		if self.type == 'I':
			f = open(filename, 'wb')
		else:
			f = open(filename, 'w')
			
		

		self.conn.send('150 File status okay; about to open data connection.\n')
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.data_addr, self.data_port))
		
		while 1:
			toBeStored = s.recv(1024)
			if toBeStored:
				f.write(toBeStored)
			else:
				break
		
		s.close()
		f.close()
		self.conn.send('226 Closing data connection. File transfer successful.\n')

        def command_missing(self):#command not implemented
            self.conn.send('502 Command not implemented.\n')
			
#Every thread will be executing this function which receives the command and arguments and decides which function from handleConnection to call
def newConnection(conn):
    connhelper = handleConnection(conn)#creating class that handles commands
    conn.send('220 Service ready for new user\n')#connection stablished wating for username
    BUFFER_SIZE = 1024#max size of buffer to be received
    
    #loop that receives every command as a string modifies it as a list and decides what to do with the command and its arguments (if any) 
    while 1:
       
        if conn:
            
            data = conn.recv(BUFFER_SIZE)#receiving command
            command_list = data.split(' ')#separating line into command and arguments
            
            #print command_list
				#Every if statement decides if the command is any of the implemented commands        
            if command_list[0][:4] == 'USER':
            	command_list[1] = command_list[1].split('\r')[0] 
            	connhelper.command_user(command_list[1])
            elif command_list[0][:4] == 'PASS':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_pass(command_list[1])
            elif command_list[0][:4] == 'SYST':
            	connhelper.command_syst()
            elif command_list[0][:3] == 'PWD':
            	connhelper.command_pwd()
            elif command_list[0][:4] == 'QUIT':
            	connhelper.command_quit()
            	break;
            elif command_list[0][:3] == 'MKD':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_mkd(command_list[1])
            elif command_list[0][:3] == 'CWD':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_cwd(command_list[1])
            elif command_list[0][:4] == 'DELE':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_dele(command_list[1])
            elif command_list[0][:4] == 'TYPE':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_type(command_list[1])
            elif command_list[0][:4] == 'PORT':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_port(command_list[1])
            elif command_list[0][:4] == 'RETR':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_retr(command_list[1])
            elif command_list[0][:4] == 'STOR':
            	command_list[1] = command_list[1].split('\r')[0]
            	connhelper.command_stor(command_list[1])
            else:
                connhelper.command_missing()
                
            



#main

#Creating socket and listening------------------------
if len(sys.argv) != 2:
	print('Try:')
	print('python server.py PORT_NUMBER')
	quit()

TCP_IP = 'localhost'
TCP_PORT = int(sys.argv[1])
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
#-----------------------------------------------------

#Loop watting for new connections (accepts connection, creates thread, and starts thread)-------------------------
while 1:
	
    conn, addr = s.accept()
    
    thread = Thread(target = newConnection, args = (conn, ))
    thread.start()
#------------------------------------------------------------------------------------------------------------------
