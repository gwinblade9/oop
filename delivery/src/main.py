"""
Главный файл с демонстрацией работы системы
"""

import json
from src.database import DatabaseManager
from src.order_manager import OrderManager
from src.models import OrderStatus


def print_section(title: str):
    """Печать разделителя"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_order(order_dict: dict):
    """Красивый вывод заказа"""
    print(f"\n📦 Заказ #{order_dict['order_id']}")
    print(f"   👤 Пользователь: {order_dict['user_id']}")
    print(f"   🏠 Ресторан: {order_dict['restaurant_id']}")
    print(f"   📊 Статус: {order_dict['status']}")
    print(f"   💰 Стоимость: {order_dict['total_price']} руб.")
    print(f"   🚚 Доставка: {order_dict['delivery_fee']} руб.")
    print(f"   ⏱️  ETA: {order_dict['eta_minutes']} мин.")
    print(f"   📍 Адрес: {order_dict['address']}")
    print(f"   🍽️ Позиции:")
    for item in order_dict['items']:
        print(f"      - {item['name']} x{item['quantity']} = {item['total']} руб.")


def main():
    """Основная функция"""
    print_section("СИСТЕМА УПРАВЛЕНИЯ ДОСТАВКОЙ ЕДЫ")
    
    print("\n📀 Инициализация базы данных...")
    db = DatabaseManager("data/delivery.db")
    db.init_database()
    db.insert_test_data()
    
    manager = OrderManager(db)
    
    print_section("СОЗДАНИЕ НОВОГО ЗАКАЗА")
    
    items = [
        {"item_id": 1, "name": "Пицца Маргарита", "price": 450, "quantity": 2},
        {"item_id": 3, "name": "Паста Карбонара", "price": 380, "quantity": 1},
        {"item_id": 4, "name": "Лимонад", "price": 150, "quantity": 2}
    ]
    
    try:
        order = manager.create_order(
            user_id=1,
            restaurant_id=1,
            items=items,
            address="ул. Тверская, д. 15",
            delivery_type="standard"
        )
        
        print(f"\n✅ ЗАКАЗ #{order.order_id} УСПЕШНО СОЗДАН!")
        print_order(order.to_dict())
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании заказа: {e}")
    
    print_section("ОБНОВЛЕНИЕ СТАТУСА ЗАКАЗА")
    
    try:
        order_id = 1
        print(f"\n🔄 Обновление статуса заказа #{order_id}:")
        
        statuses = [
            (OrderStatus.ACCEPTED, "📌 Принят"),
            (OrderStatus.PREPARING, "👨‍🍳 Готовится"),
            (OrderStatus.READY, "✅ Готов"),
            (OrderStatus.DELIVERING, "🛵 В пути"),
            (OrderStatus.DELIVERED, "🎉 Доставлен!")
        ]
        
        for status, label in statuses:
            manager.update_status(order_id, status)
            print(f"   {label} → статус: {status.value}")
        
        # Проверка валидации
        print("\n⚠️ Проверка валидации (попытка некорректного перехода):")
        try:
            manager.update_status(order_id, OrderStatus.NEW)
        except ValueError as e:
            print(f"   ❌ Ошибка: {e}")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print_section("ИНФОРМАЦИЯ О ЗАКАЗЕ")
    
    order_info = manager.get_order_info(1)
    if order_info:
        print_order(order_info)
    
    print_section("АНАЛИТИЧЕСКИЕ ДАННЫЕ")
    
    print("\n📊 1. Заказы с деталями пользователей и ресторанов:")
    orders = manager.get_orders_with_details(30)
    for o in orders[:3]:  # Показываем первые 3
        print(f"   Заказ #{o['order_id']}: {o['customer_name']} → {o['restaurant_name']} ({o['status']}) - {o['total_price']} руб.")
    
    print("\n📊 2. Статистика по ресторанам:")
    stats = manager.get_restaurant_statistics()
    for s in stats:
        print(f"   {s['restaurant_name']}: {s['orders_count'] or 0} заказов, {s['total_revenue'] or 0} руб. выручки")
    
    print("\n📊 3. Рестораны со средним чеком > 1000 руб.:")
    high_value = manager.get_high_value_restaurants(1000)
    for h in high_value:
        print(f"   {h['restaurant_name']}: средний чек {h['avg_order_price']} руб. ({h['orders_count']} заказов)")
    
    print("\n📊 4. Рестораны без заказов за последние 7 дней:")
    without = manager.get_restaurants_without_orders()
    for w in without:
        print(f"   {w['name']} - {w['address']}")
    
    print_section("ВСЕ ЗАКАЗЫ В СИСТЕМЕ")
    all_orders = manager.get_all_orders()
    for o in all_orders:
        print(f"   Заказ #{o['id']}: статус {o['status']}, сумма {o['total_price']} руб.")
    
    db.close()
    
    print("\n" + "="*70)
    print("✅ РАБОТА СИСТЕМЫ ЗАВЕРШЕНА")
    print("="*70)


if __name__ == "__main__":
    main()