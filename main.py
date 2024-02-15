import hashlib
import datetime
import pyodbc
import random

conn_str = (
    r'driver={SQL Server};'
    r'server=(local);'
    r'database=bank;'
    r'trusted_connection=yes;'
)

cnxn = pyodbc.connect(conn_str)

cursor = cnxn.cursor()


# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Function to register a new user
def register_user():
    firstname = input("Enter your first name: ")
    lastname = input("Enter your last name: ")
    username = input("Choose a username: ")
    nationalID = input("Enter your national ID: ")
    password = input("Enter your password: ")

    # Check if the userID is unique
    cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
    if cursor.fetchone():
        print("userID already exists. Please choose another one.")
        return

    hashed_password = hash_password(password)
    cursor.execute("INSERT INTO Users (firstname, lastname, username, password , nationalID) VALUES (?, ?, ?, ?, ?)",
                   (firstname, lastname, username, hashed_password, nationalID))
    cnxn.commit()
    print("Registration successful!")


# Function to log in
def login():
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    hashed_password = hash_password(password)
    cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, hashed_password))
    record = cursor.fetchone()
    if record:
        print("Login successful!")
        print("Welcome " + record[1] + " " + record[2])
        return record[0]
    else:
        print("Invalid username or password.")
        return None


def generate_bank_number():
    shabaNumber = "IR" + ''.join([str(random.randint(0, 9)) for _ in range(24)])
    cardNumber = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    return cardNumber, shabaNumber


# Function to create a new account
def create_new_account(userID):
    initial_balance = float(input("Enter the initial balance for the new account: "))
    cardNumber, shabaNumber = generate_bank_number()
    cursor.execute("INSERT INTO Accounts (userID, cardNumber, shabaNumber, balance) VALUES (?, ?, ?, ?)",
                   (userID, cardNumber, shabaNumber, initial_balance))
    cnxn.commit()
    print("Account created successfully!")


# Function to transfer money between accounts
def transfer_money(source, destination, amount, transaction_type):
    # Check the transaction type to apply limits
    daily_limit = 0
    if transaction_type == 'cardNumber':
        daily_limit = 10000000
    elif transaction_type == 'Satna':
        daily_limit = 20000000
    elif transaction_type == 'Paya':
        daily_limit = 50000000

    # Check if the daily limit is exceeded
    cursor.execute("SELECT SUM(amount) FROM Transactions WHERE date = ? AND transactiontype = ? AND source = ?",
                   (datetime.date.today().strftime("%x"), transaction_type, source))
    temp = cursor.fetchone()[0]
    if temp:
        total_daily_amount = float(temp)
    else:
        total_daily_amount = 0.0

    if total_daily_amount + amount > daily_limit:
        print(f"Daily limit for {transaction_type} transactions exceeded!")
        return

    # Update source and destination account balances
    cursor.execute("UPDATE Accounts SET balance = balance - ? WHERE cardNumber = ?", (amount, source))
    cursor.execute("UPDATE Accounts SET balance = balance + ? WHERE cardNumber = ?", (amount, destination))

    cursor.execute(
        "INSERT INTO Transactions (source, destination, amount, transactiontype, date, time) VALUES ( ?, ?, ?, ?, ?, ?)",
        (source, destination, amount, transaction_type, datetime.date.today().strftime("%x"),
         datetime.datetime.now().time().strftime("%X")))
    cnxn.commit()
    print("Transaction successful!")


# Function to get the last n transactions for an account
def get_last_transactions(userID, n):
    source = input("Enter the source card number: ")
    cursor.execute(
        "SELECT * FROM Transactions WHERE source = ? OR destination = ? ORDER BY transactionID DESC ",
        (source, source))
    transactions = cursor.fetchall()
    if transactions:
        print("\nLast N Transactions:")
        i = 1
        for transaction in transactions:
            if i > n: break
            print(transaction)
            i += 1
    else:
        print("\n no transaction have been found")
        return


# Function to check transaction validity by tracking code
def check_transaction_by_code(transaction_id):
    cursor.execute("SELECT * FROM Transactions WHERE transactionID = ?", (transaction_id,))
    transaction = cursor.fetchone()
    if transaction:
        print("\nTransaction Details:")
        print(transaction)
    else:
        print("Invalid transaction code.")


# Function to perform transactions
def perform_transaction(userID, transaction_type):
    destination = input("Enter the destination card number: ")
    source = input("Enter the source card number: ")
    amount = float(input("Enter the amount: "))

    # Check if the user has sufficient balance
    cursor.execute("SELECT balance FROM Accounts WHERE userID = ? AND cardNumber = ?", (userID, source))
    balance = cursor.fetchone()[0]
    if balance < amount:
        print("Insufficient balance!")
        return

    transfer_money(source, destination, amount, transaction_type)


# Function to receive the last N transactions
def receive_last_n_transactions(userID):
    n = int(input("Enter the number of transactions to retrieve: "))
    get_last_transactions(userID, n)


# Function to receive a transaction by ID
def receive_transaction_by_id():
    transaction_id = input("Enter the transaction ID: ")
    check_transaction_by_code(transaction_id)


# Menu loop
while True:
    print("\nMenu:")
    print("1. Sign Up")
    print("2. Log In")
    print("3. Create New Account")
    print("4. Transaction by Card Number")
    print("5. Transaction by Satna Number")
    print("6. Transaction by Paya")
    print("7. Receive Last N Transactions")
    print("8. Receive Transaction by Transaction ID")
    print("9. Exit")

    choice = input("Enter your choice (1-9): ")

    if choice == '1':
        register_user()
    elif choice == '2':
        logged_in_user = login()
    elif choice == '3':
        create_new_account(logged_in_user)
    elif choice == '4':
        perform_transaction(logged_in_user, "cardNumber")
    elif choice == '5':
        perform_transaction(logged_in_user, "Satna")
    elif choice == '6':
        perform_transaction(logged_in_user, "Paya")
    elif choice == '7':
        receive_last_n_transactions(logged_in_user)
    elif choice == '8':
        receive_transaction_by_id()
    elif choice == '9':
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 9.")

# Close the database connection
cnxn.close()
