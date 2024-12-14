import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
from datetime import datetime
import json, os

import json
def load_laststate(state_file = "last_sate.json", ):
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)        
            return data  # Return the loaded data

    else:
        return None

def run_state(last_proc_docNo=None):
    with open("last_sate.json", 'w', encoding = 'utf-8') as f:
        json.dump({
            "last_proc_docNo":str(last_proc_docNo), 
            "last_procTime":datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }, f)
async def main():
    print('Python Graph Tutorial\n')

    # Load settings
    config = configparser.ConfigParser()
    config.read("D:\MSIS\SEM_III\ISR\project\GraphAPI\config.cfg")
    print(config.sections())
    azure_settings = config['azure']

    graph: Graph = Graph(azure_settings)

    await greet_user(graph)

    choice = -1

    while choice != 0:
        print('Please choose one of the following options:')
        print('0. Exit')
        print('1. Display access token')
        print('2. List my inbox')
        print('3. Send mail')
        print('4. Make a Graph call')
        print('5. List the items in deleted folder')

        try:
            choice = int(input())
        except ValueError:
            choice = -1

        try:
            if choice == 0:
                print('Goodbye...')
            elif choice == 1:
                await display_access_token(graph)
            elif choice == 2:
                await list_inbox(graph)
            elif choice == 3:
                await send_mail(graph)
            elif choice == 4:
                await make_graph_call(graph)
            elif choice == 5:
                await list_deleted_items(graph)
            else:
                print('Invalid choice!\n')
        except ODataError as odata_error:
            print('Error:')
            if odata_error.error:
                print(odata_error.error.code, odata_error.error.message)

async def greet_user(graph: Graph):
    user = await graph.get_user()
    if user:
        print('Hello,', user.display_name)
        # Personal accounts, email is in userPrincipalName
        print('Email:', user.mail or user.user_principal_name, '\n')

async def display_access_token(graph: Graph):
    token = await graph.get_user_token()
    print('User token:', token, '\n')


async def list_inbox(graph: Graph):
    last_save_info = load_laststate()
    message_page = await graph.get_inbox(last_save_info)
    conversation_counts = {}
    if message_page:
        # Output each message's details
        for message in message_page.value:
            # print(message.conversation_id)
            conversation_id = message.conversation_id
            if conversation_id:
                if conversation_id in conversation_counts:
                    conversation_counts[conversation_id] += 1
                else:
                    conversation_counts[conversation_id] = 1
            # thread_count = await graph.get_thread_count(message.conversation_id)
            from_email = (message.from_.email_address.address 
                                if message.from_ and message.from_.email_address else None)
    
            cc_emails = []
            if message.cc_recipients:
                cc_emails = [r.email_address.address for r in message.cc_recipients if r.email_address]
            # toRecipients is a list of Recipient objects, if any.
            to_emails = []
            if message.to_recipients:
                to_emails = [r.email_address.address for r in message.to_recipients if r.email_address]
            with open("output_1.txt", 'a') as file:

                file.write("Thread count: \t"+str(conversation_counts[conversation_id])+'\n')
                file.write("Conversation ID: \t"+message.conversation_id+'\n' )
                file.write("from: \t"+from_email+'\n')
                file.write("to: \t"+(" ".join(to_emails) if cc_emails else '')+'\n')
                file.write("cc: \t"+(" ".join(cc_emails) if cc_emails else '')+'\n\n')

async def get_thread_count(self, conversation_id):
    if conversation_id:
        threads = await self.user_client.me.conversations[conversation_id].threads.get()
        return len(threads.get('value', []))
    return 0

async def list_deleted_items(graph):
    last_save_info = load_laststate()
    # h2t = HTML2Text()
    conversation_counts = {}
    message_page = await graph.get_deleted_items(last_save_info)
    if message_page:
        with open('deleted_items.jsonl', 'w', encoding='utf-8') as f:
            for i, message in enumerate(message_page):
                # print(message)
                conversation_id = message.conversation_id
                if conversation_id:
                    conversation_counts[conversation_id] = conversation_counts.get(conversation_id,0)+1
                # print(message.body.content)
                thread_count = conversation_counts[conversation_id]
                
                # Extract fields.
                from_email = (message.from_.email_address.address 
                                if message.from_ and message.from_.email_address else None)
    
                cc_emails = []
                if message.cc_recipients:
                    cc_emails = [r.email_address.address for r in message.cc_recipients if r.email_address]
                # toRecipients is a list of Recipient objects, if any.
                to_emails = []
                if message.to_recipients:
                    to_emails = [r.email_address.address for r in message.to_recipients if r.email_address]
    
                # extracting text from HTML.
                body_content = message.body.content if message.body else None
    
                record = {
                    "docNo":i,
                    "id": message.id,
                    "from": from_email,
                    "to": to_emails,
                    "cc": cc_emails,
                    "isRead": message.is_read,
                    "subject": message.subject,
                    "body": body_content,
                    "receivedDateTime": str(message.received_date_time) if message.received_date_time else None,
                    "thread_count": thread_count,
                }
    
                # Write the record as a JSON line
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            run_state(last_proc_docNo=i)
        
        print("Export completed.")


asyncio.run(main())