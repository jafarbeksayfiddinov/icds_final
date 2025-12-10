from chat_bot_client import ChatBotClient
from typing import Dict, Optional

class ChatBotManager:
    def __init__(self, bot_name: str="AI Assistant",model: str="phi3:mini"):
        self.bot_name = bot_name
        self.model = model
        self.conversations:Dict[str,ChatBotClient]={}
    def get_bot_for_conversation(self,conversation_id:str)-> ChatBotClient:
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ChatBotClient(
                name=self.bot_name,
                model=self.model)
        return self.conversations[conversation_id]

    def get_response(self,message:str,conversation_id:str,username: str="User", is_group: bool=False, mentioned: bool=False)-> Optional[str]:
        if is_group and not mentioned:
            return None
        try:
            bot= self.get_bot_for_conversation(conversation_id)
            formatted_message=f"{username}: {message}" if is_group else message
            response = bot.chat(formatted_message)
            return response
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I'm sorry, I encountered an error."
    def reset_conversation(self,conversation_id:str)->None:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]