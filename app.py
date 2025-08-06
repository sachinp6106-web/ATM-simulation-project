from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# User data: account number → [PIN, balance, transaction history, name, account_type]
users = {
    "123456": ["1234", 100000.0, [], "Sachin Parmar", "Savings"],
    "654321": ["4321", 95000.0, [], "Raju Singh", "Current"],
    "789012": ["5678", 75000.0, [], "Cheta Paliwal", "Savings"],
    "345678": ["9012", 200000.0, [], "Ravina Kumari", "Premium"]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    account_number = data.get('accountNumber')
    pin = data.get('pin')
    
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    if users[account_number][0] != pin:
        return jsonify({'success': False, 'message': 'Invalid PIN'}), 401
    
    user_info = {
        'accountNumber': account_number,
        'name': users[account_number][3],
        'accountType': users[account_number][4],
        'balance': users[account_number][1]
    }
    
    return jsonify({'success': True, 'user': user_info})

@app.route('/api/balance/<account_number>')
def get_balance(account_number):
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    user_info = {
        'accountNumber': account_number,
        'name': users[account_number][3],
        'accountType': users[account_number][4],
        'balance': users[account_number][1]
    }
    
    return jsonify({'success': True, 'user': user_info})

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    account_number = data.get('accountNumber')
    amount = float(data.get('amount'))
    
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    if amount > users[account_number][1]:
        return jsonify({'success': False, 'message': 'Insufficient funds'}), 400
    
    # Process withdrawal
    users[account_number][1] -= amount
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users[account_number][2].append(f"[{timestamp}] Withdrew ₹{amount:,.2f}")
    
    return jsonify({
        'success': True,
        'message': f'₹{amount:,.2f} withdrawn successfully',
        'newBalance': users[account_number][1]
    })

@app.route('/api/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    account_number = data.get('accountNumber')
    amount = float(data.get('amount'))
    
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    # Process deposit
    users[account_number][1] += amount
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users[account_number][2].append(f"[{timestamp}] Deposited ₹{amount:,.2f}")
    
    return jsonify({
        'success': True,
        'message': f'₹{amount:,.2f} deposited successfully',
        'newBalance': users[account_number][1]
    })

@app.route('/api/change-pin', methods=['POST'])
def change_pin():
    data = request.get_json()
    account_number = data.get('accountNumber')
    current_pin = data.get('currentPin')
    new_pin = data.get('newPin')
    
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    if users[account_number][0] != current_pin:
        return jsonify({'success': False, 'message': 'Incorrect current PIN'}), 401
    
    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({'success': False, 'message': 'PIN must be exactly 4 digits'}), 400
    
    # Update PIN
    users[account_number][0] = new_pin
    
    return jsonify({'success': True, 'message': 'PIN updated successfully'})

@app.route('/api/transactions/<account_number>')
def get_transactions(account_number):
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    transactions = users[account_number][2][-10:]  # Last 10 transactions
    
    return jsonify({
        'success': True,
        'transactions': transactions
    })

@app.route('/api/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    sender_acc = data.get('senderAccount')
    receiver_acc = data.get('receiverAccount')
    amount = float(data.get('amount'))
    
    if sender_acc not in users:
        return jsonify({'success': False, 'message': 'Sender account not found'}), 404
    
    if receiver_acc not in users:
        return jsonify({'success': False, 'message': 'Recipient account not found'}), 404
    
    if sender_acc == receiver_acc:
        return jsonify({'success': False, 'message': 'Cannot transfer to your own account'}), 400
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    if amount > users[sender_acc][1]:
        return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
    
    # Process transfer
    users[sender_acc][1] -= amount
    users[receiver_acc][1] += amount
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users[sender_acc][2].append(f"[{timestamp}] Transferred ₹{amount:,.2f} to {receiver_acc}")
    users[receiver_acc][2].append(f"[{timestamp}] Received ₹{amount:,.2f} from {sender_acc}")
    
    return jsonify({
        'success': True,
        'message': f'₹{amount:,.2f} transferred successfully to {users[receiver_acc][3]}',
        'newBalance': users[sender_acc][1]
    })

@app.route('/api/receipt/<account_number>')
def get_receipt(account_number):
    if account_number not in users:
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_info = users[account_number]
    
    receipt = {
        'dateTime': timestamp,
        'accountNumber': account_number,
        'accountHolder': user_info[3],
        'accountType': user_info[4],
        'balance': user_info[1],
        'transactions': user_info[2][-5:]  # Last 5 transactions
    }
    
    return jsonify({'success': True, 'receipt': receipt})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    account_type = data.get('accountType')
    deposit = float(data.get('deposit', 0))
    pin = data.get('pin')
    if not name or not account_type or deposit < 1 or not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({'success': False, 'message': 'Invalid input.'}), 400
    # Generate new account number (simple: max+1)
    new_acc = str(max([int(acc) for acc in users.keys()] + [100000]) + 1)
    users[new_acc] = [pin, deposit, [], name, account_type]
    return jsonify({'success': True, 'accountNumber': new_acc})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 