import socket
import re
import threading
import time
import sys

import tkinter as tk
from tkinter import messagebox

from lib.curry import curry


class bjNET_GUI(object):
	def __init__(self, parent):
		"""The init method initialises our basic programme variables like our threadlock, some state flags, our codex
		as well as handles (in a broad sense) connection to the server (actual connection is done by the connect
		method. In addition, it handles the creation of both our connection window as well as the main GUI for
		the programme!"""

		# First we are going to initialise some of our basic programme governing variables
		# This is our threadlock, some of our encoding and dispatch prefixes as well as some
		# game state flags.

		self.tLock = threading.Lock()
		self.shutdown = False
		self.connected = False
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
		self.connection_window = tk.Frame(self.my_parent, relief='sunken', width=175,
										  height=300)  # Creating a blank frame

		self.connection_window.grid(column=0, row=0, columnspan=3, rowspan=6)  # Drawing it to the screen

		# Now I am going to create + draw some labels
		welcome_label = tk.Label(self.connection_window, text="Welcome to bjNET! <3", )
		welcome_label.grid(column=1, row=0)  # We want this to be top and centre

		handle_label = tk.Label(self.connection_window, text='USERNAME:', anchor=tk.W)  # Left Justified
		handle_label.grid(column=0, row=2, sticky='e', pady=2)

		server_label = tk.Label(self.connection_window, text="SERVER IP:", anchor=tk.W)  # Left Justified
		server_label.grid(column=0, row=3, sticky='e', pady=2)

		# Now we define + draw our text entry boxes
		handle_input = tk.Entry(self.connection_window, width=30)
		handle_input.grid(column=1, row=2, columnspan=2, sticky='w', pady=2, padx=5, )

		server_input = tk.Entry(self.connection_window, width=30)
		server_input.grid(column=1, row=3, columnspan=2, sticky='w', pady=2, padx=5)

		# Finally we define + draw two buttons Join and Quit

		# Dat error handling
		join_button = tk.Button(self.connection_window, command=curry(self.connect, handle_input, server_input),
								text="Join", width=7)
		join_button.grid(column=1, row=5, rowspan=1, sticky='es', pady=10, padx=5)

		quit_button = tk.Button(self.connection_window, command=curry(sys.exit, 0), text="Quit", width=7)
		quit_button.grid(column=2, row=5, rowspan=1, sticky='ws', pady=10, padx=5)

	# TODO Fix issue where failed connection results in programme freeze.
	def connect(self, handle_input, server_input):
		"""Connects the user to the bjNET server or informs them that their connection couldn't work because either
		their user name was already taken or the server did not respond in 60 seconds."""

		# We pass in our widgets and take the information from them in the local name space. It seems to be a good_enough
		# way to do it!
		handle = handle_input.get()
		server = "127.0.0.1"  # TODO remove the hard coding of server ip
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((server, 0))
		self.sock.setblocking(True)
		self.server = (server, 5000)  # Sends messages out on port 5000

		timeout = 60  # Give the server 60 seconds to respond

		self.sock.sendto(str.encode('jo&' + handle), self.server)  # Attempting to connect to server

		while not self.connected:
			while timeout > 0:
				try:
					data, null = self.sock.recvfrom(1024)  # Receiving our data
					break  # break from our inner loop
				except ConnectionResetError:
					tk.messagebox.showinfo(message="The connection was closed by the server. Please try again!",
										   icon='warning', title='Connection Error', parent=self.connection_window)
					return
				finally:  # 5000% kosher
					time.sleep(0.5)
					timeout -= .5  # Increment our clock down.

				# Handling timeouts, user_name overlaps and finally being accepted to the server.
			if timeout == 0:
				# Create a popup window letting the user know that the server is not awake and to try another server
				tk.messagebox.showinfo(message="The Connection timed out. :_(",
									   detail="All that internet... and it STILL wasn't good enough",
									   icon='Warning', title='Connection Error')
				return
			elif data.decode('utf-8') == '409':  # User has chosen a name already in use.
				# Throw an error!
				tk.messagebox.showinfo(message="The handle you want to use is already taken.",
									   title='Connection Error', parent=self.connection_window)
				return
			elif data.decode('utf-8') == '300':  # User has been accepted!
				self.connected = True
				self.connection_window.grid_forget()  # Clears the window
				self.connection_window.destroy()
				self.main_pgm_loop()  # Is there a way to do this with out preserving a the connection method on the stack.

	def main_pgm_loop(self):
		"""This method handles the meat of the programme including handling incoming and outgoing connections
		as well as drawing the main gui elements for the game."""

		self.main_window = tk.Frame(self.my_parent, relief='sunken', width=1200,
										  height=1000,)
		self.main_window.grid(column=0, row=0, columnspan=10, rowspan=8)

		# TODO This canvas will have to be worked on quite a bit more.
		playing_table = tk.Canvas(self.main_window, width=600, height=700)
		playing_table.create_rectangle(0, 0, 300, 500, fill="green")
		playing_table.grid(column=0, row=0, rowspan=3, columnspan=5, sticky="nw", pady=3, padx=3)
		sep = tk.SEPARATOR(self.main_window, orient=HORIZONTAL)
		sep.grid(column=0, row=4, pady=3, padx=3)

		# Drawing the text window and associated elements
		chat_window = tk.Text(self.main_window, width=800, height=700, wrap="word", state="disabled")
		chat_scroll = tk.Scrollbar(self.main_window, orient=VERTICAL, command=chat_window.yview())
		chat_window['yscrollcommand'] = chat_scroll.set
		chat_window.grid(column=0, row=5, rowspan=4, columnspan=7, sticky="w", pady=3, padx=2)
		chat_scroll.grid(column=8, row=5, columnspan=1, rowspan=4,sticky=e, pady=3)





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
	root.wm_title("bjNET ALPHA. SWAG.")
	bj_gui = bjNET_GUI(root)
	root.mainloop()


main()
