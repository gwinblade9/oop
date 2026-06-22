#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import app

if __name__ == '__main__':
    print("="*60)
    print("  🚀 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("="*60)
    print(f"  🌐 Адрес: http://127.0.0.1:5000")
    print("="*60)
    print("  Нажмите Ctrl+C для остановки")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)