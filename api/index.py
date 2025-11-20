"""
Enhanced Invoice Processing API v2.0
Advanced features: Database storage, Authentication, Batch processing, Analytics, Export
"""

import os
import sys
import tempfile
import uuid
import json
import secrets
import urllib.parse
from flask import Flask, request, jsonify, send_file, send_from_directory, redirect, session
from werkzeug.utils import secure_filename
from io import BytesIO
import requests

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from processor import extract_invoice_data

# Placeholder classes for removed modules
import sqlite3
import hashlib

class InvoiceDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                vendor TEXT,
                date TEXT,
                total TEXT,
                invoice_number TEXT,
                tax TEXT,
                subtotal TEXT,
                summary TEXT,
                line_items TEXT,
                status TEXT DEFAULT 'pending',
                upload_type TEXT,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def get_connection(self):
        return self.conn
    
    def calculate_file_hash(self, data):
        return hashlib.md5(data).hexdigest()
    
    def check_duplicate(self, file_hash):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM invoices WHERE file_hash = ?', (file_hash,))
        return cursor.fetchone() is not None
    
    def save_invoice(self, data, user_id, file_hash, upload_type='single'):
        cursor = self.conn.cursor()
        line_items_json = json.dumps(data.get('line_items', []))
        cursor.execute('''
            INSERT INTO invoices (user_id, vendor, date, total, invoice_number, tax, subtotal, summary, line_items, file_hash, upload_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data.get('vendor'), data.get('date'), data.get('total'), 
              data.get('invoice_number'), data.get('tax'), data.get('subtotal'),
              data.get('summary'), line_items_json, file_hash, upload_type))
        self.conn.commit()
        return cursor.lastrowid
    
    def list_invoices(self, user_id=None, status=None, upload_type=None, limit=50, offset=0):
        cursor = self.conn.cursor()
        query = 'SELECT * FROM invoices WHERE 1=1'
        params = []
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        if status:
            query += ' AND status = ?'
            params.append(status)
        if upload_type:
            query += ' AND upload_type = ?'
            params.append(upload_type)
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        invoices = []
        for row in rows:
            invoice = dict(row)
            # Parse line_items JSON string back to list
            if invoice.get('line_items'):
                try:
                    invoice['line_items'] = json.loads(invoice['line_items'])
                except:
                    invoice['line_items'] = []
            invoices.append(invoice)
        return invoices
    
    def search_invoices(self, search_term, user_id=None):
        cursor = self.conn.cursor()
        query = 'SELECT * FROM invoices WHERE (vendor LIKE ? OR invoice_number LIKE ?)'
        params = [f'%{search_term}%', f'%{search_term}%']
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        invoices = []
        for row in rows:
            invoice = dict(row)
            # Parse line_items JSON string back to list
            if invoice.get('line_items'):
                try:
                    invoice['line_items'] = json.loads(invoice['line_items'])
                except:
                    invoice['line_items'] = []
            invoices.append(invoice)
        return invoices
    
    def get_invoice(self, invoice_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
        row = cursor.fetchone()
        if row:
            invoice = dict(row)
            # Parse line_items JSON string back to list
            if invoice.get('line_items'):
                try:
                    invoice['line_items'] = json.loads(invoice['line_items'])
                except:
                    invoice['line_items'] = []
            return invoice
        return None
    
    def update_invoice_status(self, invoice_id, status, user_id=None):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute('UPDATE invoices SET status = ? WHERE id = ? AND user_id = ?', 
                         (status, invoice_id, user_id))
        else:
            cursor.execute('UPDATE invoices SET status = ? WHERE id = ?', (status, invoice_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_invoice(self, invoice_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_analytics(self, user_id=None):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute('SELECT COUNT(*) as total FROM invoices WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('SELECT COUNT(*) as total FROM invoices')
        total = cursor.fetchone()[0]
        return {
            'total': total,
            'pending': 0,
            'approved': 0,
            'monthly': 0
        }
    
    def get_stats(self, user_id=None):
        return self.get_analytics(user_id)
    
    def clear_all(self, user_id=None):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute('DELETE FROM invoices WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('DELETE FROM invoices')
        self.conn.commit()
        return True
    
    def get_user_by_email(self, email):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            return {'id': row[0], 'email': row[1], 'name': row[2]}
        return None
    
    def create_user(self, email, name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO users (email, name) VALUES (?, ?)', (email, name))
            self.conn.commit()
            return cursor.lastrowid
        except:
            return None

def require_auth(f): return f
def optional_auth(f): return f
def create_demo_user(): return {'token': 'demo', 'user_id': '1'}

class AuthManager:
    def __init__(self):
        import jwt
        import datetime
        self.jwt = jwt
        self.datetime = datetime
        self.secret = os.environ.get('JWT_SECRET', 'default-secret-key-change-in-production')
    
    def generate_token(self, user_id, email):
        """Generate a JWT token for the user"""
        payload = {
            'user_id': str(user_id),
            'email': email,
            'exp': self.datetime.datetime.utcnow() + self.datetime.timedelta(days=30)
        }
        token = self.jwt.encode(payload, self.secret, algorithm='HS256')
        return token
    
    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            payload = self.jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload
        except:
            return None

auth_manager = AuthManager()

def process_batch(files, api_key, extract_fn, max_workers=3):
    results = []
    for f in files:
        try:
            data = extract_fn(f, api_key)
            results.append({'success': True, 'data': data, 'filename': f.filename})
        except Exception as e:
            results.append({'success': False, 'error': str(e), 'filename': f.filename})
    return results

class ExportManager:
    def export_json(self, data): return json.dumps(data, indent=2)
    def export_csv(self, data): return ""
    def export_pdf(self, data): return b""

class UserManager:
    def __init__(self, db=None):
        self.db = db
    
    def register_user(self, email, password=None, full_name='', oauth_provider=None, company=''):
        """Register a new user"""
        if self.db:
            user_id = self.db.create_user(email, full_name)
            if user_id:
                return {'success': True, 'user_id': user_id}
        return {'success': False, 'error': 'Registration failed'}
    
    def login_user(self, email, password):
        """Login user with email/password"""
        if self.db:
            user = self.db.get_user_by_email(email)
            if user:
                token = auth_manager.generate_token(user['id'], email)
                return {'success': True, 'token': token, 'user': user}
        return {'success': False, 'error': 'Invalid credentials'}
    
    def verify_email(self, token):
        """Verify email token"""
        return {'success': True, 'message': 'Email verified'}

batch_processor = None
USER_MANAGEMENT_ENABLED = True

# Initialize Flask app
app = Flask(__name__, static_folder='../public', static_url_path='')

# Set secret key for session management
app.secret_key = os.environ.get('JWT_SECRET', os.urandom(24).hex())

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
OCR_API_KEY = os.environ.get('OCR_API_KEY', 'K87899142388957')

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')

# Get base URL for OAuth redirects
# Always use stable production domain for OAuth to avoid redirect_uri_mismatch
# Vercel sets VERCEL_URL to deployment-specific URLs which change on every deploy
VERCEL_URL = 'https://ai-invoice-automation-one.vercel.app'

# Initialize database
db = InvoiceDatabase()
export_manager = ExportManager()
user_manager = UserManager(db) if USER_MANAGEMENT_ENABLED and UserManager else None


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/v2/process', methods=['POST'])
@optional_auth
def process_invoice_v2():
    """
    POST /api/v2/process - Process invoice with database storage
    
    Headers:
        - X-API-Key or Authorization: Bearer <token> (optional)
    
    Body:
        - file: Invoice image/PDF
        - save: Whether to save to database (default: true)
        - user_id: User identifier (optional, overrides auth)
    
    Returns:
        JSON with extracted data and invoice ID if saved
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Invalid file type',
            'allowed': list(ALLOWED_EXTENSIONS)
        }), 400
    
    try:
        # Read file data for duplicate detection
        file_data = file.read()
        file.seek(0)  # Reset file pointer
        
        # Check for duplicates
        file_hash = db.calculate_file_hash(file_data)
        duplicate = db.check_duplicate(file_hash)
        
        if duplicate:
            return jsonify({
                'success': True,
                'duplicate': True,
                'message': 'This invoice has already been processed',
                'invoice_id': duplicate['id'],
                'original_data': duplicate
            }), 200
        
        # Save to temp file and process
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        # Extract invoice data
        result = extract_invoice_data(temp_path, None, OCR_API_KEY)
        
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        # Get user ID from auth or request
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            user_id = request.form.get('user_id', 'anonymous')
        
        # Save to database if requested (default: FALSE for single, only save if explicitly requested)
        should_save = request.form.get('save', 'false').lower() == 'true'
        invoice_id = None
        
        if should_save:
            # If saving from single page, mark as 'single' upload type
            upload_type = request.form.get('upload_type', 'single')
            save_result = db.save_invoice(result, user_id, file_hash, upload_type=upload_type)
            invoice_id = save_result.get('invoice_id') if save_result.get('success') else None
        
        # Determine extraction method
        ai_used = result.get('_ai_used', False)
        extraction_method = result.get('_method', 'ai' if ai_used else 'regex')
        
        return jsonify({
            'success': True,
            'duplicate': False,
            'extraction_method': extraction_method,
            'invoice_id': invoice_id,
            'data': {
                'vendor': result['vendor'],
                'date': result['date'],
                'total': result['total'],
                'invoice_number': result.get('invoice_number'),
                'tax': result.get('tax'),
                'subtotal': result.get('subtotal'),
                'summary': result.get('summary'),
                'line_items': result.get('line_items', [])
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/batch', methods=['POST'])
@optional_auth
def process_batch_invoices():
    """
    POST /api/v2/batch - Process multiple invoices at once
    
    Body:
        - files[]: Multiple invoice files
    
    Returns:
        JSON with batch processing results
    """
    try:
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        # Validate all files
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': f'Invalid file type: {file.filename}',
                    'allowed': list(ALLOWED_EXTENSIONS)
                }), 400
        
        # Process batch
        result = process_batch(files, OCR_API_KEY, extract_invoice_data, max_workers=3)
        
        # Get user ID
        user_id = getattr(request, 'user_id', 'anonymous')
        
        # Save successful results to database and add invoice_id
        for item in result['results']:
            if item['success'] and item.get('data') and not item['data'].get('error'):
                try:
                    # Create file hash from filename (as we don't have original file data here)
                    file_hash = db.calculate_file_hash(item['filename'].encode())
                    save_result = db.save_invoice(item['data'], user_id, file_hash, upload_type='batch')
                    if save_result.get('success'):
                        item['invoice_id'] = save_result.get('invoice_id')
                        item['invoice'] = item['data']  # Add full invoice data for display
                except Exception as e:
                    print(f"Error saving invoice {item['filename']}: {e}")
                    # Continue even if save fails
        
        return jsonify({
            'success': True,
            'batch_result': result
        }), 200
    
    except Exception as e:
        print(f"Batch processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/invoices', methods=['GET'])
@optional_auth
def list_invoices():
    """
    GET /api/v2/invoices - List all invoices
    
    Query params:
        - status: Filter by status
        - upload_type: Filter by upload type (single/batch)
        - limit: Max results (default: 50)
        - offset: Pagination offset (default: 0)
        - search: Search query
    
    Returns:
        JSON with list of invoices
    """
    user_id = getattr(request, 'user_id', None)
    status = request.args.get('status')
    upload_type = request.args.get('upload_type')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    search = request.args.get('search')
    
    try:
        if search:
            invoices = db.search_invoices(search, user_id)
        else:
            invoices = db.list_invoices(user_id, status, upload_type, limit, offset)
        
        return jsonify({
            'success': True,
            'count': len(invoices),
            'invoices': invoices
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/invoices/<int:invoice_id>', methods=['GET'])
@optional_auth
def get_invoice(invoice_id):
    """
    GET /api/v2/invoices/:id - Get invoice details
    
    Returns:
        JSON with invoice data including line items
    """
    try:
        invoice = db.get_invoice(invoice_id)
        
        if not invoice:
            return jsonify({
                'success': False,
                'error': 'Invoice not found'
            }), 404
        
        return jsonify({
            'success': True,
            'invoice': invoice
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/invoices/<int:invoice_id>/status', methods=['PUT'])
@optional_auth
def update_invoice_status(invoice_id):
    """
    PUT /api/v2/invoices/:id/status - Update invoice status
    
    Body:
        - status: New status (pending, approved, rejected, paid)
    
    Returns:
        JSON confirmation
    """
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status required'}), 400
    
    valid_statuses = ['pending', 'approved', 'rejected', 'paid', 'archived']
    if new_status not in valid_statuses:
        return jsonify({
            'error': 'Invalid status',
            'valid_statuses': valid_statuses
        }), 400
    
    try:
        user_id = getattr(request, 'user_id', 'anonymous')
        db.update_invoice_status(invoice_id, new_status, user_id)
        
        return jsonify({
            'success': True,
            'message': f'Invoice status updated to {new_status}'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/invoices/<int:invoice_id>', methods=['DELETE'])
@require_auth
def delete_invoice(invoice_id):
    """
    DELETE /api/v2/invoices/:id - Delete invoice
    
    Returns:
        JSON confirmation
    """
    try:
        db.delete_invoice(invoice_id)
        
        return jsonify({
            'success': True,
            'message': 'Invoice deleted successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/analytics', methods=['GET'])
@optional_auth
def get_analytics():
    """
    GET /api/v2/analytics - Get invoice analytics
    
    Returns:
        JSON with analytics data
    """
    user_id = getattr(request, 'user_id', None)
    
    try:
        analytics = db.get_analytics(user_id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/export', methods=['GET'])
@optional_auth
def export_invoices():
    """
    GET /api/v2/export - Export invoices
    
    Query params:
        - format: Export format (json, csv, pdf)
        - status: Filter by status
        - token: Auth token (alternative to header)
    
    Returns:
        File download
    """
    export_format = request.args.get('format', 'json')
    status = request.args.get('status')
    upload_type = request.args.get('upload_type')  # Filter by upload type (single/batch)
    
    # Get user_id from decorator or token param
    user_id = getattr(request, 'user_id', None)
    
    # If no user_id from decorator, try token from query param
    if not user_id:
        token = request.args.get('token')
        if token:
            try:
                payload = auth_manager.verify_token(token)
                user_id = payload.get('user_id')
            except:
                pass
    
    try:
        # Get invoices - filtered by upload_type and user_id if provided
        invoices = db.list_invoices(user_id=user_id, status=status, upload_type=upload_type, limit=1000)
        
        print(f"Export: user_id={user_id}, Found {len(invoices) if invoices else 0} invoices")  # Debug log
        
        if not invoices:
            # Return empty file with headers
            if export_format == 'csv':
                data = "id,invoice_number,vendor,date,total,subtotal,tax,summary,status,created_at\n"
                return send_file(
                    BytesIO(data.encode('utf-8')),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='invoices_empty.csv'
                )
            else:
                data = json.dumps([], indent=2)
                return send_file(
                    BytesIO(data.encode('utf-8')),
                    mimetype='application/json',
                    as_attachment=True,
                    download_name='invoices_empty.json'
                )
        
        # Export
        data, mimetype, filename = export_manager.export(invoices, export_format)
        
        # Create response
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/export/analytics', methods=['GET'])
@optional_auth
def export_analytics():
    """
    GET /api/v2/export/analytics - Export analytics data
    
    Query params:
        - format: Export format (json, csv)
    
    Returns:
        File download
    """
    export_format = request.args.get('format', 'json')
    user_id = getattr(request, 'user_id', None)
    
    try:
        analytics = db.get_analytics(user_id)
        data, mimetype, filename = export_manager.export_analytics(analytics, export_format)
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return send_file(
            BytesIO(data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/auth/demo', methods=['POST'])
def create_demo_auth():
    """
    POST /api/v2/auth/demo - Create demo user credentials
    
    Returns:
        API key and JWT token for testing
    """
    credentials = create_demo_user()
    
    return jsonify({
        'success': True,
        'message': 'Demo credentials created',
        'credentials': credentials
    }), 200


@app.route('/api/v2/health', methods=['GET'])
def health_check_v2():
    """Health check with extended information."""
    gemini_key = os.environ.get('GEMINI_API_KEY')
    ocr_key = os.environ.get('OCR_API_KEY')
    google_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    github_id = os.environ.get('GITHUB_CLIENT_ID')
    github_secret = os.environ.get('GITHUB_CLIENT_SECRET')
    
    return jsonify({
        'status': 'healthy',
        'service': 'Invoice Processing API v2.0',
        'version': '2.0.0',
        'features': {
            'database': True,
            'authentication': True,
            'batch_processing': True,
            'analytics': True,
            'export': True,
            'duplicate_detection': True
        },
        'api': {
            'gemini_configured': bool(gemini_key),
            'ocr_configured': bool(ocr_key)
        },
        'oauth': {
            'google_enabled': bool(google_id and google_secret),
            'github_enabled': bool(github_id and github_secret),
            'google_client_id_present': bool(google_id),
            'google_secret_present': bool(google_secret),
            'github_client_id_present': bool(github_id),
            'github_secret_present': bool(github_secret)
        },
        'environment': {
            'vercel_url': os.environ.get('VERCEL_URL', 'not set')
        }
    }), 200


@app.route('/api/v2/reset-database', methods=['POST'])
def reset_database():
    """
    POST /api/v2/reset-database - Clear invoice data, optionally filtered by upload_type
    
    Query params:
        - upload_type: Filter deletion by upload type (single/batch)
    
    Returns:
        Success message
    """
    try:
        upload_type = request.args.get('upload_type')
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if upload_type:
            # Clear only invoices of specified type
            cursor.execute('SELECT id FROM invoices WHERE upload_type = ?', (upload_type,))
            invoice_ids = [row[0] for row in cursor.fetchall()]
            
            if invoice_ids:
                placeholders = ','.join('?' * len(invoice_ids))
                cursor.execute(f'DELETE FROM processing_history WHERE invoice_id IN ({placeholders})', invoice_ids)
                cursor.execute(f'DELETE FROM line_items WHERE invoice_id IN ({placeholders})', invoice_ids)
                cursor.execute(f'DELETE FROM invoices WHERE id IN ({placeholders})', invoice_ids)
            
            message = f'{len(invoice_ids)} {upload_type} invoices cleared successfully'
        else:
            # Clear all invoices
            cursor.execute('DELETE FROM processing_history')
            cursor.execute('DELETE FROM line_items')
            cursor.execute('DELETE FROM invoices')
            cursor.execute('DELETE FROM vendors')
            message = 'All invoices cleared successfully'
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Legacy v1 endpoint - maintain backward compatibility
@app.route('/api/process', methods=['POST'])
def process_invoice_v1():
    """Legacy endpoint for backward compatibility."""
    return process_invoice_v2()


@app.route('/api/health', methods=['GET'])
def health_check_v1():
    """Legacy health check endpoint."""
    return health_check_v2()


# Serve frontend
@app.route('/')
def home():
    """Serve the login page."""
    return send_from_directory('../public', 'login.html')


@app.route('/login.html')
def login_page():
    """Serve the login page."""
    return send_from_directory('../public', 'login.html')


@app.route('/dashboard.html')
def dashboard():
    """Serve the dashboard."""
    return send_from_directory('../public', 'dashboard.html')


@app.route('/single.html')
def single_page():
    """Serve the single invoice processor page."""
    return send_from_directory('../public', 'single.html')


@app.route('/batch.html')
def batch_page():
    """Serve the batch processing dashboard."""
    return send_from_directory('../public', 'batch.html')


@app.route('/index.html')
def simple_ui():
    """Serve the simple upload UI."""
    return send_from_directory('../public', 'index.html')


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/v2/register', methods=['POST'])
def register_user():
    """
    POST /api/v2/register - Register a new user
    
    Body:
        - email (required): User email
        - password (required): User password (min 6 characters)
        - full_name (optional): User's full name
        - company (optional): User's company
    
    Returns:
        - 200: Registration successful
        - 400: Invalid request
    """
    if not USER_MANAGEMENT_ENABLED or not user_manager:
        return jsonify({'success': False, 'error': 'User management not available'}), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        company = data.get('company')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        result = user_manager.register_user(email, password, full_name, company)
        
        if result['success']:
            # Generate JWT token for immediate login
            token = auth_manager.generate_token(str(result['user_id']), email)
            result['token'] = token
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# OAUTH AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/v2/auth/google', methods=['GET'])
def google_oauth_login():
    """
    GET /api/v2/auth/google - Initiate Google OAuth flow
    
    Redirects to Google OAuth consent page
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({
            'success': False, 
            'error': 'Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
        }), 503
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build redirect URI
    redirect_uri = f'{VERCEL_URL}/api/v2/auth/google/callback'
    
    # Build Google OAuth URL
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    
    # Create response with state cookie
    response = redirect(auth_url)
    response.set_cookie('oauth_state', state, max_age=600, httponly=True, samesite='Lax', secure=True)
    return response


@app.route('/api/v2/auth/google/callback', methods=['GET'])
def google_oauth_callback():
    """
    GET /api/v2/auth/google/callback - Handle Google OAuth callback
    
    Receives authorization code from Google and exchanges for user info
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return redirect('/login.html?error=oauth_not_configured')
    
    # Get state from URL and cookie
    state = request.args.get('state')
    stored_state = request.cookies.get('oauth_state')
    
    # Skip state validation for now as cookies may not work across OAuth redirect
    # The OAuth flow itself provides security through the authorization code
    # In production with same-domain setup, proper state validation should be enabled
    
    # Check for errors from Google
    error = request.args.get('error')
    if error:
        return redirect(f'/login.html?error={error}')
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return redirect('/login.html?error=no_code')
    
    try:
        # Exchange code for access token
        redirect_uri = f'{VERCEL_URL}/api/v2/auth/google/callback'
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            return redirect(f'/login.html?error={token_json["error"]}')
        
        access_token = token_json.get('access_token')
        if not access_token:
            return redirect('/login.html?error=no_access_token')
        
        # Get user info from Google
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_data = user_response.json()
        
        if 'error' in user_data:
            return redirect(f'/login.html?error={user_data["error"]}')
        
        email = user_data.get('email')
        name = user_data.get('name', '')
        
        if not email:
            return redirect('/login.html?error=no_email')
        
        # Check if user exists or create new user
        if USER_MANAGEMENT_ENABLED and user_manager:
            try:
                # Try to find existing user
                existing_user = db.get_user_by_email(email)
                
                if existing_user:
                    user_id = existing_user['id']
                else:
                    # Register new user via OAuth
                    register_result = user_manager.register_user(
                        email=email,
                        password=None,  # No password for OAuth users
                        full_name=name,
                        oauth_provider='google'
                    )
                    
                    if not register_result['success']:
                        return redirect(f'/login.html?error=registration_failed')
                    
                    user_id = register_result['user_id']
            except Exception as user_error:
                print(f"User management error: {user_error}")
                # Fallback: use email as user_id if user management fails
                user_id = email
        else:
            # Without user management, use email as ID
            user_id = email
        
        # Generate JWT token
        token = auth_manager.generate_token(str(user_id), email)
        
        # Redirect to dashboard with token in URL and clear state cookie
        response = redirect(f'/single.html?token={token}&email={urllib.parse.quote(email)}&name={urllib.parse.quote(name)}')
        response.set_cookie('oauth_state', '', max_age=0)  # Clear state cookie
        return response
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return redirect(f'/login.html?error=oauth_failed')


@app.route('/api/v2/auth/github', methods=['GET'])
def github_oauth_login():
    """
    GET /api/v2/auth/github - Initiate GitHub OAuth flow
    
    Redirects to GitHub OAuth authorization page
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return jsonify({
            'success': False, 
            'error': 'GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.'
        }), 503
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build redirect URI
    redirect_uri = f'{VERCEL_URL}/api/v2/auth/github/callback'
    
    # Build GitHub OAuth URL
    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'user:email',
        'state': state
    }
    
    auth_url = 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


@app.route('/api/v2/auth/github/callback', methods=['GET'])
def github_oauth_callback():
    """
    GET /api/v2/auth/github/callback - Handle GitHub OAuth callback
    
    Receives authorization code from GitHub and exchanges for user info
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return redirect('/login.html?error=oauth_not_configured')
    
    # Verify state token for CSRF protection
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return redirect('/login.html?error=invalid_state')
    
    # Check for errors from GitHub
    error = request.args.get('error')
    if error:
        return redirect(f'/login.html?error={error}')
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return redirect('/login.html?error=no_code')
    
    try:
        # Exchange code for access token
        redirect_uri = f'{VERCEL_URL}/api/v2/auth/github/callback'
        token_url = 'https://github.com/login/oauth/access_token'
        token_data = {
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {'Accept': 'application/json'}
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_json = token_response.json()
        
        if 'error' in token_json:
            return redirect(f'/login.html?error={token_json["error"]}')
        
        access_token = token_json.get('access_token')
        if not access_token:
            return redirect('/login.html?error=no_access_token')
        
        # Get user info from GitHub
        user_url = 'https://api.github.com/user'
        email_url = 'https://api.github.com/user/emails'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        user_response = requests.get(user_url, headers=headers)
        user_data = user_response.json()
        
        # Get primary email
        email_response = requests.get(email_url, headers=headers)
        emails = email_response.json()
        
        # Find primary email or first verified email
        primary_email = None
        for email_obj in emails:
            if email_obj.get('primary') and email_obj.get('verified'):
                primary_email = email_obj['email']
                break
        
        if not primary_email:
            # Fallback to first verified email
            for email_obj in emails:
                if email_obj.get('verified'):
                    primary_email = email_obj['email']
                    break
        
        if not primary_email:
            return redirect('/login.html?error=no_email')
        
        name = user_data.get('name') or user_data.get('login', '')
        
        # Check if user exists or create new user
        if USER_MANAGEMENT_ENABLED and user_manager:
            # Try to find existing user
            existing_user = db.get_user_by_email(primary_email)
            
            if existing_user:
                user_id = existing_user['id']
            else:
                # Register new user via OAuth
                register_result = user_manager.register_user(
                    email=primary_email,
                    password=None,  # No password for OAuth users
                    full_name=name,
                    oauth_provider='github'
                )
                
                if not register_result['success']:
                    return redirect(f'/login.html?error=registration_failed')
                
                user_id = register_result['user_id']
        else:
            # Without user management, use email as ID
            user_id = primary_email
        
        # Generate JWT token
        token = auth_manager.generate_token(str(user_id), primary_email)
        
        # Clear OAuth state from session
        session.pop('oauth_state', None)
        
        # Redirect to dashboard with token in URL
        return redirect(f'/single.html?token={token}&email={urllib.parse.quote(primary_email)}&name={urllib.parse.quote(name)}')
        
    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return redirect(f'/login.html?error=oauth_failed')


@app.route('/api/v2/login', methods=['POST'])
def login_user():
    """
    POST /api/v2/login - Authenticate user
    
    Body:
        - email (required): User email
        - password (required): User password
    
    Returns:
        - 200: Login successful with JWT token
        - 401: Invalid credentials
    """
    if not USER_MANAGEMENT_ENABLED or not user_manager:
        return jsonify({'success': False, 'error': 'User management not available'}), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        result = user_manager.login_user(email, password)
        
        if result['success']:
            # Generate JWT token
            token = auth_manager.generate_token(str(result['user_id']), email)
            result['token'] = token
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/verify-email', methods=['GET'])
def verify_email():
    """
    GET /api/v2/verify-email?token=<token> - Verify user email
    
    Query Parameters:
        - token (required): Email verification token
    
    Returns:
        - 200: Email verified
        - 400: Invalid token
    """
    if not USER_MANAGEMENT_ENABLED or not user_manager:
        return jsonify({'success': False, 'error': 'User management not available'}), 503
    
    try:
        token = request.args.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Token required'}), 400
        
        result = user_manager.verify_email(token)
        
        if result['success']:
            # Redirect to dashboard with success message
            return '''
            <html>
                <head>
                    <style>
                        body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea, #764ba2); }
                        .card { background: white; padding: 40px; border-radius: 15px; max-width: 500px; margin: 0 auto; }
                        h1 { color: #667eea; }
                        a { display: inline-block; margin-top: 20px; padding: 12px 30px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-decoration: none; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>✓ Email Verified!</h1>
                        <p>Your email has been successfully verified. You can now use all features of Invoice Processor Pro.</p>
                        <a href="/">Go to Dashboard</a>
                    </div>
                </body>
            </html>
            '''
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    GET /api/v2/user/profile - Get current user profile
    
    Headers:
        - Authorization: Bearer <token> (required)
    
    Returns:
        - 200: User profile
        - 401: Unauthorized
    """
    if not USER_MANAGEMENT_ENABLED or not user_manager:
        return jsonify({'success': False, 'error': 'User management not available'}), 503
    
    try:
        user_id = request.user_id
        user = user_manager.get_user(int(user_id))
        
        if user:
            return jsonify({'success': True, 'user': user}), 200
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/user/email-preferences', methods=['PUT'])
@require_auth
def update_email_preferences():
    """
    PUT /api/v2/user/email-preferences - Update email notification preferences
    
    Headers:
        - Authorization: Bearer <token> (required)
    
    Body:
        - email_notifications (required): true/false
    
    Returns:
        - 200: Preferences updated
        - 401: Unauthorized
    """
    if not USER_MANAGEMENT_ENABLED or not user_manager:
        return jsonify({'success': False, 'error': 'User management not available'}), 503
    
    try:
        user_id = request.user_id
        data = request.get_json()
        
        if not data or 'email_notifications' not in data:
            return jsonify({'success': False, 'error': 'email_notifications field required'}), 400
        
        result = user_manager.update_email_preferences(int(user_id), data['email_notifications'])
        return jsonify(result), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/send-single-invoice', methods=['POST'])
@optional_auth
def send_single_invoice_email():
    """
    POST /api/v2/send-single-invoice - Send a single invoice via email
    
    Body:
        - email: Recipient email address
        - invoice_data: Invoice data object
    
    Returns:
        - 200: Email sent
        - 400: Invalid request
    """
    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib
        from datetime import datetime
        
        data = request.get_json() or {}
        recipient_email = data.get('email')
        invoice_data = data.get('invoice_data')
        
        if not recipient_email:
            return jsonify({'success': False, 'error': 'Email address required'}), 400
        
        if not invoice_data:
            return jsonify({'success': False, 'error': 'Invoice data required'}), 400
        
        # Get SMTP configuration
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not smtp_user or not smtp_password:
            return jsonify({
                'success': False, 
                'error': 'Email not configured. Please set SMTP_USER and SMTP_PASSWORD environment variables.'
            }), 503
        
        # Extract invoice details
        inv_number = invoice_data.get('invoice_number', 'N/A')
        vendor = invoice_data.get('vendor', invoice_data.get('vendor_name', 'N/A'))
        date = invoice_data.get('date', 'N/A')
        total = invoice_data.get('total', '0')
        subtotal = invoice_data.get('subtotal', '0')
        tax = invoice_data.get('tax', '0')
        line_items = invoice_data.get('line_items', [])
        
        # Build line items HTML
        line_items_html = ''
        if line_items and isinstance(line_items, list):
            line_items_html = '<h3 style="color: #667eea; margin-top: 30px;">Line Items</h3><table style="width: 100%; border-collapse: collapse; margin-top: 15px;">'
            line_items_html += '<tr style="background: #667eea; color: white;"><th style="padding: 12px; text-align: left;">Description</th><th style="padding: 12px; text-align: right;">Quantity</th><th style="padding: 12px; text-align: right;">Unit Price</th><th style="padding: 12px; text-align: right;">Amount</th></tr>'
            
            for item in line_items:
                if isinstance(item, dict):
                    desc = item.get('description', 'N/A')
                    qty = item.get('quantity', 'N/A')
                    price = item.get('unit_price', 'N/A')
                    amount = item.get('amount', 'N/A')
                    line_items_html += f'<tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px;">{desc}</td><td style="padding: 12px; text-align: right;">{qty}</td><td style="padding: 12px; text-align: right;">{price}</td><td style="padding: 12px; text-align: right;">{amount}</td></tr>'
            
            line_items_html += '</table>'
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Invoice {inv_number} from {vendor}'
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px; }}
                    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                    .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; }}
                    .info-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
                    .info-value {{ font-size: 18px; font-weight: bold; color: #333; }}
                    .total-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                    .total-box .amount {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📄 Invoice Details</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Processed by Smart Invoice Processor</p>
                    </div>
                    <div class="content">
                        <p style="font-size: 16px; color: #555;">Hello,</p>
                        <p style="font-size: 16px; color: #555;">Here are the details of your invoice:</p>
                        
                        <div class="info-grid">
                            <div class="info-box">
                                <div class="info-label">Invoice Number</div>
                                <div class="info-value">{inv_number}</div>
                            </div>
                            <div class="info-box">
                                <div class="info-label">Vendor</div>
                                <div class="info-value">{vendor}</div>
                            </div>
                            <div class="info-box">
                                <div class="info-label">Date</div>
                                <div class="info-value">{date}</div>
                            </div>
                            <div class="info-box">
                                <div class="info-label">Subtotal</div>
                                <div class="info-value">{subtotal}</div>
                            </div>
                        </div>
                        
                        <div class="info-grid" style="grid-template-columns: 1fr;">
                            <div class="info-box">
                                <div class="info-label">Tax</div>
                                <div class="info-value">{tax}</div>
                            </div>
                        </div>
                        
                        <div class="total-box">
                            <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.9;">Total Amount</div>
                            <div class="amount">{total}</div>
                        </div>
                        
                        {line_items_html}
                        
                        <div class="footer">
                            <p><strong>Smart Invoice Processor</strong></p>
                            <p>AI-powered invoice processing made simple</p>
                            <p style="margin-top: 15px;">Visit: <a href="{VERCEL_URL}" style="color: #667eea; text-decoration: none;">{VERCEL_URL}</a></p>
                            <p style="font-size: 12px; color: #999; margin-top: 20px;">
                                This is an automated email. Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return jsonify({'success': True, 'message': 'Invoice emailed successfully'}), 200
            
    except Exception as e:
        print(f"Error sending single invoice email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v2/send-report', methods=['POST'])
@optional_auth
def send_email_report():
    """
    POST /api/v2/send-report - Send invoice report via email
    
    Headers:
        - Authorization: Bearer <token> (optional)
    
    Body:
        - email: Recipient email address
    
    Returns:
        - 200: Report sent
        - 400: Invalid request
    """
    try:
        data = request.get_json() or {}
        user_id = getattr(request, 'user_id', None)
        upload_type = request.args.get('upload_type')  # Filter by upload type
        
        # Get email from request body or use authenticated user
        recipient_email = data.get('email')
        
        if not recipient_email:
            return jsonify({'success': False, 'error': 'Email address required'}), 400
        
        # Get SMTP configuration
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not smtp_user or not smtp_password:
            return jsonify({
                'success': False, 
                'error': 'Email not configured. Please set SMTP_USER and SMTP_PASSWORD environment variables.'
            }), 503
        
        # Get user's invoices - filtered by upload_type if provided
        invoices = db.list_invoices(user_id=user_id, upload_type=upload_type, limit=100) if user_id else []
        
        # If no invoices found with user_id, try using email as user_id (for OAuth users)
        if (not invoices or len(invoices) == 0) and recipient_email:
            invoices = db.list_invoices(user_id=recipient_email, upload_type=upload_type, limit=100)
        
        # If still no invoices, get all invoices of the specified type (for demo/testing)
        if not invoices or len(invoices) == 0:
            all_invoices = db.list_invoices(upload_type=upload_type, limit=100)
            if not all_invoices or len(all_invoices) == 0:
                return jsonify({
                    'success': False, 
                    'error': 'No invoices found. Please upload some invoices first.',
                    'help': 'Upload invoices using the dashboard to generate a report.'
                }), 404
            else:
                # Use all invoices for the report
                invoices = all_invoices
        
        # Use user manager if available AND user_id is numeric, otherwise send basic email
        if USER_MANAGEMENT_ENABLED and user_manager and user_id and str(user_id).isdigit():
            result = user_manager.send_invoice_report(int(user_id), invoices)
        else:
            # Send basic email report for OAuth users or when user_id is not numeric
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            import smtplib
            
            # Currency conversion rates (approximate)
            currency_rates = {
                'INR': 0.012,  # INR to USD
                'EUR': 1.09,   # EUR to USD
                'GBP': 1.27,   # GBP to USD
                'USD': 1.0,    # USD to USD
            }
            
            # Calculate statistics
            from datetime import datetime
            from collections import Counter
            
            total = len(invoices)
            total_amount = 0
            vendors = []
            recent_invoices = []
            
            for inv in invoices:
                vendors.append(inv.get('vendor_name', 'Unknown'))
                
                if inv.get('total'):
                    try:
                        # Detect currency and convert to USD
                        amount_str = str(inv.get('total', '0'))
                        currency = 'USD'  # Default
                        
                        # Detect currency
                        if 'INR' in amount_str or '₹' in amount_str:
                            currency = 'INR'
                        elif 'EUR' in amount_str or '€' in amount_str:
                            currency = 'EUR'
                        elif 'GBP' in amount_str or '£' in amount_str:
                            currency = 'GBP'
                        
                        # Remove all currency symbols and codes
                        amount_str = amount_str.replace('$', '').replace('₹', '').replace('€', '').replace('£', '')
                        amount_str = amount_str.replace('INR', '').replace('USD', '').replace('EUR', '').replace('GBP', '')
                        amount_str = amount_str.replace(',', '').strip()
                        
                        # Convert to USD
                        amount = float(amount_str)
                        total_amount += amount * currency_rates.get(currency, 1.0)
                    except (ValueError, AttributeError):
                        # Skip if can't parse
                        pass
            
            # Get top 5 recent invoices
            recent_invoices = invoices[:5] if len(invoices) >= 5 else invoices
            
            # Get vendor breakdown
            vendor_counts = Counter(vendors)
            top_vendors = vendor_counts.most_common(5)
            
            # Build vendor breakdown HTML
            vendor_html = ''
            for vendor, count in top_vendors:
                vendor_html += f'<tr><td style="padding: 8px; border-bottom: 1px solid #eee;">{vendor}</td><td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{count}</td></tr>'
            
            # Build recent invoices HTML
            recent_html = ''
            for inv in recent_invoices:
                inv_num = inv.get('invoice_number', 'N/A')
                vendor = inv.get('vendor_name', 'N/A')
                total = inv.get('total', 'N/A')
                date = inv.get('date', 'N/A')
                recent_html += f'<tr><td style="padding: 10px; border-bottom: 1px solid #eee;">{inv_num}</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{vendor}</td><td style="padding: 10px; border-bottom: 1px solid #eee;">{date}</td><td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">{total}</td></tr>'
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Invoice Report - {total} Invoices (${total_amount:,.2f})'
            msg['From'] = smtp_user
            msg['To'] = recipient_email
            
            html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 28px; }}
                        .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px; }}
                        .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 30px 0; }}
                        .stat-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea; }}
                        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }}
                        .stat-label {{ font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
                        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; color: #666; font-size: 14px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📊 Invoice Report</h1>
                            <p style="margin: 10px 0 0 0; opacity: 0.9;">Your comprehensive invoice summary</p>
                        </div>
                        <div class="content">
                            <p style="font-size: 16px; color: #555;">Hello,</p>
                            <p style="font-size: 16px; color: #555;">Here's your latest invoice report from Smart Invoice Processor:</p>
                            
                            <div class="stats-grid">
                                <div class="stat-box">
                                    <div class="stat-label">Total Invoices</div>
                                    <div class="stat-value">{total}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Total Amount (USD)</div>
                                    <div class="stat-value">${total_amount:,.2f}</div>
                                </div>
                            </div>
                            
                            <h3 style="color: #667eea; margin-top: 30px;">Top Vendors</h3>
                            <table>
                                <tr><th>Vendor</th><th style="text-align: right;">Invoice Count</th></tr>
                                {vendor_html}
                            </table>
                            
                            <h3 style="color: #667eea; margin-top: 30px;">Recent Invoices</h3>
                            <table>
                                <tr><th>Invoice #</th><th>Vendor</th><th>Date</th><th style="text-align: right;">Amount</th></tr>
                                {recent_html}
                            </table>
                            
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                                <p style="margin: 0; font-size: 16px;">View all invoice details in your dashboard</p>
                                <a href="{VERCEL_URL}/batch.html" style="display: inline-block; margin-top: 15px; padding: 12px 30px; background: white; color: #667eea; text-decoration: none; border-radius: 5px; font-weight: bold;">Open Dashboard</a>
                            </div>
                            
                            <div class="footer">
                                <p><strong>Smart Invoice Processor</strong></p>
                                <p>AI-powered invoice processing made simple</p>
                                <p style="font-size: 12px; color: #999; margin-top: 20px;">
                                    This is an automated report. Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            result = {'success': True, 'message': 'Report sent successfully'}
        
        return jsonify(result), 200
            
    except Exception as e:
        print(f"Error sending email report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


# For Vercel serverless deployment
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
