from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            """
    You are an agent that helps the user manage their accounts in a Bank.

    Users may not refer to their account by the exact name, so try to get a list of valid names
    before getting a balance or executing a transaction.
    """
        ),
        MessagesPlaceholder(variable_name="messages", optional=True),
    ]
)
