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

        # These two lines handle local checking of whether or not a player has gone bust or chosen to stand. It cuts
        # down on server - load because the simple check can be done client side without need for the server to do
        # anything.

        # TODO Ensure that these two flags are correctly implemented clientside
        self.bust = False
        self.stand = False


        # Now we set up our encoding and decoding "cyphers". Note to self. 'I' in the re.compile function call is to
        # ignore the case of the matching string. This is so someone could type /QUIT or /QUiT
        # Note. I see the regular expressions as a potential point of conflict for the application so it must be tested
        # well.

        self.encodings = [(re.compile('^/bet', re.I),'be&'), (re.compile('^/quit', re.I), 'co&'), (re.compile('^/hit', re.I), 'ht&'),
                          (re.compile('^/stand', re.I), 'sd&'), (re.compile('^/pinfo', re.I), 'pl&'),
                          (re.compile('^/ginfo', re.I), 'ul&')]

        self.decodings = {}

        # Here the programme handles the joining the server. This was originally in the main loop but is now in the
        # initialisation of the class.


        self.handle = str(input('Welcome to your BJNet client. To join the server, please the handle you\'d ' +
                                'like to use in the chat room!\n\n> '))
        while not self.joined:
            self.sock.sendto(str.encode('jo&'+self.handle), self.SERVER)
            data, null = self.sock.recvfrom(1024) # Now we recieve back whether or not the username is good
            if data.decode('utf-8') == '300':  # 300 - HTTP Code for Accepted. We've found the server and it's accepted us.
                print('300')
                self.joined = True
                print('Welcome Message')
            elif data.decode('utf-8') == '409': # 409 Wants us to keep choosing user-names
                print('409')
                self.handle = str(input('The username you have chosen is already in use. Please select a new' +
                                          ' username\n\n> '))



    def recieving(self):
        while not self.shutdown:
            try:
                self.tLock.acquire()
                while True:
                    message, addr = self.sock.recvfrom(2048)
                    self.decoder(message)
            except:
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
                self.sock.sendto(str.encode(pre + message), self.SERVER) # Not sure of we just send to the host or the
                # sever tuple
                return

        # If we've made it out of the loop we know that we have a chat message so we send the following.
        self.sock.sendto((str.encode('ch&' + self.handle + ' : ' + pre + ' ' + message)), self.SERVER)
        return


    def decoder(self, message):
        '''As is well established: messages consist of two things a prefix and then the body of the message Below,
        I detail the potential codes that the server could potentially send to the client: the form the message will take
        and any other documentation I deem necessary for understanding the workings of this programme.

        de - Serer deals a card to the player. This is issued in response by the player to "hit me".
            Message will take the form de&VALUE with the value in caps being the most value of the card dealed.
            If there message sent has two values (delimited by a ;) then the first value is the face down card while
            the second is the face up card (in a new game)

        sd - The server acknowledges the players request to stands

        bu - The server has informed that the player has gone bust

        New Round - Puts out the call that it is a new round. Players are instructed to make their bets.
            nr& Upon seeing this client side bust and stand values are also reset.

        New Credits for winning a bet
            nc&VALUE - Where VALUE is the amount of credits the player has added to their total. Since money already bet
            is stored seperately it accounts for both this and winnings.

        st - Stand Confirmation Message. If it is followed by a 21 it means that the server has automatically made the
        player stand because the player reached 21. If it's followed by bj it's because the player got blackjack.

        Relayed Chat Message
            ch - Message

        ng& - This is the

        ul - When sent from the server this is a response to a query for public information about the current game.

        pl - Response to a query about player information in the game'''


    def help(self):
        print('Help Documentation. Documentation will likely be read in from a text file for the sake of orderly code.')

    def main_loop(self):
        '''This is the main loop that handles player interface. Joining the server may be mapped out to another method
        but for now it is simply a part of the main loop It may also become part of the __init__ method.'''

        while True:
            message = str(input('> '))
            self.encoder(message) # For simplicity in the main loop, sending the message is handled by the encoder






def main():
    myplayer = highroller()
    myplayer.main_loop()

main()