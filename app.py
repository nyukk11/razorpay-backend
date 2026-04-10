import os
import pkgutil

# Monkey patch to fix the missing ImpImporter (MUST be before importing razorpay)
if not hasattr(pkgutil, 'ImpImporter'):
    class ImpImporter:
        pass
    pkgutil.ImpImporter = ImpImporter

# Now import razorpay and other libraries
import razorpay
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for your Flutter app

# Get keys from environment variables (never hardcode!)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@app.route('/')
def home():
    return jsonify({"message": "Razorpay Backend is Running!", "status": "active"})

@app.route('/create-order', methods=['POST'])
def create_order():
    """
    Create a Razorpay Order
    Expects JSON: {"amount": 10000, "currency": "INR", "receipt": "order_rcpt_1"}
    Amount is in paise (10000 paise = ₹100)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'amount' not in data:
            return jsonify({"error": "Amount is required"}), 400
        
        amount = data['amount']
        currency = data.get('currency', 'INR')
        receipt = data.get('receipt', f'receipt_{int(os.times().system)}')
        
        # Create order on Razorpay
        order_data = {
            'amount': amount,
            'currency': currency,
            'receipt': receipt,
            'payment_capture': 1  # Auto-capture payment
        }
        
        order = client.order.create(order_data)
        
        return jsonify({
            "success": True,
            "order_id": order['id'],
            "amount": order['amount'],
            "currency": order['currency']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    """
    Verify payment signature
    Expects JSON: {"razorpay_order_id": "order_xxx", "razorpay_payment_id": "pay_xxx", "razorpay_signature": "signature_xxx"}
    """
    try:
        data = request.get_json()
        
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        # Verify signature
        client.utility.verify_payment_signature(params_dict)
        
        return jsonify({
            "success": True,
            "message": "Payment verified successfully"
        })
        
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Signature verification failed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payment-status/<payment_id>', methods=['GET'])
def check_payment_status(payment_id):
    """
    Check payment status by payment ID
    """
    try:
        payment = client.payment.fetch(payment_id)
        return jsonify({
            "payment_id": payment['id'],
            "status": payment['status'],
            "amount": payment['amount'],
            "method": payment['method']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)