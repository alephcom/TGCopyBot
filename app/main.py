from dotenv import load_dotenv, find_dotenv
from os import getenv
from sys import exit
from telegram.client import Telegram
import argparse

load_dotenv(find_dotenv())

######################
# App Configurations #
######################

src_chat = getenv("SOURCE") or None
dst_chat = getenv("DESTINATION") or None

###########################
# Telegram Configurations #
###########################

tg = Telegram(
    api_id=getenv("API_ID"),
    api_hash=getenv("API_HASH"),

    phone=getenv("PHONE"),

    database_encryption_key=getenv("DB_PASSWORD"),
    files_directory=getenv("FILES_DIRECTORY"),

    proxy_server=getenv("PROXY_SERVER"),
    proxy_port=getenv("PROXY_PORT"),
    proxy_type={
          # 'proxyTypeSocks5', 'proxyTypeMtproto', 'proxyTypeHttp'
          '@type': getenv("PROXY_TYPE"),
    },
)

parser = argparse.ArgumentParser()
parser.add_argument("--messages", type=int, default=0, help="Number of messages to retrieve from history")
args = parser.parse_args()
# Adding optional argument

###############
# App methods #
###############

def copy_message(from_chat_id: int, message_id: int, send_copy: bool = True) -> None:
    data = {
        'chat_id': dst_chat,
        'from_chat_id': from_chat_id,
        'message_ids': [message_id],
        'send_copy': send_copy,
    }
    result = tg.call_method(method_name='forwardMessages', params=data, block=True)
    # print(result.update)


def new_message_handler(update):
    # To print every update:
    # print(update)

    # We want to process only new messages
    if 'sending_state' in update['message']:
        return

    message_chat_id = update['message']['chat_id']
    message_id = update['message']['id']

    # We want to process only messages from specific channel
    if message_chat_id != src_chat:
        return

    # Check if message is forwarded
    if 'forward_info' in update['message']:
        copy_message(message_chat_id, message_id, False)
    else:
        copy_message(message_chat_id, message_id)


def process_source_chat(tg,chat_id,history_limit):
    message_list = []

    limit = 1
    from_message_id = 0
    offset = 0
    only_local = False

    c = 0;

    print("\nRetrieving Chat History from: " + str(chat_id))

    while c < history_limit:
        r = tg.get_chat_history(
            chat_id=chat_id,
            limit=limit,
            from_message_id=from_message_id,
            offset=offset,
            only_local=only_local,
        )

        r.wait()
        print("\nPrinting Chat History")
        print("Total: " + str(r.update['total_count']))
#        print(r.update)
        messages = r.update['messages']
        for m in messages:
            print('Message ID: ' + str(from_message_id))
            print(m['content']['@type'])
            from_message_id = m['id']
            if m['content']['@type'] == 'messageText':
                print(m['content']['text']['text'])
                message_list.append(m)
#                copy_message(m['chat_id'], m['id'])
            if m['content']['@type'] == 'messageAudio':
                message_list.append(m)
#                copy_message(m['chat_id'], m['id'])

                #stats_data[message['id']] = message['content']['text']['text']
            #from_message_id = message['id']
#            c = c+1;
        c = c+1;

    print('\nDone retrieving history')
    message_list.reverse()
    for m in message_list:
        copy_message(m['chat_id'], m['id'])

if __name__ == "__main__":

    tg.login()
    result = tg.get_chats()

    result = tg.get_chats(9223372036854775807)  # const 2^62-1: from the first
    result.wait()
    chats = result.update['chat_ids']
    for chat_id in chats:
        r = tg.get_chat(chat_id)
        r.wait()
        title = r.update['title']
        print(f"{chat_id}, {title}")

    if (src_chat is None or dst_chat is None):
        print("\nPlease enter SOURCE and DESTINATION in .env file")
        exit(1)
    else:
        src_chat = int(src_chat)
        dst_chat = int(dst_chat)
 
    tg.add_message_handler(new_message_handler)

    if (int(args.messages) > 0):
        print (args.messages)
        process_source_chat(
            tg=tg,
            chat_id=src_chat,
            history_limit=int(args.messages)
        )

    tg.idle()

