from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock database
accounts = {
    "1234": {"balance": "₹16,000", "loan_status": "Active"},
    "7899": {"balance": "₹8,500", "loan_status": "Closed"},
    "9999": {"balance": "₹2,000", "loan_status": "Pending"},
}

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()

    intent = req.get('queryResult', {}).get('intent', {}).get('displayName')
    params = req.get('queryResult', {}).get('parameters', {})
    contexts = req.get('queryResult', {}).get('outputContexts', [])
    accountLast4 = params.get('accnumber')

    print(req)

    original_intent = None
    for context in contexts:
        if 'awaiting_auth' in context.get('name', ''):
            original_intent = context.get('parameters', {}).get('original_intent')

 
   

    def build_response(text, ssml=None, output_contexts=None):
        messages = [{"text": {"text": [text]}}]
        if ssml:
            messages.insert(0, {
                "platform": "AUDIO",
                "ssml": f"<speak>{ssml}</speak>"
            })

        response_data = {
            "fulfillmentText": text,  # <- ADD THIS LINE
            "fulfillmentMessages": messages
        }

        if output_contexts:
            response_data["outputContexts"] = output_contexts

        return jsonify(response_data)
    
    print(intent)

    if intent == 'authenticateUser':
        if accountLast4 in accounts:
            text = f"Authenticated successfully for account ending with {accountLast4}."
            ssml = f"Authenticated successfully for account ending with <say-as interpret-as='digits'>{accountLast4}</say-as>."
            output_contexts = [
                {
                    "name": f"{req['session']}/contexts/authenticated",
                    "lifespanCount": 5,
                    "parameters": {
                        "accnumber": accountLast4
                    }
                },
                {
                    "name": f"{req['session']}/contexts/redirect",
                    "lifespanCount": 1,
                    "parameters": {
                        "original_intent": original_intent or ""
                    }
                }
            ]
            return build_response(text, ssml, output_contexts)
        else:
            return build_response("Authentication failed. Please try again with a valid account number.",
                                  "Authentication failed. Please try again with a valid account number.")

    elif intent == 'getBalance':
        if not accountLast4:
            for context in contexts:
                if 'authenticated' in context.get('name', ''):
                    accountLast4 = context.get('parameters', {}).get('accnumber')
        balance = accounts.get(accountLast4, {}).get('balance')
        if balance:
            text = f"Your account balance is {balance}."
            ssml = f"Your account balance is <say-as interpret-as='currency'>{balance}</say-as>."
            return build_response(text, ssml)
        else:
            return build_response("Please authenticate first.",
                                  "Please authenticate first.")

    elif intent == 'getLoanStatus':
        if not accountLast4:
            for context in contexts:
                if 'authenticated' in context.get('name', ''):
                    accountLast4 = context.get('parameters', {}).get('accnumber')
        status = accounts.get(accountLast4, {}).get('loan_status')
        if status:
            text = f"Your loan status is {status}."
            ssml = f"Your loan status is <emphasis level='moderate'>{status}</emphasis>."
            return build_response(text, ssml)
        else:
            return build_response("Sorry, I couldn't find your account. Please authenticate first.",
                                  "Sorry, I couldn't find your account. Please authenticate first.")

    return build_response("Sorry, I didn't get that.", "Sorry, I didn't get that.")

if __name__ == '__main__':
    app.run(port=5000)
