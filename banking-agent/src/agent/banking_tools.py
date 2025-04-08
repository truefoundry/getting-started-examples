from langchain_core.tools import tool
from src.agent.accounts_model import Account, UserAccounts
from traceloop.sdk.decorators import tool as traceloop_tool

USER_ACCOUNTS = UserAccounts(
    accounts=[
        Account(name="current-account", balance=100),
        Account(name="savings-account", balance=3_0),
    ]
)


@tool
@traceloop_tool()
async def list_accounts() -> str:
    """List the names of the user's accounts."""
    return await USER_ACCOUNTS.get_account_names()


@tool
@traceloop_tool()
async def get_account_balance(account_name: str) -> str:
    """Get the balance of one of the user accounts by its exact name."""
    try:
        account = await USER_ACCOUNTS.get_account(account_name)
        return f"${account.balance}"
    except ValueError as error:
        return f"{error}"


@tool
@traceloop_tool()
async def transfer_money(amount: float, source_account: str, destination_account: str) -> str:
    """Transfer money between two accounts."""
    try:
        await USER_ACCOUNTS.transfer_money(amount, source_account, destination_account)
        return "Successful transaction"
    except ValueError as error:
        return f"{error}"


tools = [list_accounts, get_account_balance, transfer_money]
