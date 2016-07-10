import socket
import re
import threading
import time


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

        # Now we set up our encoding and decoding "cyphers". Note to self. 'I' in the re.compile function call is to
        # ignore the case of the matching string. This is so someone could type /QUIT or /QUiT
        # Note. I see the regular expressions as a potential point of conflict for the application so it must be tested
        # well.
        self.encodings = [(re.compile('^/bet', re.I),'be&'), (re.compile('^/quit', re.I), 'co&'), (re.compile('^/hit', re.I), 'ht&'),
                          (re.compile('^/stand', re.I), 'sd&'), (re.compile('^/pinfo', re.I), 'pl&'),
                          (re.compile('^/ginfo', re.I), 'ul&'), re.compile('^/pinfo', re.I), re.compile('^/force'),]

        self.dispatch_prefixes = {'ch': self.print_chat, 'cb': self.print_bet_confirm, 'st': self.print_stand_confirm,
                                  'nc': self.print_newcard, 'br': self.print_broadcast, 'ac': self.print_ace,
                                  'ui': self.print_user_info}
        # TODO Complete this list.

        # Here the programme handles the joining the server. This was originally in the main loop but is now in the
        # initialisation of the class.


        self.joined = False
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

        threading.Thread(target=self.recieving).start()  # Do we need to pass in self?


    def recieving(self):
        while True:
            # self.tLock.acquire()
            message, addr = self.sock.recvfrom(2048)
            message = message.decode('utf-8')
            self.decoder(message)


    def decoder(self, message):
        '''This decoder handles all incomming messages. For complete details on the codec employed by this programme
        take a peak at CodecDescriptions.txt'''
        pre, null, message = message.partition('&')
        self.dispatch_prefixes[pre](msg = message) # We don't need to include address since it always goes through
        # the server


    def encoder(self, message):
        '''A message is to consist of two parts a prefix and then a message body. Some messages that are simple commands
            will only have a prefix as there is no need to have a lengthy message. The prefix is seperated from the main
            body with an '&' symbol. '''

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

    # Below is a host of methods that allow the client to correctly handle and display any incoming messages.

    def print_chat(self, **kwargs):
        'This method prints chat messages. It mostly exists so that the rest of the decoder plays nice'
        print(kwargs['msg'])

    def print_newcard(self, **kwargs):
        'This method handles and correctly formats a message when the end user gets a new card'
        card, null, total = kwargs['msg'].partition(_)
        print("You have been dealt a " + str(card) + ". This brings the total value of your cards to" + \
                str(total))


    def print_user_info(self, **kwargs):
        '''This method handles and formats user information. It only handles one
        user at a time (requests, even whole table requests are sent piece meal.'''

        uinfo_table = ["User: ", "Cards: ", "Hand Value: ", "Current Bet: ", "Game Status: "]
        # TODO look into how the list of cards is being sent from server to client. This could
        # muck up how the table is parsed below. 
        message = kwargs['msg'].split(',')  # Splits our string up into a table. 

        for info, loc in enumerate(message):
            print('\n' + uinfo_table[loc] +  str(info))


    def print_bet_confirm(self, **kwargs):
        'Correctly formats a message from the server informing the user that the bet has been confirmed.'
        msg = kwargs['msg']
        if msg == "Accepted":
            print("The dealer acknowledges your bet")
        else:
            print("You have bet more monies than you currently have. Enter a new figure after /bet")


    def print_stand_confirm(self, **kwargs):
        'Correctly prints a confirmation of a stand message'
        print(kwargs['msg'])

    def print_broadcast(self,**kwargs):
        'Basically it adds \'BROADCAST\' in front of a broadcast message'
        print("BROADCAST: " + kwargs['msg'])

    def print_ace(self, **kwargs):
        'A print method handling ace confirmation messages!'
        ace = kwargs['msg']
        if ace == 'HI':
            print("Big Brother Says Your Ace is best off high!")
        elif ace == 'LO':
            print("Big Brother thinks your Ace is best off being kept low!")
        elif ace == 'MX': # Note: Ace High Value is returned in another message. May want to inform users of this
            null , null , tv = ace.split(',')
            print("The logic of the server sees advantages to your ace being either high or low. For what it's worth," +
            " should your ace be counted as low you'd have a total value of " + tv)

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
