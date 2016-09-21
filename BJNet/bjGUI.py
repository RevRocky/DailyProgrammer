import socket
import re
import threading
import time
import sys


import tkinter as tk

import lib.curry as curry

class bjNET_GUI(object):

	def __init__(self, parent):

		# First we are going to initialise some of our basic programme governing variables
		# This is our threadlock, some of our encoding and dispatch prefixes as well as some
		# game state flags.

		self.tLock = threading.Lock()
		self.shutdown = False
		self.my_parent = parent

		# Now we set up our encoding and decoding "cyphers". Note to self. 'I' in the re.compile function call is to
		# ignore the case of the matching string. This is so someone could type /QUIT or /QUiT
		# Note. I sthreee the regular expressions as a potential point of conflict for the application so it must be tested
		# well.

		# Encodings go out
		self.encodings = [(re.compile('^/bet', re.I), 'be&'), (re.compile('^/quit', re.I), 'co&'),
								(re.compile('^/hit', re.I), 'ht&'),
								(re.compile('^/stand', re.I), 'sd&'), (re.compile('^/pinfo', re.I), 'pl&'),
								(re.compile('^/ginfo', re.I), 'ul&'), (re.compile('^/force', re.I), 'ng&')]

		# Dispatch is on the way in!
		self.dispatch_prefixes = {'ch': self.handle_cards, 'cb': self.handle_bet_confirm(),
											'sd': self.handle_stand_confirm(), 'nc': self.handle_cards,
											'br': self.handle_broadcast(), 'ac': self.handle_ace,
											'ui': self.handle_user_info, 'oc': self.handle_others_cards}

		# Now we are going to create a dialogue that allows for the user to input the server they'd like to connect
		# to as well as their desired username.

		# TODO Do these variables need to be class attributes?
		self.connection_window = tk.Frame(self.my_parent)  # Creating a blank frame
		self.connection_window.grid(column = 0, row = 0, columnspan = 3, rowspan = 4)  # Drawing it to the screen

		# Now I am going to create some labels
		welcome_label = tk.Label(self.connection_window, text = "Welcome to bjNET! <3",)

		handle_label = tk.Label(self.connection_window, text = 'Username:', anchor = tk.W)  # Left Justified
		server_label = tk.Label(self.connection_window, text = "SERVER IP:", anchor = tk.W)  # Left Justified

		# Now we define our text entry boxes
		handle_input = tk.Entry(self.connection_window)
		handle = handle_input.get()  # Obtaining input

		server_input = tk.Entry(self.connection_window)
		server = server_input.get()  # Obtaining that sweet sweet INFORRRRRMATION!

		# Finally we define two buttons Join and Quit
		join_button = tk.Button(self.connection_window, command=curry(self.connect, handle, server))
		quit_button = tk.Button(self.connection_window, command= curry(sys.exit, 0), text="Quit")

		# Now let's pack these widgets into a frame!

		welcome_label.grid(column=1, row=0)  # We want this to be top and centre

		handle_label.grid(column=0, row=1, sticky='w')
		handle_input.grid(column=1, row=1, sticky='w')

		server_label.grid(column=0, row=2, sticky='w')
		server_input.grid(column=1, row=2, sticky='w')

		join_button.pack(column=1, row=3)
		quit_button.pack(column=2, row=3)














	def connect(self, handle, server):
		pass

	def listen(self):
		pass

	def decoder(self):
		pass

	def encoder(self):
		pass

	def handle_chat(self):
		pass

	def handle_cards(self):
		pass

	def handle_user_info(self):
		pass


	### These next few methods could easily be combined into a handle_game method or something of the like
	### that handles all messages coming from the server meant to handle game state stuff (it will all be placed
	### in a separate chat pane.
	def handle_bet_confirm(self):
		pass

	def handle_others_cards(self):
		"""This method handles and prints to the chat window information about other's dealings in the game!"""
		pass

	def handle_stand_confirm(self):
		pass

	def handle_broadcast(self):
		pass

	def handle_ace(self):
		"""This is a special method that handles ace-logic messages!"""
		pass
	### Below will be other methods that will define further GUI based functionality!

	def wipe_table(self):
		"""Once the server signals to the client that the programme is going into an end game state, this method will
		clear the board for the next round of play!"""
		pass

	def handle_server_cards(self):
		"""This method will handle the dealing of cards from the server to the client.

		NOTE: This will require some rewriting of both the server and the CLI client!"""
		pass


# May put some of the... behind the scenes data management stuff into it's own class called highroller

def main():
	# The first thing we will do in main is establish the foundations for our GUI

	root = tk.Tk()
	bj_gui = bjNET_GUI(root)

main()