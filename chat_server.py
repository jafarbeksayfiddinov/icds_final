"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
from chatbot_manager import ChatBotManager

class Server:
    def __init__(self):
        self.new_clients = [] #list of new sockets of which the user id is not known
        self.logged_name2sock = {} #dictionary mapping username to socket
        self.logged_sock2name = {} # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        #initialize past chat indices
        self.indices={}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        self.chatbot=ChatBotManager(bot_name="AI Assistant",model="phi3:mini")
    def new_client(self, sock):
        #add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        #read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    
                    if self.group.is_member(name) != True:
                        #move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        #add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        #load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name]=pkl.load(open(name+'.idx','rb'))
                            except IOError: #chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    else: #a client under this name has already logged in
                        mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print ('wrong code received')
            else: #client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        #remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx','wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

#==============================================================================
# main command switchboard
#==============================================================================
    def handle_msg(self, from_sock):
        #read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
#==============================================================================
# handle connect request
#==============================================================================
            msg = json.loads(msg)
            # define from_name early for later use
            from_name = self.logged_sock2name.get(from_sock, "")
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action":"connect", "status":"self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    # send success response to initiator FIRST (this is what client waits for)
                    msg = json.dumps({"action":"connect", "status":"success"})
                    mysend(from_sock, msg)
                    # then notify peers asynchronously
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps({
                            "action":"connect", "status":"request", "from":from_name
                        }))
                    # skip sending a request back to initiator to avoid confusing the blocking response read
                    return
                else:
                    msg = json.dumps({"action":"connect", "status":"no-user"})
                mysend(from_sock, msg)
#==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
#==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                #said = msg["from"]+msg["message"]
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, json.dumps({"action":"exchange", "from":msg["from"], "message":msg["message"]}))
                # Record human-to-human chat into bot context for this conversation
                try:
                    if isinstance(the_guys, list) and len(the_guys) > 1:
                        participants = sorted(the_guys)  # includes from_name and peers
                        conv_id = "dm:" + "+".join(participants)
                    else:
                        conv_id = f"user:{from_name}"
                    bot = self.chatbot.get_bot_for_conversation(conv_id)
                    bot.messages.append({
                        "role": "user",
                        "content": f"{from_name}: {msg['message']}"
                    })
                except Exception as e:
                    print(f"Bot context append error: {e}")
#==============================================================================
#                 listing available peers
#==============================================================================
            elif msg["action"] == "list":
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                mysend(from_sock, json.dumps({"action":"list", "results":msg}))
#==============================================================================
#             retrieve a sonnet
#==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps({"action":"poem", "results":poem}))
#==============================================================================
#                 time
#==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps({"action":"time", "results":ctime}))
#==============================================================================
#                 search
#==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join([x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps({"action":"search", "results":search_rslt}))
#==============================================================================
# the "from" guy has had enough (talking to "to")!
#==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"disconnect"}))
#==============================================================================
#                 the "from" guy really, really has had enough
#==============================================================================
            elif msg["action"]=="bot_command":
                return self.handle_bot_command(from_sock, msg)
        else:
            #client died unexpectedly
            self.logout(from_sock)
        # Chatbot mention handling (kept safe and within parsed msg scope)
        if isinstance(msg, dict):
            try:
                text = msg.get("message", "")
                if text:
                    tl = text.lower()
                    bot_lower = self.chatbot.bot_name.lower()
                    mention_tags = {f"@{bot_lower}", "@ai", "@aiassistant", "@ai-assistant","@bot"}
                    mentioned = any(tag in tl for tag in mention_tags)
                    if mentioned:
                        # Build a shared conversation id based on current chat participants
                        try:
                            the_guys = self.group.list_me(from_name)
                            if isinstance(the_guys, list) and len(the_guys) > 1:
                                for g in the_guys:
                                    if g != from_name:  # Don't send back to sender
                                        to_sock = self.logged_name2sock.get(g)
                                        if to_sock:
                                            mysend(to_sock, json.dumps({
                                                "action": "message",
                                                "from": from_name,
                                                "message": text
                                            }))

                        except:
                            pass
                        try:
                            the_guys = self.group.list_me(from_name)
                            if isinstance(the_guys, list) and len(the_guys) > 1:
                                participants = sorted(the_guys)
                                conv_id = "dm:" + "+".join(participants)
                            else:
                                conv_id = f"user:{from_name}"
                        except:
                            conv_id = f"user:{from_name}"
                        response = self.chatbot.get_response(
                            message=text,
                            conversation_id=conv_id,
                            username=from_name,
                            is_group=False,
                            mentioned=True
                        )
                        if response:
                            payload = json.dumps({
                                "action": "message",
                                "from": self.chatbot.bot_name,
                                "message": response
                            })
                            # If user is in a chat, broadcast bot reply to peers too
                            try:
                                the_guys = self.group.list_me(from_name)
                            except Exception:
                                the_guys = [from_name]
                            sent_to_any = False
                            if isinstance(the_guys, list) and len(the_guys) > 1:
                                # send to self and peers
                                mysend(from_sock, payload)
                                sent_to_any = True
                                for g in the_guys[1:]:
                                    to_sock = self.logged_name2sock.get(g)
                                    if to_sock:
                                        mysend(to_sock, payload)
                            if not sent_to_any:
                                # fallback to self only
                                mysend(from_sock, payload)
            except Exception as e:
                print(f"Bot handling error: {e}")
#==============================================================================
# main loop, loops *forever*
#==============================================================================
    def run(self):
        print ('starting server...')
        while(1):
           read,write,error=select.select(self.all_sockets,[],[])
           print('checking logged clients..')
           for logc in list(self.logged_name2sock.values()):
               if logc in read:
                   self.handle_msg(logc)
           print('checking new clients..')
           for newc in self.new_clients[:]:
               if newc in read:
                   self.login(newc)
           print('checking for new connections..')
           if self.server in read :
               #new client request
               sock, address=self.server.accept()
               self.new_client(sock)

    def send_to_group(self, group_id:str, message:dict)->None:
        if not hasattr(self, "group"):
            print("Error: Group chat not initialized")
            return
        try:
            group_id=int(group_id) if isinstance(group_id, str) and group_id.isdigit() else group_id
            members=self.group.chat_grps.get(group_id, [])

            if not members:
                print(f"Error: Group {group_id} not found or empty")
                return
            message_json=json.dumps(message)
            for member in members:
                if member in self.logged_name2sock:
                    try:
                        mysend(self.logged_name2sock[member], message_json)
                    except Exception as e:
                        print(f"Error sending to {member}: {str(e)}")
                        self.logout(self.logged_name2sock[member])
        except (ValueError, AttributeError) as e:
            print(f"Error processing group message: {str(e)}")

    def handle_bot_command(self, from_sock, msg):
        command=msg.get("command","").lower()
        from_name=self.logged_sock2name[from_sock]
        if command=="reset":
            solo_conv = f"user:{from_name}"
            try:
                the_guys = self.group.list_me(from_name)
                if isinstance(the_guys, list) and len(the_guys) > 1:
                    participants = sorted(the_guys)  # e.g., ['A','B']
                    dm_conv = "dm:" + "+".join(participants)  # e.g., dm:A+B
                else:
                    dm_conv = None
            except Exception:
                dm_conv = None

            self.chatbot.reset_conversation(solo_conv)
            if dm_conv:
                self.chatbot.reset_conversation(dm_conv)

            response = "Bot conversation memory has been reset."
        elif command in ("persona", "personality"):
            conv_id = f"user:{from_name}"
            persona_text = msg.get("args", "").strip()
            if not persona_text:
                response = (
                    "Usage: /bot persona <style/role>. e.g.\n"
                    " /bot persona You are a friendly Chinese tutor. Use HSK1 words and pinyin."
                )
            else:
                # Ensure a bot exists, then append a system message without resetting context
                bot = self.chatbot.get_bot_for_conversation(conv_id)
                bot.messages.append({
                    "role": "system",
                    "content": persona_text
                })
                response = "Personality updated for this conversation."
        else:
            response= (
                "Available commands:\n"
                "/bot persona <text> - Set my personality without resetting context\n"
                "/bot reset - Reset our conversation\n"
                "In chats, mention me with @AI to talk!"
            )
        mysend(from_sock, json.dumps({
            "action":"bot", "message":response
        }))

def main():
    server=Server()
    server.run()

main()
