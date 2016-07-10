import socket
import threading
import time
import queue
import re

from random import randint
from copy import deepcopy

class CardServer(object):

    def __init__(self):

        # This block handles establishing connection info for our socket.
        self.HOST = '127.0.0.1'
        self.PORT = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.HOST, self.PORT))
        self.sock.setblocking(True)

        # Establishing a 'list' of connected clients.
        self.clients = {}  # I'm using a dict because it gives me better ability to keep track of user names.
        self.new_friends = {}  # This is a queue of players who have not yet been dealt a hand
        self.dealer = Player()

        # Now we establish our dispatch prefixes.
        self.dispatch_prefixes = {'ch': self.relay_message, 'jo': self.new_connection,
                                  'ul': self.player_info_processing,
                                  'qu': self.close_connection, 'co': self.close_connection,
                                  'ht': self.hit_me, 'sd': self.confirm_stand, 'ng': self.new_game}

        # Now we establish our game states and our stand-bust count.
        self.new_game = False
        self.quitting = False
        self.game_time = False  # Tracks the state of either being in game or not. If not in game only chat relay
        # Functionality works
        self.end_game = False
        self.stand_bust_count = 0

        # Here we establish both our thread-lock and an empty queue.
        self.print_lock = threading.Lock()
        self.task_queue = queue.Queue()

        # Finally we construct our deck.
        self.deck = []
        self.deck = self.construct_deck()

        print("The server has initialised!")

        # TODO Ensure this variable is properly updated in the presence of threading

    def listen_loop(self):
        '''This is the main loop which listens for in coming connections and when messages are received it handles
        the messages accordingly. The only problem with it currently that it is not threaded and were it to be threaded:
        new connections would have to be handled outside of this method. This is something that will be worked on
        once core functionality is built and confirmed to work'''

        while not self.quitting:
            try:
                data, addr = self.sock.recvfrom(2048)
                decode_data = data.decode('utf-8')\

                # We now add our decoded data to the queue.
                self.task_queue.put((decode_data, addr))
                threading.Thread(target = self.parser).start() # This launches a new thread.

            except:
                pass
        self.sock.close()

    def parser(self):
        '''This method parses incoming messages and takes the appropriate action.

        For a complete breakdown of the Codec visit CodecDescriptions.txt.'''
        decode_data, addr = self.task_queue.get()

        # This is where we split apart our message into its constituent parts.
        pre, null, message = decode_data.partition('&')

        # TODO Does the thread need to some how signal that it has completed it's task.
        try:
            self.dispatch_prefixes[pre](msg=message, conn=addr)
        except KeyError:  # Some other client is trying to connect to the server. This sends a message informing the
            # user to get the proper client
            self.sock.sendto(str.encode('This server only handles BJNet clients. To get a BJNet client visit: ' +
                                        'website.com'), addr)

    def new_connection(self, **kwargs):
        handle = kwargs['msg']
        connection = kwargs['conn']
        # Here we check if the username is already being used. Multiple connections by the same client is handled server
        #side
        for client in self.clients:
            if handle in client[0]:
                self.sock.sendto(str.encode("409"), connection)  # nh is prefix for new handle
                return # Now we cut out of the function

        for client in self.new_friends:
            if handle in client[0]:
                self.sock.sendto(str.encode("409"), connection)  # nh is prefix for new handle
                return  # Now we cut out of the function

        self.new_friends[connection] = (handle, Player())  # Adds the client to the list of connected clients

        self.sock.sendto(str.encode('300'), connection)
        # Now we broadcast this fact
        self.broadcast(handle + " has joined the table and will join in the game next round Say hi!")

    def close_connection(self, **kwargs):
        '''If the server is in the END GAME state this allows a user to safely close their connection.'''

        conn = kwargs['conn']
        if self.end_game:  # If it's not the end game then we do not want to have players quitting midstream.
            # TODO In a later build of this server I will allow for saving of one's purse. That's for a later time tho.
            # TODO Correctly impliment broadcasting of when someone leaves the room.
            self.sock.sendto(str.encode("The dealer nods bidding you adieu. Your connection will now be safely closed."))
            # We must check through both the new_user queue and the queue of established players.
            try:
                # HERE IS WHERE WE'D IMPLEMENT SAVEGAME CODE.
                del self.clients[conn]
            except KeyError:  # A key error lets us know that the player is in the new friends category.
                del self.new_friends[conn]
        else: # The user is allowed to quit mid-game but it is simply treated as a stand
            try:
                # TODO Implement a flagging system for an account to be flagged for removal at the start of the next game.
                self.clients[conn][1].stand = True
                self.stand_bust_count += 1
            except KeyError:
                del self.new_friends[conn]

    def relay_message(self, **kwargs):
        message = kwargs['msg']
        sender = kwargs['conn']
        print(time.ctime(time.time()) + str(sender) + ': :' + message)

        # Unfortunately one of the pitfalls of my design is that messages will have to be re-encoded and have the 'ch'
        # prefix re-attached. Unlike how this will be approached client-side we can simply append the prefix.

        message = str.encode('ch&' + message)
        for client, information in self.clients.items():
            self.sock.sendto(message, client)

        for client, information in self.new_friends.items():
            self.sock.sendto(message, client)

    def shutdown(self, **kwargs):
        '''This function will work by taking a shutdown request from a user. It will IMMEDIATELY. Close the programme.
        It can only be sent during end-game/new-game and the message will require a server shut-down password that
        is defined in the __init__ method.'''
        pass

    def player_info_processing(self, **kwargs):
        '''This is a one-stop shop method for returning information both about the users as well as the dealer.

        There are three modes.

        dealer - Returns information on the dealer
        [user] - Returns information on desired user
        self - Returns information on oneself
        All - Returns information on all users currently playing the game'''

        try:
            mode = kwargs['msg']
            # TODO When testing it is highly likely that this will be a point of contention as spaces could easily
            # muck with everything.
        except ValueError: # If the message is blank then we want info of all the users
            mode = 'all'
        recipient = kwargs['conn']

        if mode == 'dealer':
            message = self.get_player_info(self.dealer, 'dealer')
            self.sock.sendto(message, recipient)
        elif mode == 'self':
            try:
                message = self.get_player_info(self.clients[recipient])
                self.sock.sendto(message, recipient)
                self.sock.sendto(str.encode("ch&SERVER: You currently have " + str(self.clients[recipient][1].credits) \
                                            + "credits."), recipient)
            except ValueError: # The specified user is not currently in the game
                self.sock.sendto("ch%SERVER: You are not currently in the game!")
                return
        elif mode == 'all':
            for client in self.clients.items():
                message = self.get_player_info(client[1])
                self.sock.sendto(message, recipient)
                self.sock.sendto(str.encode("ch&SERVER: You currently have " + str(self.clients[recipient][1].credits) \
                                            + "credits."), recipient)
                self.sock.sendto('ch&There are currently ' + str(len(self.new_friends)) + 'people waiting to join!')
        else: # They must have wanted a specific user's information.
            for client in self.clients:
                if client[0] == mode: # In this case mode is the name of the user we are looking for
                    message = self.get_player_info(client[1])
                    self.sock.sendto(message, recipient)
            self.sock.sendto("ch&The user you were looking for could not be found.")

        # Given the nature of this message I think it is best practise we do a sign-off of sorts.
        message = "There are currently " + str(len(self.new_friends)) + ' users waiting to join the game!'
        message = str.encode(message)
        self.sock.sendto(message, recipient)

    def get_player_info(self, target, mode = 'user'):
        'To avoid a messy method above, this function handles the actual retrieval of stored player information.'

        handle, target = target[0], target[1]
        if target.stand:
            status = "stand"
        elif target.natural:
            status = "beej"
        elif target.bust:
            status = "bust"
        else:  # The player is currently in game
            status = "NONE"

            # Now we compile the message we're going to send.
        if mode == 'user':
            message = handle + ',' + \
            str(target.cards) + ',' + str(target.total_value) + ',' + \
            str(target.current_bet) + ',' + status
            return str.encode('ui&' + message)

        elif mode == 'dealer':
            message = "Dealer," + str(target.cards[1:]) + ',' + str(target.total_value) + ',' + status
            return str.encode('ui&' + message)

    def new_round(self):
        """ This method begins a new round by ensuring the player list is up to date AND dealing cards/ dealing
        with black jack."""

        self.new_game = True # Just in case we need to make use of states. If not this line will be removed.

        self.clients = {**self.clients, **self.new_friends}  # Merges our new friends with our clients
        self.new_friends = {} # New friends is now emptied out.

        # We construct a new deck if need be.
        if len(self.deck) < (2 * (len(self.clients) + 1)):  # If there's not enough cards to go around
            self.construct_deck()

        # First we must collect bets from the players.
        self.broadcast('Bet Now')
        self.collecting_bets = True

        # TODO Check to ensure that the function returns how we think it ought to.
        threading.Thread(target=self.countdown, args=('new', 90)).start()
        while self.collecting_bets:
            pass # Like with our end game function we assume the computer is still listening

        # Players who have not bet are now pruned from the list of active players. This is our time out.
        # Would this be better suited as it's own method or not?
        for player in self.clients:
            if player[1].current_bet == 0:  # If they have not made a bet...
                self.new_friends[player] = deepcopy(self.clients[player])
                del self.clients[player] # Removes them from the list of active clients.
                self.sock.sendto('ch& You have waited too long to make a bet, as such you will sit out this game.' +
                                 'You will automatically be entered into the next round however.', player)
            else: # the player has made a bet thus we deal them cards.
                for card in range(2):
                    self.deal_card(conn=player)
                if player[1].total_value == 21:
                    self.confirm_stand('bj')

        # Now we deal cards to the dealer.
        for card in range(2):
            new_card = self.deck.pop()

            if new_card == 1 and not self.dealer.aces: # If we have an ace
                self.dealer.cards.append(11)
                self.dealer.total_value += 11
                self.dealer.aces = True
            else:
                self.dealer.cards.append(new_card)
                self.dealer.total_value += new_card

        # Now we track if the dealer stands or has a blackjack. If the dealer has black jack we still deal cards to the
        # players but only those with black jack can earn a pay out so we skip the main body of the game rather quickly.

        if self.dealer.total_value == 21: # Dealer has blackjack.
            self.dealer.natural = True
        elif 17 <= self.dealer.total_value < 21: # Dealer stands!
            self.dealer.stand = True

        # Broadcasts the dealer's face up card to the table.
        self.broadcast('The dealer\'s face up card is a ' + str(self.dealer.cards[1]))

        self.new_game = False
        self.game_time = True
        return # This should just pop us back to the main loop...

    def end_round(self):
        """This method clears the table, pays out bets and begins a timer where players can opt out of playing the
        new game. All players who are in the clients list but haven't opted out are assumed to be connected and the game
        will begin."""

        # First the dealer's hand is dealt with.
        self.game_time = False  # Changing our state! This should ensure only chat gets through to the server!
        self.end_game = True

        self.deal_server()  # Deals out the server's hand
        self.pay_winnings_clear_table()  # This method handles the winnings as well as clears the table

        # Time left tracks whether or not there is time left in the countdown. It starts at true. The countdown function
        # returns a False. Once this is done we can exit the while loop below and feel confident in starting a new game.

        self.broadcast("If you'd like to disconnect from the server, you can now do so safely. Type /quit into your " +
                       "console")
        threading.Thread(target=self.countdown, args='end').start()

        # Note we should still be in the listening loop so this bit may all be redundant. We will keep the structure
        # incase testing reveals that we are not still in the listening loop.
        # TODO ensure this works.
        while self.end_game:
            pass

        self.new_round()

    def process_bet(self, **kwargs):
        '''This method handles the processing of player's bets. When they get the message. It can only be activated
        should the game be at the "new_game" state.'''

        if self.collecting_bets:
            bet = kwargs['msg']
            conn = kwargs['conn']
            player = self.clients[conn][1]

            # Now we update the player's totals to reflect their bet
            player.credits, player.current_bet = (player.credits - bet), bet
            self.sock.sendto(('cb&' + str(bet)), conn) # Sends the player a message letting them know their bet was
            # confirmed.

        else:  # It's not a new game so we don't want to process any bets.
            self.sock.sendto('ch&SERVER: You can\'t bet right now')

    def countdown(self, mode, seconds_left = 60):
        'This method counts down for us in various situations'
        mode_dict = {'new': self.collecting_bets, 'end': self.end_game} # Is this the best place for this?
        while seconds_left > 0:
            if seconds_left in [5, 15, 30, 45]:
                self.broadcast(seconds_left)  # Lets players know that there is only a certain amount of time left
                # To opt out of the game.
            print("Next Phase in" + str(seconds_left))
            time.sleep(1)
            seconds_left -= 1 # We increment down.
        mode_dict[mode] = False

    def pay_winnings_clear_table(self):

        # We make the rounds of the table paying out winnings to each player.
        # We make use of the for loop to clear the table.

        for client in self.clients:

            if client[1].stand and self.dealer.bust: # If the dealer goes bust, all players not bust win their bet\
                self.sock.sendto(str.encode("ch&SERVER: The dealer has gone bust. Since you also did not go bust, "
                                            "you have won " + str( 1.25 * client[1].current_bet) +
                                            " credits. You now have"
                                            + " a total of" + str((client[1].credits + int(1.25 * client[1].current_bet)))
                                            + " credits!"), client)
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1.25 * client[1].current_bet))

            elif client[1].stand and (client[1].total_value > self.dealer.total_value): # Player wins!
                self.sock.sendto(str.encode("ch&SERVER: Your hand is greater than the dealer. As a result you have won "
                                            + str(1.25 * client[1].current_bet) +
                                            " credits. You now have a total of" +
                                            str((client[1].credits + int(1.25 * client[1].current_bet)))
                                            + " credits!"), client)
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1.25 * client[1].current_bet))

            elif client[1].natural and not self.dealer.natural: # Player has black jack
                self.sock.sendto(str.encode("ch&SERVER: Blackjack! You've hit the jackpot and as a result you will "
                                            + "receive double what you bet on the round"
                                            + str(2 * client[1].current_bet) +
                                            " credits. You now have a total of" +
                                            str((client[1].credits + int(2 * client[1].current_bet)))
                                            + " credits!"), client)
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(2 * client[1].current_bet))



            elif client[1].natural and self.dealer.natural: # Both player and dealer have black jack
                self.sock.sendto(str.encode("ch&SERVER: Blackjack! You've hit the jackpot but in some twist of fate "
                                            + "the dealer has as well. As a result you will receive your original bet of "
                                            + str(client[1].current_bet) + " credits back. You now have a total of"
                                            + str((client[1].credits + int(1 * client[1].current_bet)))
                                            + " credits."), client)
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1 * client[1].current_bet))


            else: # The player has lost in some fashion. either the dealer had a higher hand OR the player went bust.
                self.sock.sendto(str.encode("ch&SERVER: You have lost, as a result your wager is forefeit. You now have "
                                            + str(client[1].credits + " credits."), client))
                client[1].current_bet = 0
                # The message is relayed to the player

            client[1].cards = [] # Cards are returned to the dealer.
            client[1].total_value = 0 # The total value is now zero.
            client[1].bust, client[1].stand, client[1].natural, client[1].aces = False, False, False, False
            # Values are reset.

        # Now we do the same table clear for the dealer.
        self.dealer.cards = []
        self.dealer.total_value = 0
        self.dealer.bust, self.dealer.stand, self.dealer.natural, self.dealer.aces = False, False, False, False


    def broadcast(self, message):
        '''This method broadcasts a server announcement to all players currently in the game. Relay message would be used
        but it is built in a fashion that is a bit too particular to chat messages.'''

        # This code is simple, we just send out the message to everyone in the room!
        for client in self.clients:
            self.sock.sendto('b4&' + message, client)
        for client in self.new_friends:
            self.sock.sendto('b4&' + message, client)


    ##### Separating Server-esque functions from dealer functions for readability ######

    def construct_deck(self):
        '''This method handles the construction of a new deck of cards.
        Decks are generated pseudo-randomly and currently there is no means by which someone can count cards.
        In a future build of the programme, one area that will be targeted for improvement is to '''
        for card in range(300):  # Our deck will have 300 cards!
            temp = randint(1, 10)
            self.deck.append(temp)
        return self.deck

    def hit_me(self, **kwargs):
        'This method acts as a gate-keeper for the deal card function'
        player = self.clients[kwargs['conn']][1]
        if self.game_time and not (player.stand or player.bust): # If we are in game time we can give the player a card.
            self.deal_card(msg=kwargs['msg'], conn=kwargs['conn'])
        else:
            self.sock.sendto("ch&SERVER: I'm afraid I can't let you do that", kwargs['conn'])

    def deal_card(self, **kwargs):
        '''This method draws a card and deals it to the recipient'''
        conn = kwargs['conn']
        player = self.clients[conn][1] # For quicker reference to the actual player object.

        if len(self.deck) < 2:
            self.construct_deck()

        new_card = self.deck.pop(0)

        if len(player.cards) < 2 and new_card == 1:  # This makes it much quicker/easier
            # to handle a blackjack in a new game.
            player.aces = True
            player.cards.append(11) # Add it to their hand
            player.total_value += 11 # Update their total value.
            self.sock.sendto(('nc&' + 'Ace' + '_' + str(player.total_value)), conn)

        elif len(player.cards) >= 2 and new_card == 1: # The player has drawn an ace on any other turn
            player.aces = True
            player.cards.append(1)
            player.total_value += 1
            self.aces_logic(self.clients[conn])
            # TODO ensure that messages are sent in a clear fashion by our aces logic

        else:  # The player hasn't drawn an ace so we don't need to do anything fancy.
            player.cards.append(new_card)
            player.total_value += new_card
            # Now we run aces logic.
            if player.aces:
                player.aces_logic()
                # Will have to send an ace flip message.
            self.sock.sendto(('nc&'+ str(new_card) + '_' + str(player.total_value))) # Informing the players of their
            # new card.
        if player.total_value == 21 and len(player.cards) == 2:  # The player has blackjack
            self.confirm_stand('bj', conn = conn)
        elif player.total_value == 21:
            self.confirm_stand('21', conn = conn)
        elif player.total_value > 21:  # The player has gone bust. Only time we have to explicitly handle everything.
            self.stand_bust_count += 1
            player.bust = True
            self.sock.sendto('sd&With a total over 21, you have gone bust and as such you will forefeit your bet and'
                             + ' sit out until the next round.')
            if self.stand_bust_count == len(self.clients):  # If everyone's exited we want to end the round,
                self.end_round()

    def aces_logic(self, client, mode = 'client'):
        '''This method handles whether or not an ace should be considered high or low by the game engine. In addition
        to this it sends messages to the player informing them of whether or not the ace has been considered high or low.

        Mode Explanations

        client - We are running this logic on the client. As a result the client parameter will be a socket object.
        dealer - We are running this logic for the dealer. Thus the client parameter will be a player object!'''

        if mode == 'client':
            player = self.clients[client][1]
        elif mode == 'dealer':
            player = client

        # We loop through the cards looking for the first ace. If it's ace high we set it to ace low. This is for
        # simplicity in our code.
        for card in player.cards():
            if card == 1:
                break  # We only need one ace to flip.
            elif card == 11:
                card = 1
                player.total_value -= 10
                break

        if player.total_value + 10 in range(17, 22):  # Check if ace high is in our optimal range
            player.total_value += 10
            card = 11
            if mode == client:
                self.sock.sendto('ac&HI', client) # Informs the client that their ace is high. In all circumstances this would
                # be followed with a message informing them that their new card and a total.
            else:
                self.broadcast('The dealer has chosen to keep his ace high')

        elif player.total_value + 10 <= 16:  # Ace high and low give values within our range. Challenge here is how to
            # handle in the calling environment.
            player.total_value += 10
            card = 11
            if mode == client:
                self.sock.sendto('ac&MX,'+ str(player.total_value - 10)) # We send the low value as well.
            else:
                self.broadcast('The dealer has chosen to keep his ace high but, should his ace not be high his hand ' +
                               'would have value of ' +str(player.total_value - 10))


        else:
            # we have accounted for all of the situations with ace high. If none of these worked out then we know we
            # want our ace to be low.
            if mode == client:
                self.sock.sendto('ac&LO')
            else:
                self.broadcast('The dealer has chosen to keep his ace low.')

    def store_bet(self, **kwargs):
        '''Accepts the bet from the player and stores the information serverside.'''
        conn = kwargs['conn']
        bet = kwargs['message']
        player = self.clients[conn][1] # Cleans u[ the code.

        if self.game_time or self.end_game: # Perhaps a redundant check to ensure we are in the right state
            self.sock.sendto(str.encode("cb&Declined"), conn)
            return
        if bet <= player.credits: # Checks to make sure the bet is not over the amount of money they have
            player.credits, player.current_bet = (player.credits - bet), bet
            self.sock.sendto(str.encode("cb%Accepted"), conn)
        else:
            self.sock.sendto(str.encode("cb&Declined"), conn)

    def confirm_stand(self, flag = None, **kwargs):
        '''Confirm that the player has chosen to stand and lck in their current value.'''
        conn = kwargs['conn']
        player = self.clients[conn][1]

        self.stand_bust_count += 1 # Incrementing our stand and bust tracker by one.
        if flag == '21':
            self.sock.sendto(str.encode('sd&You have a total of 21, as a result you decide to stand. Winnings will be '
                                        + 'paid once a new round starts'))
            player.stand = True

        elif flag == 'bj':
            self.sock.sendto(str.encode('sd&Joy fills the air. Everything in the casino seems a bit brighter as you realise' +
                                        'that you have hit the big jackpot. BLACKJACK.' +
                                        'The moment passes and you soon realise that... there is no casino. This is an' +
                                        'online game... and the money isn\'t real. Still feels good though doesn\'t it?')
                             , conn)
            player.natural = True

            # Why not broadcast blackjacks!
            self.broadcast(self.clients[conn][0] + 'is a lucky one indeed! They have blackjack!')

        else: # The player has chosen to stand
            self.sock.sendto(str.encode('sd&The dealer nods, acknowledging your request to stand. Winnings will be payed'
                           + ' out once the round is finished'), conn)
            player.stand = True
        if self.stand_bust_count == len(self.clients):
            self.end_round()

            # TODO Check to make sure we enter the end game state at the appropriate time.

    def deal_server(self):
        '''Once every player has ether chosen to stand or has gone bust, the dealer then deals cards to himself. This
        handles the game logic on the servers end of things. Game logic forv the server works roughly as follows:
        The server will check the total value of it's cards. Dealer stands on soft seventeen. Dealer will stand if
        the total value of their cards is <= 17. Before each turn; the value of the hands will be evaluated with aces
        both high and low. '''
        # Note for future reference. Handling of a dealer black jack is done in the new game method.
        # A soft seventeen is also handled during the beginning of the new game. To simplify code flow we will still go
        # into this function but exit out rather quickly.

        dealer = self.dealer # This just simplifies some of the expressions below

        self.broadcast("The dealer flips over the card in the hole to reveal a " + str(dealer.cards[0]) + '! This gives'
                        + ' them a hand totaling ' + str(dealer.total_value)+ '.')

        if dealer.natural:
            self.broadcast('The dealer smirks briefly as they look at their hand. The smirk disappears as they begin to'
                           + ' look around the table to see if anyone is even going to get the "push"')
            return
        elif dealer.stand:
            self.broadcast('Since the dealer has a total value above 17, the rules dictate that they must stand. '
                          + 'It\'s now time to pay out any winnings!')

        if dealer.aces:
            self.aces_logic(dealer, mode = 'dealer')

        while dealer.total_value < 17:
            if len(self.deck) <= 2:
                self.construct_deck()
            new_card = self.deck.pop(0)
            if new_card == 1: # If an ace is drawn we now know that the player has an ACE!
                dealer.aces = True # In some cases this will be redundant but better be safe than sorry.
                dealer.cards.append(new_card) # Adds the card to the hand.
                dealer.total_value += 1
                self.broadcast("The dealer has drawn an Ace.") # Informs players of what just happened.
            else: # The dealer not drawn an ace.
                dealer.cards.append(new_card)
                dealer.total_value += new_card
                self.broadcast("The dealer has drawn a " + str(new_card))

            # Now we do ace_logic and broadcast the result to the players.
            if dealer.aces:
               self.aces_logic(dealer, mode = 'dealer')
            else: # The dealer does not have an ace.
                self.broadcast("This brings the total value of the dealers hand to: " + str(dealer.total_value))

        # Now we broadcast a message that the dealer has either chosen to stand or has gone bust.

        if dealer.total_value <= 21:
            dealer.stand = True # The dealer stands.
            self.broadcast("Since the dealer has a total above seventeen, the dealer has elected to stand. He stands at"
                            + str(dealer.total_value))
        else: # The dealer has gone bust.
            dealer.bust = True
            self.broadcast("LUCKY! The dealer has drawn over 21 and has gone bust. All those with totals under 21 will"
                            + " receive payouts.")


class Player(object):
    '''This is a class to handle gamestate/player management from the server server side.'''

    def __init__ (self):
        '''Currently all players will start with the same "slate".'''
        self.cards = [] # The card in position 0 is the face down card.
        self.credits = 100
        self.current_bet = 0 # This is a sort of holding pool for the players current bet. The money is taken out of
        # credits.
        self.bust = False # This will change to true if the player has value over 21
        self.stand = False
        self.natural = False # Boolean tracks whether or not someone has a black jack. Considered in the same way that
        self.aces = False # This is a boolean flag that tracks whether or not there is an ace in the player's hand.
        # stand and bust are used by the programme.
        self.total_value = 0 # This is the total value of the players cards

def main():
    dealer = CardServer()
    dealer.listen_loop()

main()