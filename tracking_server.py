from flask import Flask, request, send_file, Response
import logging
from history_manager import HistoryManager
import io
from PIL import Image

app = Flask(__name__)
# Suppress Flask CLI logging but keep errors
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

history_manager = HistoryManager()

def create_transparent_pixel():
    img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

PIXEL_DATA = create_transparent_pixel()

@app.route('/track')
def track():
    tracking_id = request.args.get('id')
    print(f"DEBUG: /track called with id={tracking_id}") # Visible in terminal
    
    if tracking_id:
        try:
            history_manager.update_status(tracking_id, read=True)
            print(f"Tracking: Email with ID {tracking_id} was OPENED.")
        except Exception as e:
            print(f"Error updating status: {e}")
    
    resp = Response(PIXEL_DATA, mimetype='image/png')
    # Add headers to prevent caching and allow cross-origin
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def run_server(port=5000):
    print(f"Server starting on port {port}...")
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    run_server()
