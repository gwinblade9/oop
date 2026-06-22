"""
Работа с базой данных SQLite
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import threading


class DatabaseManager:
    """Класс для управления базой данных с поддержкой многопоточности"""
    
    def __init__(self, db_path: str = "data/delivery.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._local = threading.local()
    
    def _ensure_db_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _get_connection(self):
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def close(self):
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def close_all(self):
        self.close()
    
    def init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                role TEXT DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT,
                cuisine TEXT,
                rating REAL DEFAULT 0,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category TEXT,
                is_available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                restaurant_id INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                total_price REAL NOT NULL,
                delivery_fee REAL DEFAULT 0,
                delivery_address TEXT NOT NULL,
                delivery_type TEXT DEFAULT 'standard',
                eta_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                price_at_order REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
            CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant_id ON menu_items(restaurant_id);
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
        ''')
        
        conn.commit()
        print("✅ База данных инициализирована")
    
    def insert_test_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("ℹ️ Тестовые данные уже есть")
            return
        
        cursor.executemany('''
            INSERT INTO users (name, email, password_hash, phone, address, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ("Иван Петров", "ivan@mail.ru", "hash123", "+7-999-111-22-33", "ул. Тверская 15", "customer"),
            ("Мария Смирнова", "maria@mail.ru", "hash456", "+7-999-444-55-66", "ул. Арбат 10", "customer"),
            ("Алексей Менеджер", "alex@rest.ru", "hash789", "+7-999-777-88-99", "ул. Пушкина 5", "manager")
        ])
        
        cursor.executemany('''
            INSERT INTO restaurants (name, address, phone, cuisine, rating, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            ("Пиццерия №1", "ул. Ленина 10", "+7-495-111-11-11", "Итальянская", 4.5, 55.7558, 37.6173),
            ("Суши-бар 'Сакура'", "ул. Тверская 25", "+7-495-222-22-22", "Японская", 4.8, 55.7658, 37.6073),
            ("Бургерная 'BBQ'", "ул. Арбат 30", "+7-495-333-33-33", "Американская", 4.3, 55.7458, 37.6273)
        ])
        
        cursor.executemany('''
            INSERT INTO menu_items (restaurant_id, name, description, price, category)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            (1, "Пицца Маргарита", "Томатный соус, моцарелла, базилик", 450, "Пицца"),
            (1, "Пицца Пепперони", "Томатный соус, пепперони, моцарелла", 520, "Пицца"),
            (1, "Паста Карбонара", "Спагетти, бекон, яйцо, пармезан", 380, "Паста"),
            (1, "Лимонад", "Домашний лимонад с мятой", 150, "Напитки"),
            (2, "Филадельфия ролл", "Лосось, сливочный сыр, огурец", 650, "Роллы"),
            (2, "Калифорния ролл", "Краб, авокадо, огурец", 580, "Роллы"),
            (2, "Суши сет 'Сакура'", "6 видов суши", 1200, "Сеты"),
            (2, "Зеленый чай", "Японский зеленый чай", 100, "Напитки"),
            (3, "Чизбургер классический", "Говяжья котлета, сыр, салат", 350, "Бургеры"),
            (3, "Двойной чизбургер", "Двойная котлета, сыр, соус", 480, "Бургеры"),
            (3, "Картошка фри", "Хрустящий картофель", 150, "Гарниры"),
            (3, "Милкшейк", "Ванильный молочный коктейль", 200, "Напитки")
        ])
        
        cursor.executemany('''
            INSERT INTO orders (user_id, restaurant_id, status, total_price, delivery_fee, 
                              delivery_address, delivery_type, eta_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, 1, "delivered", 980, 0, "ул. Тверская 15", "standard", 35, datetime.now().isoformat()),
            (2, 2, "delivering", 1420, 100, "ул. Арбат 10", "express", 25, datetime.now().isoformat())
        ])
        
        cursor.executemany('''
            INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_order)
            VALUES (?, ?, ?, ?)
        ''', [
            (1, 1, 2, 450),
            (1, 3, 1, 380),
            (2, 5, 2, 650),
            (2, 8, 1, 100)
        ])
        
        conn.commit()
        print("✅ Тестовые данные добавлены")
    
    def get_orders_with_details(self, days: int = 7) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                o.id AS order_id,
                u.name AS customer_name,
                u.email AS customer_email,
                u.phone AS customer_phone,
                r.name AS restaurant_name,
                r.cuisine AS restaurant_cuisine,
                o.total_price,
                o.delivery_fee,
                o.status,
                o.created_at,
                o.eta_minutes,
                o.delivery_address
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE o.created_at >= datetime('now', ?)
            ORDER BY o.created_at DESC
        ''', (f'-{days} days',))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_restaurant_statistics(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.id AS restaurant_id,
                r.name AS restaurant_name,
                COUNT(o.id) AS orders_count,
                SUM(o.total_price) AS total_revenue,
                AVG(o.total_price) AS avg_order_value,
                SUM(o.delivery_fee) AS total_delivery_fee
            FROM restaurants r
            LEFT JOIN orders o ON r.id = o.restaurant_id 
                AND o.status != 'cancelled'
                AND o.created_at >= datetime('now', '-30 days')
            GROUP BY r.id, r.name
            ORDER BY total_revenue DESC NULLS LAST
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_high_value_restaurants(self, threshold: float = 1000) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.id AS restaurant_id,
                r.name AS restaurant_name,
                COUNT(o.id) AS orders_count,
                ROUND(AVG(o.total_price), 2) AS avg_order_price,
                ROUND(SUM(o.total_price), 2) AS total_revenue
            FROM restaurants r
            JOIN orders o ON r.id = o.restaurant_id
            WHERE o.status = 'delivered'
                AND o.created_at >= datetime('now', '-30 days')
            GROUP BY r.id, r.name
            HAVING AVG(o.total_price) > ?
            ORDER BY avg_order_price DESC
        ''', (threshold,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_restaurants_without_orders(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.id,
                r.name,
                r.phone,
                r.address,
                r.rating,
                COUNT(o.id) AS orders_count
            FROM restaurants r
            LEFT JOIN orders o ON r.id = o.restaurant_id 
                AND o.created_at >= datetime('now', '-7 days')
            GROUP BY r.id, r.name, r.phone, r.address, r.rating
            HAVING COUNT(o.id) = 0
            ORDER BY r.name
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_order(self, order_data: Dict[str, Any]) -> int:
        """Сохранение заказа в БД"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print(f"💾 Сохранение заказа в БД...")
        print(f"   Данные заказа: user_id={order_data['user_id']}, restaurant_id={order_data['restaurant_id']}")
        print(f"   Позиций для сохранения: {len(order_data.get('items', []))}")
        
        # Сохраняем заказ
        cursor.execute('''
            INSERT INTO orders (
                user_id, restaurant_id, status, total_price, delivery_fee,
                delivery_address, delivery_type, eta_minutes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['user_id'],
            order_data['restaurant_id'],
            order_data['status'],
            order_data['total_price'],
            order_data.get('delivery_fee', 0),
            order_data['delivery_address'],
            order_data.get('delivery_type', 'standard'),
            order_data.get('eta_minutes', 30),
            datetime.now().isoformat()
        ))
        
        order_id = cursor.lastrowid
        print(f"   Создан заказ #{order_id}")
        
        # Сохраняем позиции заказа
        items_count = 0
        for item in order_data.get('items', []):
            try:
                print(f"   Сохранение позиции: item_id={item['item_id']}, quantity={item['quantity']}, price={item['price']}")
                cursor.execute('''
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_order)
                    VALUES (?, ?, ?, ?)
                ''', (
                    order_id,
                    item['item_id'],
                    item['quantity'],
                    item['price']
                ))
                items_count += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка при сохранении позиции: {e}")
        
        conn.commit()
        print(f"   Сохранено {items_count} позиций")
        
        # Проверка: сразу проверяем, что сохранилось
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE order_id = ?", (order_id,))
        db_count = cursor.fetchone()[0]
        print(f"   Проверка: в БД {db_count} позиций для заказа #{order_id}")
        
        return order_id
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        delivered_at = datetime.now().isoformat() if status == "delivered" else None
        
        cursor.execute('''
            UPDATE orders 
            SET status = ?, delivered_at = COALESCE(?, delivered_at)
            WHERE id = ?
        ''', (status, delivered_at, order_id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        
        cursor.execute('''
            SELECT 
                oi.menu_item_id as item_id,
                mi.name,
                oi.price_at_order as price,
                oi.quantity,
                (oi.price_at_order * oi.quantity) as total
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        
        items = cursor.fetchall()
        result['items'] = [dict(item) for item in items] if items else []
        
        return result
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]