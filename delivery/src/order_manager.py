"""
Менеджер заказов - связующее звено между моделями и БД
"""

from typing import List, Dict, Any, Optional
from src.models import DeliveryOrder, OrderItem, OrderStatus
from src.database import DatabaseManager


class OrderManager:
    """Класс для управления заказами с интеграцией с БД"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._orders_cache: Dict[int, DeliveryOrder] = {}
        self._order_counter = 1
    
    def create_order_from_db(self, order_id: int) -> Optional[DeliveryOrder]:
        """Создание объекта заказа из данных БД"""
        data = self.db.get_order_by_id(order_id)
        if not data:
            return None
        
        order = DeliveryOrder(
            order_id=data['id'],
            user_id=data['user_id'],
            restaurant_id=data['restaurant_id']
        )
        
        order.db_id = data['id']
        order.status = OrderStatus(data['status'])
        order.address = data['delivery_address']
        order.delivery_type = data.get('delivery_type', 'standard')
        order._delivery_fee = data.get('delivery_fee', 0)
        order._total_price = data['total_price']
        order._eta_minutes = data.get('eta_minutes', 0)
        
        for item_data in data.get('items', []):
            item = OrderItem(
                item_id=item_data['item_id'],
                name=item_data['name'],
                price=item_data['price'],
                quantity=item_data['quantity']
            )
            order.add_item(item)
        
        self._orders_cache[order.order_id] = order
        return order
    
    def create_order(self, user_id: int, restaurant_id: int,
                    items: List[Dict], address: str,
                    delivery_type: str = "standard") -> DeliveryOrder:
        if not items:
            raise ValueError("Заказ не может быть пустым")
        if delivery_type not in ["standard", "express"]:
            raise ValueError("Некорректный тип доставки")
        
        print(f"📦 Создание заказа...")
        
        order = DeliveryOrder(self._order_counter, user_id, restaurant_id)
        self._order_counter += 1
        
        for item_data in items:
            item = OrderItem(
                item_id=item_data.get("item_id", 0),
                name=item_data.get("name", ""),
                price=float(item_data.get("price", 0)),
                quantity=int(item_data.get("quantity", 1))
            )
            order.add_item(item)
            print(f"   Добавлена позиция: {item.name} x{item.quantity}")
        
        order.address = address
        order.delivery_type = delivery_type
        order.calculate_total()
        order.calculate_eta()
        
        print(f"   Итоговая сумма: {order.total_price}")
        print(f"   ETA: {order.eta_minutes} мин.")
        
        order_data = {
            'user_id': user_id,
            'restaurant_id': restaurant_id,
            'status': order.status.value,
            'total_price': order.total_price,
            'delivery_fee': order.delivery_fee,
            'delivery_address': address,
            'delivery_type': delivery_type,
            'eta_minutes': order.eta_minutes,
            'items': [
                {
                    'item_id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'quantity': item.quantity
                }
                for item in order.get_items()
            ]
        }
        
        db_id = self.db.save_order(order_data)
        order.db_id = db_id
        self._orders_cache[order.order_id] = order
        
        print(f"✅ Заказ #{order.order_id} создан, позиций: {len(order.get_items())}")
        
        return order
    
    def update_status(self, order_id: int, status: OrderStatus) -> bool:
        order = self._orders_cache.get(order_id)
        if not order:
            order = self.create_order_from_db(order_id)
            if not order:
                raise ValueError(f"Заказ #{order_id} не найден")
        
        order.status = status
        result = self.db.update_order_status(order.db_id, status.value)
        return result
    
    def get_order(self, order_id: int) -> Optional[DeliveryOrder]:
        if order_id in self._orders_cache:
            return self._orders_cache[order_id]
        return self.create_order_from_db(order_id)
    
    def get_order_info(self, order_id: int) -> Optional[Dict[str, Any]]:
        order = self.get_order(order_id)
        if order:
            order_dict = order.to_dict()
            if 'items' in order_dict:
                if not isinstance(order_dict['items'], list):
                    order_dict['items'] = []
            else:
                order_dict['items'] = []
            if hasattr(order_dict['items'], '__call__'):
                order_dict['items'] = []
            return order_dict
        return None
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        return self.db.get_all_orders()
    
    def get_orders_with_details(self, days: int = 7) -> List[Dict[str, Any]]:
        return self.db.get_orders_with_details(days)
    
    def get_restaurant_statistics(self) -> List[Dict[str, Any]]:
        return self.db.get_restaurant_statistics()
    
    def get_high_value_restaurants(self, threshold: float = 1000) -> List[Dict[str, Any]]:
        return self.db.get_high_value_restaurants(threshold)
    
    def get_restaurants_without_orders(self) -> List[Dict[str, Any]]:
        return self.db.get_restaurants_without_orders()
    
    def clear_cache(self):
        self._orders_cache.clear()
    
    def get_cached_orders_count(self) -> int:
        return len(self._orders_cache)