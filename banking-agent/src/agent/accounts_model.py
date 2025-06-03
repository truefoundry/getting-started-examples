from pydantic import BaseModel
from traceloop.sdk.decorators import task


class Account(BaseModel):
    """Represents a bank account with a name and balance."""

    name: str
    balance: float


class UserAccounts(BaseModel):
    """Represents a collection of bank accounts for a user."""

    accounts: list[Account]

    @task()
    async def get_account_names(self) -> list[str]:
        """Returns a list of the names of all accounts."""
        return [account.name for account in self.accounts]

    @task()
    async def get_account(self, account_name: str) -> Account:
        """Returns the account with the given name.

        Raises:
            ValueError: If no account with the given name exists.
        """
        for account in self.accounts:
            if account_name == account.name:
                return account
        error_message = (
            f"There is no account named {account_name}. Options are {', '.join(await self.get_account_names())}"
        )
        raise ValueError(error_message)

    @task()
    async def transfer_money(self, amount: float, source_acc_name: str, dest_acc_name: str) -> None:
        """Transfers money from one account to another.

        Raises:
            ValueError: If the source account does not have enough funds.
        """
        source_account = await self.get_account(source_acc_name)
        destination_account = await self.get_account(dest_acc_name)

        if source_account.balance < amount:
            error_message = (
                f"There is not enough funds in account {source_acc_name}. "
                f"The balance is only ${source_account.balance}."
            )
            raise ValueError(error_message)

        source_account.balance = source_account.balance - amount
        destination_account.balance = destination_account.balance + amount
