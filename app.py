import os
import json
import datetime
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

class Transaction:
    def __init__(self, category, amount, description, transaction_type):
        self.date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.category = category
        self.amount = amount
        self.description = description
        self.transaction_type = transaction_type

    def to_dict(self):
        return {
            'date': self.date,
            'category': self.category,
            'amount': self.amount,
            'description': self.description,
            'transaction_type': self.transaction_type
        }

class Node:
    def __init__(self, transaction):
        self.transaction = transaction
        self.next = None

class Queue:
    def __init__(self):
        self.front = None
        self.rear = None
        self.size = 0

    def is_empty(self):
        return self.front is None

    def enqueue(self, transaction):
        new_node = Node(transaction)
        if self.rear is None:
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        self.size += 1

    def dequeue(self):
        if self.is_empty():
            return None
        temp = self.front
        self.front = self.front.next
        if self.front is None:
            self.rear = None
        self.size -= 1
        return temp.transaction

    def get_all_transactions(self):
        transactions = []
        current = self.front
        while current:
            transactions.append(current.transaction)
            current = current.next
        return transactions

class BSTNode:
    def __init__(self, transaction):
        self.transaction = transaction
        self.left = None
        self.right = None

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, transaction):
        if self.root is None:
            self.root = BSTNode(transaction)
        else:
            self._insert(self.root, transaction)

    def _insert(self, node, transaction):
        if transaction.amount < node.transaction.amount:
            if node.left is None:
                node.left = BSTNode(transaction)
            else:
                self._insert(node.left, transaction)
        else:
            if node.right is None:
                node.right = BSTNode(transaction)
            else:
                self._insert(node.right, transaction)

    def find_max(self):
        if not self.root:
            return None
        return self._find_max(self.root)

    def _find_max(self, node):
        while node.right:
            node = node.right
        return node.transaction

class TransactionManager:
    def __init__(self):
        self.transactions = Queue()
        self.transaction_bst = BinarySearchTree()
        self.load_data()

    def add_transaction(self, category, amount, description, transaction_type):
        transaction = Transaction(category, amount, description, transaction_type)
        self.transactions.enqueue(transaction)
        self.transaction_bst.insert(transaction)
        self.save_data()

    def save_data(self):
        data = [t.to_dict() for t in self.transactions.get_all_transactions()]
        with open('transactions.json', 'w') as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if os.path.exists('transactions.json'):
            with open('transactions.json', 'r') as f:
                data = json.load(f)
                for item in data:
                    transaction = Transaction(
                        item['category'], item['amount'], item['description'], item['transaction_type']
                    )
                    transaction.date = item['date']
                    self.transactions.enqueue(transaction)
                    self.transaction_bst.insert(transaction)

    def get_total_balance(self):
        total_income = sum(t.amount for t in self.transactions.get_all_transactions() if t.transaction_type == 'income')
        total_expenses = sum(t.amount for t in self.transactions.get_all_transactions() if t.transaction_type == 'expense')
        balance = total_income - total_expenses
        return total_income, total_expenses, balance

    def get_income_and_expenses(self):
        dates = []
        income = []
        expenses = []
        for t in self.transactions.get_all_transactions():
            dates.append(t.date)
            if t.transaction_type == 'income':
                income.append(t.amount)
                expenses.append(0)
            else:
                income.append(0)
                expenses.append(t.amount)
        return dates, income, expenses

    def find_max_transaction(self):
        return self.transaction_bst.find_max()

# Initialize transaction manager
manager = TransactionManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        description = request.form['description']
        transaction_type = request.form['transaction_type']

        # Add transaction using the manager
        manager.add_transaction(category, amount, description, transaction_type)

        return redirect(url_for('transactions'))

    return render_template('index.html')

@app.route('/transactions')
def transactions():
    transactions = manager.transactions.get_all_transactions()
    return render_template('transactions.html', transactions=transactions)

@app.route('/balance')
def balance():
    total_income, total_expenses, balance = manager.get_total_balance()
    return render_template('balance.html', total_income=total_income, total_expenses=total_expenses, balance=balance)

@app.route('/max_transaction')
def max_transaction():
    max_trans = manager.find_max_transaction()
    return render_template('max_transaction.html', transaction=max_trans)

@app.route('/graph')
def graph():
    dates, income, expenses = manager.get_income_and_expenses()

    plt.figure(figsize=(10, 6))

    # Plotting income and expenses over time
    plt.plot(dates, income, label="Income", marker='o', linestyle='-', color='green')
    plt.plot(dates, expenses, label="Expenses", marker='o', linestyle='-', color='red')

    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.title("Income vs Expenses Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # Save the plot to a bytes object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
