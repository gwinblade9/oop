
import sqlite3
import os
import sys

# Добавляем путь к src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager


def clear_database_via_manager():

    print("\n" + "="*60)
    print("  🗑️ ОЧИСТКА БАЗЫ ДАННЫХ (через DatabaseManager)")
    print("="*60)
    
    db = DatabaseManager("data/delivery.db")
    
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    items_count = cursor.fetchone()[0]
    
    print(f"\n📊 Текущее состояние БД:")
    print(f"   Заказов: {orders_count}")
    print(f"   Позиций заказов: {items_count}")
    
    if orders_count == 0 and items_count == 0:
        print("\nℹ️ База данных уже пуста!")
        db.close()
        return
    
    # Подтверждение
    print(f"\n⚠️ Вы собираетесь удалить ВСЕ данные!")
    confirm = input("Вы уверены? (да/нет): ").strip().lower()
    
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        db.close()
        return
    
    try:
        # Удаляем данные
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM menu_items")
        cursor.execute("DELETE FROM restaurants")
        cursor.execute("DELETE FROM users WHERE role = 'customer'")
        
        # Сбрасываем счетчики
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='order_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='restaurants'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        
        conn.commit()
        
        print(f"\n✅ База данных очищена!")
        print(f"   Удалено заказов: {orders_count}")
        print(f"   Удалено позиций: {items_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()


def clear_database_sqlite():
    """Очистка через прямое подключение к SQLite"""
    print("\n" + "="*60)
    print("  🗑️ ОЧИСТКА БАЗЫ ДАННЫХ (через SQLite)")
    print("="*60)
    
    db_path = "data/delivery.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем количество данных
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    items_count = cursor.fetchone()[0]
    
    print(f"\n📊 Текущее состояние БД:")
    print(f"   Заказов: {orders_count}")
    print(f"   Позиций заказов: {items_count}")
    
    if orders_count == 0 and items_count == 0:
        print("\nℹ️ База данных уже пуста!")
        conn.close()
        return
    
    # Подтверждение
    print(f"\n⚠️ Вы собираетесь удалить ВСЕ данные!")
    confirm = input("Вы уверены? (да/нет): ").strip().lower()
    
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        conn.close()
        return
    
    try:
        # Отключаем проверку внешних ключей для быстрого удаления
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Очищаем таблицы
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM menu_items")
        cursor.execute("DELETE FROM restaurants")
        cursor.execute("DELETE FROM users WHERE role = 'customer'")
        
        # Сбрасываем счетчики
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='order_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='restaurants'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        
        # Включаем проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        
        print(f"\n✅ База данных очищена!")
        print(f"   Удалено заказов: {orders_count}")
        print(f"   Удалено позиций: {items_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


def clear_orders_only():
    """Очистка только заказов (без удаления ресторанов и меню)"""
    print("\n" + "="*60)
    print("  🗑️ ОЧИСТКА ЗАКАЗОВ (сохранение ресторанов и меню)")
    print("="*60)
    
    db_path = "data/delivery.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    items_count = cursor.fetchone()[0]
    
    print(f"\n📊 Текущее состояние БД:")
    print(f"   Заказов: {orders_count}")
    print(f"   Позиций заказов: {items_count}")
    
    if orders_count == 0:
        print("\nℹ️ Заказов нет!")
        conn.close()
        return
    
    confirm = input(f"\n⚠️ Удалить {orders_count} заказов? (да/нет): ").strip().lower()
    
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        conn.close()
        return
    
    try:
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='order_items'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
        
        conn.commit()
        
        print(f"\n✅ Удалено {orders_count} заказов и {items_count} позиций!")
        print("   Рестораны и меню сохранены.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


def clear_orders_by_status():
    """Удаление заказов по статусу"""
    print("\n" + "="*60)
    print("  🗑️ УДАЛЕНИЕ ЗАКАЗОВ ПО СТАТУСУ")
    print("="*60)
    
    db_path = "data/delivery.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Показываем доступные статусы
    cursor.execute("SELECT DISTINCT status, COUNT(*) FROM orders GROUP BY status")
    statuses = cursor.fetchall()
    
    print("\n📊 Заказы по статусам:")
    for status, count in statuses:
        status_ru = {
            'new': 'Новый',
            'accepted': 'Принят',
            'preparing': 'Готовится',
            'ready': 'Готов',
            'delivering': 'В пути',
            'delivered': 'Доставлен',
            'cancelled': 'Отменён'
        }.get(status, status)
        print(f"   {status_ru} ({status}): {count} заказов")
    
    status = input("\nВведите статус для удаления: ").strip().lower()
    
    # Проверяем, есть ли заказы с таким статусом
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = ?", (status,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"❌ Заказов со статусом '{status}' не найдено")
        conn.close()
        return
    
    confirm = input(f"\n⚠️ Удалить {count} заказов со статусом '{status}'? (да/нет): ").strip().lower()
    
    if confirm not in ['да', 'yes', 'y', 'д']:
        print("❌ Операция отменена")
        conn.close()
        return
    
    try:
        cursor.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE status = ?)", (status,))
        cursor.execute("DELETE FROM orders WHERE status = ?", (status,))
        conn.commit()
        
        print(f"\n✅ Удалено {count} заказов со статусом '{status}'!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


def reset_and_recreate():
    """Полный сброс БД (удаление и создание заново)"""
    print("\n" + "="*60)
    print("  🔄 ПОЛНЫЙ СБРОС БАЗЫ ДАННЫХ")
    print("="*60)
    
    db_path = "data/delivery.db"
    
    if os.path.exists(db_path):
        confirm = input("\n⚠️ Удалить файл БД и создать заново? (да/нет): ").strip().lower()
        
        if confirm not in ['да', 'yes', 'y', 'д']:
            print("❌ Операция отменена")
            return
        
        try:
            os.remove(db_path)
            print(f"✅ Файл БД удален: {db_path}")
        except Exception as e:
            print(f"❌ Ошибка при удалении: {e}")
            return
    
    # Создаем новую БД с тестовыми данными
    print("\n📀 Создание новой базы данных...")
    db = DatabaseManager(db_path)
    db.init_database()
    db.insert_test_data()
    db.close()
    
    print("\n✅ База данных создана заново с тестовыми данными!")


def show_menu():
    """Главное меню"""
    print("\n" + "="*60)
    print("  🗑️ ОЧИСТКА БАЗЫ ДАННЫХ")
    print("="*60)
    print("\nВыберите действие:")
    print("1. Полная очистка БД (через DatabaseManager)")
    print("2. Полная очистка БД (через SQLite)")
    print("3. Очистка только заказов")
    print("4. Удаление заказов по статусу")
    print("5. Полный сброс БД (удалить и создать заново)")
    print("6. Выйти")
    
    choice = input("\nВаш выбор (1-6): ").strip()
    
    if choice == "1":
        clear_database_via_manager()
    elif choice == "2":
        clear_database_sqlite()
    elif choice == "3":
        clear_orders_only()
    elif choice == "4":
        clear_orders_by_status()
    elif choice == "5":
        reset_and_recreate()
    elif choice == "6":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    show_menu()