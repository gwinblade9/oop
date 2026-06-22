#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Точка входа в приложение
"""

import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()