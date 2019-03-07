from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import get_user_model
from .models import Message
import json

User = get_user_model()


class ChatConsumer(WebsocketConsumer):

    # get all last messages from server
    # and send to user
    def fetch_messages(self,data):
        # last messages
        messages = Message.last_messages()
        content = {
            'command': 'messages',
            'messages': self.messages_to_json(messages)
        }
        self.send_message(content)

    # create and send message to chat
    def new_message(self, data):
        author = data['from']
        message = Message(author,data['message'])
        content = {
            'command': 'new_message',
            'messages': self.message_to_json(message)
        }
        return self.send_chat_message(content)

    # convert last messages to json format
    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    # convert message for sending to json format
    @staticmethod
    def message_to_json(message):
        return {
            'author': message.author,
            'content': message.content,
            'time': str(message.time)
        }

    # connect to chat
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'main_%s' % self.room_name

        # join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }

    # receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self,data)

    def send_chat_message(self, message):
        # send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    # receive message from room group
    def chat_message(self, event):
        message = event['message']

        # send message to WebSocket
        self.send_message(message)
