#!/usr/bin/env python3
"""
Main Flask app for Render deployment
"""

import os
from real_only_dashboard import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
