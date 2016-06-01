import socket, time, threading, re


class highroller(object):

    def __init__(self):
        # Here we define some basic instance variables as well as setting up our socket.
        self.tLock = threading.Lock()
        self.shutdown = False
        self.HOST = '127.0.0.1'
        self.PORT = 0
        self.SERVER = ('127.0.0.1', 5000)

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind((self.HOST, self.PORT))
        self.sock.setblocking(True)
        self.recievingThread = threading.Thread(target=self.recieving) # Do we need to pass in self?
        self.joined = False

        # Now we set up our encoding and decoding "cyphers". Note to self. 'I' in the re.compile function call is to
        # ignore the case of the matching string. This is so someone could type /QUIT or /QUiT
        # Note. I see the regular expressions as a potential point of conflict for the application so it must be tested
        # well.

        self.encodings = [(re.compile('^/bet', I),'be%'), (re.compile('^/quit', I), 'co%'), (re.compile('^/hit', I), 'ht%'),
                          (re.compile('^/stand', I), 'sd%'), (re.compile('^/pinfo', I), 'pl%'),
                          (re.compile('^/ginfo', I), 'ul%')]

        self.decodings = {}


        # Here the programme handles the joining the server. This was originally in the main loop but is now in the
        # initialisation of the class.
        self.handle = str(input('Welcome to your BJNet client. To join the server, please the handle you\'d ' +
                                'like to use in the chat room!\n\n> '))
        while not self.joined:
            self.sock.sendto(str.encode('jo&'+self.handle), self.SERVER)
            data, null = self.sock.recvfrom(1024) # Now we recieve back whether or not the username is good
            if data.decode('utf-8') == '300': # 300 - HTTP Code for Accepted. We've found the server and it's accepted us.
                print('300')
                self.joined = True
                print('Welcome Message')
            elif data.decode('utf-8') == '409': # 409 Wants us to keep choosing user-names
                print('409')
                self.handle = str(input('The username you have chosen is already in use. Please select a new' +
                                             ' username\n\n> '))


    def recieving(self):
        pass

    def encoder(self, message):
        '''A message is to consist of two parts a prefix and then a message body. Some messages that are simple commands
            will only have a prefix as there is no need to have a lengthy message. The prefix is seperated from the main
            body with an '&' symbol.

            A guide to what prefixes are used in this protocol is below.

            ch - Chat Message. Server simply logs this and relays message to all connected clients
                Format of a ch message is ch MESSAGE. Only MESSAGE is relayed to all clients.

                NOTE: Any server instructions are sent as chat protocol messages.

            co - Cashout. User leaves table. Connection is closed.

            ht - Hit Me. User is requesting a card. Changes to game-state are first applied server side and then are
            communicated to the player

            sd - Player stands locking in their current score

            bet - This prefix handles betting

                bet AMOUNT

            ul - A server side query to send all public information about the table to the requesting player

            pl - Similar to the previous command except it returns all private information about the requesting player to
            the player'''

        # We start by splitting the first word off from the rest of the message and checking if it matches any one of
        # the outgoing prefixes. If it does not it is assumed to be a chat message and the ch prefix is appended to the
        # message
        pre, null, message = message.partition(' ')

        # Help is handled locally
        if pre == '/help':
            self.help()
            return

        # We cycle through each of our potential prefixes looking for a match. Should a match be found, we use the
        # correct prefix and then we send the message out over the wire.
        for regex_tuple in self.encodings:
            if regex_tuple[0].fullmatch(pre):
                pre = regex_tuple[1]

                # We may have to do something with our thread lock here. I'm not too certain.
                self.sock.sendto(str.encode(pre + message), self.HOST) # Not sure of we just send to the host or the
                # sever tuple
                return

        # If we've made it out of the loop we know that we have a chat message so we send the following.
        self.sock.sendto((str.encode('ch%' + self.handle + ':' + pre + message)), self.HOST) # See Comment on Line 95
        return









    def decoder(self):
        pass


    def help(self):
        print('Help Documentation. Documentation will likely be read in from a text file for the sake of orderly code.')

    def main_loop(self):
        '''This is the main loop that handles player interface. Joining the server may be mapped out to another method
        but for now it is simply a part of the main loop It may also become part of the __init__ method.'''

    while True:
        message = str(input('Name: '))
        self.encoder(message) # For simplicity in the main loop, sending the message is handled by the encoder









    myplayer = highroller()
    myplayer.main_loop()

main()