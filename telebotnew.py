import os, telegram, telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import logging
import threading #possibility to use for timing out
import json
# to build a storage file...?

# DEBUGGING THINGS
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='logs.txt',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S'
                    )
mytoken = '1188903464:AAFt1oJnTo5byKZl0gtoRt757mAX--1IIdY'
bot = telebot.TeleBot(mytoken)
def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))
#to receive all content types
all_content_types = ['text','document','game','audio','animation','photo','sticker','video','video_note','contact','location','venue','dice']
'''
A bot that takes user's private messages and forwards them to the group, while storing them as a list of questions to resolve. Basically a multi-pin function, where pinned messages were sent in private chats
Need to program this bot so multiple users can use at once....
Constants needed: USER_STEP and TOPIC_NAME, all should be specific to one user. Can be bypassed with a listener
'''

USER_STEP = {}
#User step will be a dictionary of key: value pair chat_id to list [x,y,z]
#x: current step
#y: recording topic (if needexists)
#z: message instance for tracking who is replying to a bot in a group

topic_dict = {}
class stored_msg():
    def __init__(self, msg_id,chat_id):
        self.original_msg_id = msg_id
        self.original_chat_id = chat_id

class user_instance():
    def __init__(self, chat_id, current_step = 0, topic_name = ''):
        self.chat_id = chat_id
        self.current_step = current_step
        self.topic_name = topic_name

#catch exception that user is not inside
def check_user_step(message):
    try:
        
        return USER_STEP[message.chat.id][0]
    except Exception as e:
        print('Expected error', e)
        return 0

def check_reply(message):
    try:
        print(message.reply_to_message.from_user.id)
        return message.reply_to_message.from_user.id == 1188903464
        
    except Exception as e:
        print('Expected error in checking reply', e)
        return False
#check user
#what needs work:
#creating a user class so bot can be used synonymously
#timing out of /end
#check if a message is a pm or a group msg
def is_msg_dm(message):
    if message.chat.type == "private":
	# private chat message
        return True
    if message.chat.type == "group":
	# group chat message
        return False
    if message.chat.type == "supergroup":
	# supergroup chat message
        return False
    if message.chat.type == "channel":
	# channel message
        return False
#I'm importing global variables in all these functions. Not sure if advisable.
#need to store message for every dtype

#I am going to create a listener to catch all messages not beloning to USER_ID

#help message for bot
@bot.message_handler(commands=['start'], content_types = ['text'])
def help_message(msg):
    help_text = \
'''
Hello W0Rld!
I am a bot that helps you pin questions in this group. 
To begin, dm me with /ask [Your question subject/topic]
Subsequently, all of your messages will be 'recorded'
Then, use /end to end the recording!

To get a list of questions, type /questions in the group
Please note that naming the same topic will override the previous messages.
To resolve a question, type /resolve
Happy Coding!
'''
    bot.send_message(chat_id = msg.chat.id, text = help_text)
#this function records the text for the question
@bot.message_handler(commands=['ask'], content_types = ['text'], func=lambda message: message.chat.type == "private")
def newtopic(msg):
    global topic_dict
    global USER_STEP
    
    if msg.text.strip() == '/ask' :
        bot.reply_to(msg, "Try again. You didn't name a topic.")
        return
    TOPIC_NAME = msg.text.replace('/ask ','')
    topic_dict[TOPIC_NAME] = []
    USER_STEP[msg.chat.id] = [1 , TOPIC_NAME]
    bot.reply_to(msg, "Your messages are now being recorded!")
    
@bot.message_handler(content_types = all_content_types, func=lambda message: check_user_step(message)  == 1 and message.text != '/end')
def storemsg_text(msg):
    #make sure question is not the same... alternatively, allow functionality to add questions  
    newitem = stored_msg(msg.message_id, msg.chat.id)
    print(msg.message_id)
    #dump(msg)
    global topic_dict
    global USER_STEP
    TOPIC_NAME = USER_STEP[msg.chat.id][1]
    if TOPIC_NAME not in topic_dict:
        topic_dict[TOPIC_NAME] = []
    topic_dict[TOPIC_NAME].append(newitem)
    print(topic_dict)
    
@bot.message_handler(commands = ['end'], func=lambda message: check_user_step(message)  == 1 )
def end_text(msg):
    global USER_STEP
    global topic_dict
    bot.reply_to(msg, "Recording has ended. Do not delete this chat, or my memory will be wiped!")
    del USER_STEP[msg.chat.id]

#this function gets the list of questions, while sending a message indicating the question topic and corresponding number
@bot.message_handler(commands=['questions'])
def gen_keyboard(msg):
    global topic_dict
    
    global USER_STEP
    print(topic_dict)
    markup = ReplyKeyboardMarkup()
    USER_STEP[msg.chat.id] = [2, 0, msg.message_id]
    question_text = \
'''
Right away. Here are this list of questions. Tap the corresponding number to find out more: \n
'''
    for number, topic in enumerate(topic_dict.keys()):
        number += 1
        question_text += str(number) + '. ' + str(topic) + '\n'
        markup.add(InlineKeyboardButton(str(number)))            
    print(question_text)               
    bot.send_message(chat_id = msg.chat.id, text = question_text, reply_markup=markup)
    


@bot.message_handler(func=lambda message: check_user_step(message) == 2 and (check_reply(message) or message.chat.type == "private") )
def forward_message(selected_msg):
    global topic_dict
    global USER_STEP
    
    try:
        current_chat_id = selected_msg.chat.id
        index = int(selected_msg.text) - 1
        selected_topic = list(topic_dict.keys())[index]
        #get corresponding topic value from number.... not advised, should fix. But after Py3.7, dictionaries maintain orders by default
        for message in topic_dict[selected_topic]:
            bot.forward_message(chat_id = current_chat_id , from_chat_id = message.original_chat_id , message_id = message.original_msg_id)
        bot.send_message(chat_id = selected_msg.chat.id, text = '**----End of Question----**', reply_markup = ReplyKeyboardRemove())
        del USER_STEP[selected_msg.chat.id]
    except KeyError as e:
        bot.send_message(chat_id = selected_msg.chat.id, text = 'Please key in a valid number! Try again.', reply_markup = ReplyKeyboardRemove())
    except ValueError as v:
        bot.send_message(chat_id = selected_msg.chat.id, text = 'Please key in a number not text! Try again.', reply_markup = ReplyKeyboardRemove())

#Now, a function to resolve a question
@bot.message_handler(commands=['resolve'], content_types = ['text'], func=lambda message: message.chat.type == "private")
def killtopic(msg):
    global topic_dict
    global USER_STEP
    print(topic_dict)
    markup = ReplyKeyboardMarkup()
    resolve_text = \
    '''
    Right away. Which question would you like to resolve?: \n
    '''
    try:
        for number, topic in enumerate(topic_dict.keys()):
            number += 1
            resolve_text += str(number) + '. ' + str(topic) + '\n'
            markup.add(InlineKeyboardButton(str(number)))            
        print(resolve_text)               
        bot.send_message(chat_id = msg.chat.id, text = resolve_text, reply_markup=markup)
        USER_STEP[msg.chat.id] = [3]
    except KeyError as e:
        bot.send_message(chat_id = msg.chat.id, text = 'Please key in a valid number! Try again.', reply_markup = ReplyKeyboardRemove())
        print(e)
    except ValueError as v:
        bot.send_message(chat_id = msg.chat.id, text = 'Please key in a number not text! Try again.', reply_markup = ReplyKeyboardRemove())
        print(v)
@bot.message_handler(func=lambda message:  check_user_step(message) == 3)
def check_user_del_topic(msg):
    global topic_dict
    global USER_STEP
    current_chat_id = msg.chat.id
    index = int(msg.text) - 1
    selected_topic = list(topic_dict.keys())[index]
    stored_chat_id = topic_dict[selected_topic][0].original_chat_id
    if stored_chat_id != current_chat_id:
        bot.send_message(chat_id = current_chat_id, text = 'You\'re not the user who posted the question!')
    else:
        removed_value = topic_dict.pop(selected_topic, 'ERROR: No Key found') 
        bot.send_message(chat_id = current_chat_id, text = 'Question removed! Thank the user who answered you.', reply_markup = ReplyKeyboardRemove())
    del USER_STEP[msg.chat.id]
#ADMIN FUNCTIONS
@bot.message_handler(commands=['store'], content_types = ['text'], func =  lambda message: message.chat.id == 242546822)
def store_dict(msg):
    global topic_dict
    output = open('data.json','a')
    json.dump(topic_dict, output, indent = 4) 



bot.polling()