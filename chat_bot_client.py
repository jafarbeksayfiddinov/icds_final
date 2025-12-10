from ollama import Client


class ChatBotClient():

    def __init__(self, name="3po", model="phi3:mini", host='http://localhost:11434', headers={'x-some-header': 'some-value'}):
        self.host = host
        self.name = name
        self.model = model
        self.client = Client(host=self.host, headers=headers)
        # self.client = OpenAI(api_key="EMPTY", base_url="http://10.209.93.21:8000/v1")  # use this if switching to OpenAI-compatible API
        self.messages = []
    
    def chat(self, message: str):
        # If you want context, you can add previous conversation history
        self.messages.append({"role": "user", "content": message})

        response = self.client.chat(
            self.model,
            messages=self.messages
        )
        msg = response["message"]["content"]

        # Add assistant's response to the conversation context
        self.messages.append({"role": "assistant", "content": msg})
        return msg
    
    def stream_chat(self, message):
        self.messages.append({
            'role': 'user',
            'content': message,
        })
        response = self.client.chat(self.model, self.messages, stream=True)
        answer = ""
        for chunk in response:
            piece = chunk["message"]["content"]
            print(piece, end="")
            answer += piece
        self.messages.append({"role": "assistant", "content": answer})



if __name__ == "__main__":
    c = ChatBotClient()
    print(c.chat("Your name is Tom, and you are the learning assistant of Python programming."))
    print(c.stream_chat("What's your name and role?"))