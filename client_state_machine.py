"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if my_msg.startswith("/bot "):
            parts= my_msg[5:].split(' ',1)
            command = parts[0] if len(parts)>0 else ""
            args= parts[1] if len(parts)>1 else ""

            mysend(self.s, json.dumps({
                "action": "bot_command",
                "command": command,
                "args": args
            }))
            return ""

        # allow talking to the bot directly even when not connected to a peer
        if my_msg.strip().startswith("@"):
            mysend(self.s, json.dumps({
                "action": "message",
                "message": my_msg
            }))
            # show locally
            self.out_msg += "[" + self.me + "] " + my_msg + "\n"
            # Do not change state; allow normal flow to continue
            return self.out_msg

        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg.get("action") == "connect":
                    status = peer_msg.get("status")
                    if status == "request":
                        # Incoming invitation to chat
                        self.peer = peer_msg.get("from", "")
                        self.out_msg += 'Request from ' + self.peer + '\n'
                        self.out_msg += 'You are connected with ' + self.peer
                        self.out_msg += '. Chat away!\n\n'
                        self.out_msg += '------------------------------------\n'
                        self.state = S_CHATTING
                    elif status == "success":
                        # Ignore here; the synchronous connect_to() already handled it
                        pass
                    else:
                        # Unknown connect message; ignore safely
                        pass
                elif peer_msg.get("action") in ("message", "bot"):
                    sender = peer_msg.get("from", "[System]")
                    self.out_msg += sender + ": " + peer_msg.get("message", "") + "\n"

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                # echo my own message locally so I can see it immediately
                self.out_msg += "[" + self.me + "]" + my_msg + "\n"
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                action = peer_msg.get("action")
                if action == "connect":
                    self.out_msg += "(" + peer_msg.get("from", "?") + " joined)\n"
                elif action == "disconnect":
                    self.state = S_LOGGEDIN
                elif action in ("exchange",):
                    self.out_msg += peer_msg.get("from", "") + " " + peer_msg.get("message", "") + "\n"
                elif action in ("message", "bot"):
                    sender = peer_msg.get("from", "[System]")
                    self.out_msg += sender + ": " + peer_msg.get("message", "") + "\n"
                else:
                    # Fallback: show raw content if structured fields are missing
                    text = peer_msg.get("message") or str(peer_msg)
                    self.out_msg += "[System]: " + text + "\n"


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
