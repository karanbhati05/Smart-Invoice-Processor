"""
Invoice Data Extraction Module
Extracts invoice data directly from images using Gemini Vision API.
"""

import os
import requests
import json
import base64


def extract_invoice_data(image_path, known_vendors=None, ocr_api_key=None):
    """
    Extract key invoice information from an image using Gemini Vision API.
    
    Args:
        image_path (str): Path to the invoice image file
        known_vendors (list, optional): Deprecated - not used
        ocr_api_key (str, optional): Deprecated - not used
    
    Returns:
        dict: Dictionary containing vendor, date, total, and other invoice fields
    """
    # Use Gemini Vision API directly - no OCR needed
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if not gemini_key:
        return {
            'vendor': None,
            'date': None,
            'total': None,
            'error': 'GEMINI_API_KEY environment variable not set'
        }
    
    try:
        print("🔍 Processing invoice with Gemini Vision API...")
        result = extract_with_gemini_vision(image_path, gemini_key)
        print("✅ Gemini Vision extraction successful!")
        return result
    except Exception as e:
        print(f"❌ Gemini Vision extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'vendor': None,
            'date': None,
            'total': None,
            'error': f'Gemini Vision API failed: {str(e)}'
        }


def extract_with_gemini_vision(image_path, api_key):
    """
    Use Gemini Vision API to extract invoice data directly from image.
    Uses Gemini's multimodal capabilities to read and understand invoices.
    
    Args:
        image_path (str): Path to the image file
        api_key (str): Gemini API key
    
    Returns:
        dict: Extracted invoice data with all fields
    """
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine mime type from file extension
    ext = image_path.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'pdf': 'application/pdf'
    }
    mime_type = mime_types.get(ext, 'image/jpeg')
    
    # Configure Gemini API request
    model = "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    
    prompt = """Analyze this invoice image and extract all relevant information. Return ONLY valid JSON in this exact format:

{
  "vendor": "company/vendor name",
  "invoice_number": "invoice or receipt number",
  "date": "date in YYYY-MM-DD format",
  "subtotal": "subtotal amount with currency symbol",
  "tax": "tax amount with currency symbol",
  "total": "total amount with currency symbol",
  "summary": "brief 1-sentence summary of what this invoice is for",
  "line_items": [
    {"description": "item/service description", "quantity": "quantity", "price": "unit price with currency"}
  ]
}

Important:
- Return null for any field you cannot find
- Keep currency symbols with amounts (e.g., "$150.00", "€45.50")
- Format dates as YYYY-MM-DD
- Extract ALL line items you can see
- Be precise and accurate"""

    # Build request payload with image and prompt
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096
        }
    }
    
    print(f"📤 Sending {mime_type} to Gemini Vision API (model: {model})...")
    response = requests.post(url, json=payload, timeout=30)
    
    # Check for API errors
    if response.status_code != 200:
        error_text = response.text
        print(f"❌ Gemini Vision API Error ({response.status_code}): {error_text}")
        raise Exception(f"Gemini Vision API returned status {response.status_code}: {error_text}")
    
    result = response.json()
    print(f"📥 Received response from Gemini")
    
    # Extract and parse the response
    if 'candidates' in result and len(result['candidates']) > 0:
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        print(f"📄 Generated text length: {len(generated_text)} chars")
        
        # Clean up markdown formatting
        generated_text = generated_text.replace('```json', '').replace('```', '').strip()
        
        try:
            data = json.loads(generated_text)
            print(f"✅ Successfully parsed invoice data")
            
            return {
                'vendor': data.get('vendor'),
                'date': data.get('date'),
                'total': data.get('total'),
                'invoice_number': data.get('invoice_number'),
                'tax': data.get('tax'),
                'subtotal': data.get('subtotal'),
                'summary': data.get('summary'),
                'line_items': data.get('line_items', []),
                '_ai_used': True,
                '_method': 'gemini_vision'
            }
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {str(e)}")
            print(f"Raw response: {generated_text[:500]}...")
            raise Exception(f"Invalid JSON response from Gemini: {str(e)}")
    
    print("❌ No candidates in Gemini response")
    raise Exception("No valid response from Gemini Vision API")

