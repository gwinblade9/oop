"""
Просмотр содержимого базы данных SQLite через Python
"""

import sqlite3
import os

def view_database(db_path="data/delivery.db"):
    """Просмотр всех таблиц в базе данных"""
    
    if not os.path.exists(db_path):
        print(f"❌ Файл БД не найден: {db_path}")
        print("   Сначала запустите программу для создания БД: python run.py")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("="*70)
    print("  СОДЕРЖИМОЕ БАЗЫ ДАННЫХ")
    print("="*70)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📋 ТАБЛИЦА: {table_name}")
        print("-"*70)
        
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        # Получаем данные
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Выводим заголовки
        print(" | ".join(col_names))
        print("-"*70)
        
        # Выводим данные
        if rows:
            for row in rows:
                print(" | ".join(str(val) for val in row))
            print(f"\n✅ Всего записей: {len(rows)}")
        else:
            print("   (нет данных)")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ ПРОСМОТР ЗАВЕРШЕН")
    print("="*70)


def run_sql_query(db_path="data/delivery.db", query=""):
    """Выполнение произвольного SQL-запроса"""
    
    if not os.path.exists(db_path):
        print(f"❌ Файл БД не найден: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print("="*70)
        print(f"  РЕЗУЛЬТАТ ЗАПРОСА:")
        print("="*70)
        
        # Получаем названия колонок
        if cursor.description:
            col_names = [desc[0] for desc in cursor.description]
            print(" | ".join(col_names))
            print("-"*70)
            
            for row in rows:
                print(" | ".join(str(val) for val in row))
            
            print(f"\n✅ Найдено записей: {len(rows)}")
        else:
            print("✅ Запрос выполнен успешно")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка SQL: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Проверяем наличие БД
    db_path = "data/delivery.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        print("   Запустите сначала: python run.py")
    else:
        print("\n1️⃣ Просмотр всей БД")
        print("2️⃣ Выполнить свой SQL-запрос")
        print("3️⃣ Показать статистику заказов")
        
        choice = input("\nВыберите действие (1-3): ").strip()
        
        if choice == "1":
            view_database(db_path)
        elif choice == "2":
            query = input("Введите SQL-запрос: ")
            run_sql_query(db_path, query)
        elif choice == "3":
            run_sql_query(db_path, """
                SELECT 
                    u.name as Покупатель,
                    r.name as Ресторан,
                    o.total_price as Сумма,
                    o.status as Статус,
                    o.created_at as Дата
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN restaurants r ON o.restaurant_id = r.id
                ORDER BY o.created_at DESC
            """)
        else:
            print("❌ Неверный выбор")