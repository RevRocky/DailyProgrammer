import requests
import random
import re
from lxml import etree


def process_input(webpage, prefix_length=2):
    '''This function scrapes a given website and returns returns the text as a plain text file.
    At present this web scraper is set up to only correctly parse Project Gutenberg.txt Books. '''

    # TODO this here web parser must work with all Gutenberg Ebooks for this to be considered.... something "workable"
    response = requests.get(webpage) # This gets the text of our webpage.
    wp = response.text
    page = etree.HTML(wp) # We just want our page to be the text.
    tst = page.findall('.//p')
    book_text = '\n'.join([el.text for el in page.findall('.//p')])


    # And now we build our markov dictionary straight from the text
    # Now we have the... relatively simple task of building our dictionary.
    # This loop uses the very last word in a chain of prefixes as our "focal point" since it is easy to capture the
    # entirety of the list-section by simply taking a range from the last_prefix back a number of cells that correspond
    # with how long we want each prefix to be. It also makes grabbing the suffix much easier as we just add one.
    # TODO Incorporate Multiplicity into this dictionary construction In a more... elegant manner
    # TODO Find a way to differentiate between prefixes that start with capitals and those that do not. To provide for
    # more realistic text generation.
    markov_dict = {}

    book_text = book_text.split()
    for last_prefix in range(prefix_length, len(book_text)):
        prefix = ' '.join(book_text[last_prefix - prefix_length : last_prefix])
        if prefix in markov_dict.keys():
            markov_dict[prefix].append(book_text[last_prefix])
        else:  # The prefix already exists.
            markov_dict[prefix] = [book_text[last_prefix]]

    return markov_dict

def monkeys_with_typewriters(text, length = 200, prefix_length = 2):
    '''This function will generate what it considers to be grammatically valid text based on the input that it has
    been given. Length is a parameter that will define how long the generated text should be.'''


    output = []
    prefix = random.choice(list(text.keys())) # Get a random key and partition it.
    suffix = random.choice(text[prefix])

    # storing the previous prefixes to variables for easy tracking
    # First we get a random starting point


    for word in prefix.split():
        output.append(word)  # Append our prefixes to our output list
    output.append(suffix)  # Append our suffix on to the list as well.
    last_word = len(output)  # Here we are going to avoid calling len() on our output 1 million billion times

    # Now we loop through doing this until the length of our output matches the desired length!
    while last_word <= length:
        prefix = ' '.join(output[(last_word - prefix_length):last_word+1]) # Get the new prefix
        suffix = random.choice(text[prefix]) # Get a new suffix based upon said prefix
        output.append(suffix) # append that suffix to our output
        last_word += 1 # Move forward one spot

    output = ' '.join(output)
    return output

def xlsxdebug(text_dict):
    '''This function is used in debugging any issues with our markov dictionary.'''
    import xlsxwriter

    workbook = xlsxwriter.Workbook('belair.xlsx')
    worksheet = workbook.add_worksheet()
    row, col = 0, 0

    for key in text_dict.keys():
        row += 1
        worksheet.write(row, col, key)
        for item in text_dict[key]:
            worksheet.write(row, col + 1, item)
            row += 1
    workbook.close()

def main():
    my_text = process_input('https://www.gutenberg.org/files/52362/52362-h/52362-h.htm', prefix_length=3)
    # xlsxdebug(my_text)
    print(monkeys_with_typewriters(my_text, prefix_length=3))

main()