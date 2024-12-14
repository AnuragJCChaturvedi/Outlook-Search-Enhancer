from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from datetime import datetime

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')

        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id)
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)


    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token
 
    async def get_user(self):
        # Only request specific properties using $select
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=['displayName', 'mail', 'userPrincipalName']
        )

        request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        user = await self.user_client.me.get(request_configuration=request_config)
        return user
    
    async def get_thread_count(self, conversation_id):
        if conversation_id:
            try:
                response = await self.user_client.custom_get_request(f'/me/conversations/{conversation_id}/threads')
                threads_data = await response.json()  # Assuming the response needs to be parsed from JSON
                return len(threads_data.get('value', []))
            except Exception as e:
                print(f"Failed to retrieve threads for conversation {conversation_id}: {str(e)}")
                return 0
        return 0
    
    async def get_inbox(self, last_save_info):
        if last_save_info:
            last_run_time = last_save_info.get("last_procTime")
            filter_query = f"receivedDateTime ge {last_run_time} and receivedDateTime le {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}"
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['id', 'from', 'toRecipients', 'ccRecipients', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId'],
                top=50,
                orderby=['receivedDateTime ASC'], 
                filter=filter_query
            )
        else:
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['id', 'from', 'toRecipients', 'ccRecipients', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId'],
                top=50,
                orderby=['receivedDateTime ASC']
            )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters= query_params
        )

        messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
        return messages

    async def get_deleted_items(self,last_save_info):
        if last_save_info:
            last_run_time = last_save_info.get("last_procTime")
            filter_query = f"receivedDateTime ge {last_run_time} and receivedDateTime le {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}"
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['id', 'from', 'toRecipients', 'ccRecipients', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId'],
                top=50,
                orderby=['receivedDateTime DESC'], 
                filter=filter_query
            )
        else:
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['id', 'from', 'toRecipients', 'ccRecipients', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId'],
                top=50,
                orderby=['receivedDateTime DESC']
            )

        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        all_messages = []
        messages_page = await self.user_client.me.mail_folders.by_mail_folder_id('deleteditems').messages.get(
            request_configuration=request_config
        )

        # Process pages of messages
        while messages_page:
            if messages_page.value:
                all_messages.extend(messages_page.value)
            if messages_page.odata_next_link:
                next_page_builder = MessagesRequestBuilder(self.user_client.request_adapter, messages_page.odata_next_link)
                messages_page = await next_page_builder.get()
            else:
                break

        return all_messages
