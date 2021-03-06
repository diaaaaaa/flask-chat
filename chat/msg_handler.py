'''
   This module contains helper functions for processing
   messages.
'''

import re

def html_encode(text):
    '''Encode text to avoid XSS attacks.'''
    return text.replace("<", "&lt;").replace(">", "&gt;")


def generate_html(text, user):
    '''
        Format HTML based on the message type.

        :param text: The message to be formatted.
        :type text: string
        :param user: the user that entered the message
        :type user: string
        :returns:  tuple containing text (the formatted message) and type (header, action, link, default)

        Cases:

        - header  - large centered text with no username
        - action  - bolded text similar to default
        - link    - hyperlink to a site
        - default - plain message

        .. note::

            Link is delicate and will create a lot of broken links
            if they are not full paths.  Links must start with http or
            https.  It should be fine if the link is copied directly
            from a browser such as chrome.
    '''
    type = ''

    # Format header message
    if text[0:7] == "/header":
        type = "header"
        text = '</br><center class="{user}" style="font-size:1.5em;font-weight:bold;">{message}</center>'.format(user=user, message=text[8:])

    # Format action message
    elif text[0:4] == "/act":
        type = "action"
        text = '<b>{user}</b>: <strong>{message}</strong>'.format(user=user, message=text[5:])

    # Format link message
    elif text[0:5] == "/link":
        type = "link"
        text = '<b>{user}</b>: <a target="_blank" href="{message}">{message}</a>'.format(user=user, message=text[6:])

    # Format default message
    else:
        type = "default"
        text = '<b>{user}</b>: {message}'.format(user=user, message=text)

    return text, type


def handle_message(message, stream_user):
    '''
        Parse the message and determine how to proceed.

        This will either return a value to close the
        stream, or return a message to broadcast to all
        connections.

        :param message: the message that is being processed
        :type message: dict
        :param stream_user: the user that this stream corresponds to
        :type stream_user: string

        :returns: tuple containing text (the formatted message) and mine (bool, indicates that the user sending the message corresponds to this data stream)

        If the message is associated with the current
        user, append it to the redis DB chat list.

        Each stream will process these messages.
        In order to verify that we do not create
        duplicates in the database, we must ensure that
        it is only added once.  This is done by checking
        the associated user in the 'mine' variable.
    '''
    # Ignore the message if it is a subscription
    if message['type'] == 'subscribe':
        return

    # Convert text to a string
    text = str(message['data'])

    # HTML encode to avoid XSS attacks
    text = html_encode(text)

    # Check to see if the user is leaving
    if text[0:5] == "/quit":
        if text[6:] == stream_user:
            return "quit", True

    # Extract username
    sep = text.split("}|{")
    msg_user = sep[0]
    text = sep[1]

    # Generate HTML formatting
    text, type = generate_html(text, msg_user)

    # Determine if the message belongs to the stream user
    mine = True if msg_user == stream_user else False

    # Return message and whether it matches the stream user
    return text, mine
