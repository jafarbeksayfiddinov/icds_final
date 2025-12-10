# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from chat_utils import *
import json


# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""



    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width=False,
                             height=False)
        self.login.configure(width=400,
                             height=300)
        # create a Label
        self.pls = Label(self.login,
                         text="Please login to continue",
                         justify=CENTER,
                         font="Helvetica 14 bold")

        self.pls.place(relheight=0.15,
                       relx=0.2,
                       rely=0.07)
        # create a Label
        self.labelName = Label(self.login,
                               text="Name: ",
                               font="Helvetica 12")

        self.labelName.place(relheight=0.2,
                             relx=0.1,
                             rely=0.2)

        # create a entry box for
        # tyoing the message
        self.entryName = Entry(self.login,
                               font="Helvetica 14")

        self.entryName.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.2)

        # set the focus of the curser
        self.entryName.focus()

        # create a Continue Button
        # along with action
        self.go = Button(self.login,
                         text="CONTINUE",
                         font="Helvetica 14 bold",
                         command=lambda: self.goAhead(self.entryName.get()))

        self.go.place(relx=0.4,
                      rely=0.55)
        self.Window.mainloop()

    def goAhead(self, name):
        if len(name) > 0:
            msg = json.dumps({"action": "login", "name": name})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state=NORMAL)
                # self.textCons.insert(END, "hello" +"\n\n")
                self.textCons.insert(END, menu + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)
                # while True:
                #     self.proc()
            # the thread to receive messages
            process = threading.Thread(target=self.proc)
            process.daemon = True
            process.start()

    # The main layout of the chat
    def layout(self, name):

        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False,
                              height=False)
        self.Window.configure(width=470,
                              height=550,
                              bg="#17202A")
        self.labelHead = Label(self.Window,
                               bg="#17202A",
                               fg="#EAECEE",
                               text=self.name,
                               font="Helvetica 13 bold",
                               pady=5)

        self.labelHead.place(relwidth=1)
        self.line = Label(self.Window,
                          width=450,
                          bg="#ABB2B9")

        self.line.place(relwidth=1,
                        rely=0.07,
                        relheight=0.012)

        self.textCons = Text(self.Window,
                             width=20,
                             height=2,
                             bg="#17202A",
                             fg="#EAECEE",
                             font="Helvetica 14",
                             padx=5,
                             pady=5)

        self.textCons.place(relheight=0.745,
                            relwidth=1,
                            rely=0.08)
        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)

        # place the scroll bar
        # into the gui window
        scrollbar.place(relheight=1,
                        relx=0.974)

        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=DISABLED)
        # bottom label
        self.labelBottom = Label(self.Window,
                                 bg="#ABB2B9",
                                 height=40)

        self.labelBottom.place(relwidth=1,
                               rely=0.825)

        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 13")
        self.entryMsg.place(relwidth=0.60,  # reduced from 0.72
                            relheight=0.06,
                            rely=0.008,
                            relx=0.011)

        # Emoji picker button (opens popup)
        self.buttonEmoji = Button(self.labelBottom,
                                  text="😊",
                                  font="Helvetica 12",
                                  width=2,
                                  command=self.openEmojiPicker)
        # place it right after entry
        self.buttonEmoji.place(relx=0.70, rely=0.008, relheight=0.06, relwidth=0.06)

        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 13")

        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth=0.68,
                            relheight=0.06,
                            rely=0.008,
                            relx=0.011)

        # self.entryMsg.focus()

        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text="Send",
                                font="Helvetica 10 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: self.sendButton(self.entryMsg.get()))
        self.buttonMsg.place(relx=0.78,
                             rely=0.008,
                             relheight=0.06,
                             relwidth=0.22)
        # Features Buttons
        self.buttonTime = Button(self.Window,
                                 text="Time",
                                 command=self.getTime)
        self.buttonTime.place(relx=0.02, rely=0.92, relwidth=0.16)

        self.buttonWho = Button(self.Window,
                                text="Who",
                                command=self.getWho)
        self.buttonWho.place(relx=0.22, rely=0.92, relwidth=0.16)
        self.buttonSearch = Button(self.Window,
                                   text="Search",
                                   command=self.searchWindow)
        self.buttonSearch.place(relx=0.42, rely=0.92, relwidth=0.16)

        self.buttonPoem = Button(self.Window,
                                 text="Get Poem",
                                 command=self.getPoem)
        self.buttonPoem.place(relx=0.62, rely=0.92, relwidth=0.16)



        self.buttonChatbot = Button(self.Window,
                                    text="Chatbot",
                                    command=self.chatbotWindow)
        self.buttonChatbot.place(relx=0.82, rely=0.92, relwidth=0.16)

    def openEmojiPicker(self):
        """Open a small popup with emoji buttons."""
        # simple emoji list — extend as desired
        emojis = [
            "😊","😂","😍","👍","🙏","😅","😎","🤔",
            "😢","😡","🎉","💯","🔥","🤖","🙂","😴"
        ]
        picker = Toplevel(self.Window)
        picker.title("Emoji")
        picker.resizable(False, False)

        # grid of emoji buttons
        cols = 8
        for idx, em in enumerate(emojis):
            b = Button(picker, text=em, font=("Helvetica", 14),
                       command=lambda e=em: self.insertEmoji(e, picker))
            r = idx // cols
            c = idx % cols
            b.grid(row=r, column=c, ipadx=6, ipady=6, padx=2, pady=2)

        # optional: close picker if it loses focus
        picker.transient(self.Window)
        picker.grab_set()

    def insertEmoji(self, emoji_char, picker_window=None):
        """Insert emoji into entry at cursor position and close picker."""
        try:
            # Entry widget supports the INSERT index
            self.entryMsg.insert(INSERT, emoji_char)
        except Exception:
            # fallback: append at the end
            cur = self.entryMsg.get()
            self.entryMsg.delete(0, END)
            self.entryMsg.insert(END, cur + emoji_char)
        # refocus the entry so user can keep typing
        self.entryMsg.focus()
        if picker_window:
            picker_window.destroy()


    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.textCons.config(state=DISABLED)
        self.my_msg = msg
        # print(msg)
        self.entryMsg.delete(0, END)

    def getTime(self):
        self.my_msg = 'time'

    def getWho(self):
        self.my_msg = "who"

    def disconnect(self):
        self.my_msg = 'bye'

    # poem
    def getPoem(self):
        win = Toplevel()
        win.title("Poem")
        Label(win, text="Poem number (1-154):").pack()
        entry = Entry(win)
        entry.pack()
        Button(win, text="Get Poem",
               command=lambda: self.setPoem(entry.get(), win)).pack()

    def setPoem(self, num, win):
        self.my_msg = "p" + num
        win.destroy()

    # Search pop up window
    def searchWindow(self):
        win = Toplevel()
        win.title("Search")
        Label(win, text="Enter keyword:").pack()
        entry = Entry(win)
        entry.pack()
        Button(win, text="Search",
               command=lambda: self.setSearch(entry.get(), win)).pack()

    def setSearch(self, term, win):
        self.my_msg = "?" + term
        win.destroy()

    # chatbot pop up window
    def chatbotWindow(self):
        bot = Toplevel()
        bot.title("Chatbot")

        Label(bot, text="Ask the Chatbot:").pack()
        entry = Entry(bot)
        entry.pack()

        Button(bot, text="Send",
               command=lambda: self.chatbotReply(entry.get(), bot)).pack()

    def chatbotReply(self, text, bot):
        # simple rule-based chatbot
        msg = text
        self.my_msg = "@bot " + msg
        bot.destroy()

    def proc(self):
        # print(self.msg)
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = ""
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                # print(self.system_msg)
                self.system_msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                self.textCons.config(state=NORMAL)
                self.textCons.insert(END, self.system_msg + "\n\n")
                self.system_msg = ""
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)

    def run(self):
        self.login()


if __name__ == "__main__":
    import socket
    from client_state_machine import ClientSM

    # create a socket and connect to server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 1112))  # make sure IP/port match your server

    # create the state machine
    sm = ClientSM(s)

    # create and run the GUI
    gui = GUI(
        send=lambda msg: mysend(s, msg),  # use your chat_utils send
        recv=lambda: myrecv(s),  # use your chat_utils recv
        sm=sm,
        s=s
    )
    gui.run()

