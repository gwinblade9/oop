"""
Модели данных для системы доставки еды
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import math


class OrderStatus(Enum):
    """Статусы заказа"""
    NEW = "new"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem:
    """Позиция заказа"""
    
    def __init__(self, item_id: int, name: str, price: float, quantity: int):
        self.id = item_id
        self.name = name
        self.price = price
        self.quantity = quantity
    
    @property
    def total(self) -> float:
        """Общая стоимость позиции"""
        return round(self.price * self.quantity, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование позиции в словарь"""
        return {
            "item_id": self.id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "total": self.total
        }


class DeliveryOrder:
    """Класс заказа с инкапсуляцией данных"""
    
    def __init__(self, order_id: int, user_id: int, restaurant_id: int):
        self._order_id = order_id
        self._user_id = user_id
        self._restaurant_id = restaurant_id
        self._items: List[OrderItem] = []
        self._status = OrderStatus.NEW
        self._address = ""
        self._delivery_type = "standard"
        self._total_price = 0.0
        self._eta_minutes = 0
        self._created_at = datetime.now()
        self._delivery_fee = 0.0
        self._db_id = None
    
    @property
    def order_id(self) -> int:
        return self._order_id
    
    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def restaurant_id(self) -> int:
        return self._restaurant_id
    
    @property
    def status(self) -> OrderStatus:
        return self._status
    
    @status.setter
    def status(self, new_status: OrderStatus):
        if not isinstance(new_status, OrderStatus):
            raise ValueError("Некорректный статус заказа")
        
        if new_status == self._status:
            return
        
        valid_transitions = {
            OrderStatus.NEW: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.DELIVERING],
            OrderStatus.DELIVERING: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: []
        }
        
        if new_status not in valid_transitions.get(self._status, []):
            raise ValueError(
                f"Недопустимый переход статуса: {self._status.value} -> {new_status.value}"
            )
        
        self._status = new_status
    
    @property
    def total_price(self) -> float:
        return round(self._total_price, 2)
    
    @property
    def eta_minutes(self) -> int:
        return self._eta_minutes
    
    @property
    def address(self) -> str:
        return self._address
    
    @address.setter
    def address(self, value: str):
        if not value or not value.strip():
            raise ValueError("Адрес не может быть пустым")
        self._address = value.strip()
    
    @property
    def delivery_type(self) -> str:
        return self._delivery_type
    
    @delivery_type.setter
    def delivery_type(self, value: str):
        if value not in ["standard", "express"]:
            raise ValueError("Некорректный тип доставки")
        self._delivery_type = value
    
    @property
    def delivery_fee(self) -> float:
        return self._delivery_fee
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def db_id(self) -> Optional[int]:
        return self._db_id
    
    @db_id.setter
    def db_id(self, value: int):
        self._db_id = value
    
    def add_item(self, item: OrderItem):
        if item.quantity <= 0:
            raise ValueError("Количество должно быть больше 0")
        if item.price < 0:
            raise ValueError("Цена не может быть отрицательной")
        
        for existing in self._items:
            if existing.id == item.id:
                existing.quantity += item.quantity
                return
        
        self._items.append(item)
    
    def remove_item(self, item_id: int):
        self._items = [item for item in self._items if item.id != item_id]
    
    def clear_items(self):
        self._items.clear()
    
    def get_items(self) -> List[OrderItem]:
        return self._items.copy()
    
    def get_items_count(self) -> int:
        return len(self._items)
    
    def get_total_quantity(self) -> int:
        return sum(item.quantity for item in self._items)
    
    def calculate_total(self, delivery_fee_base: float = 100.0,
                        express_fee: float = 200.0,
                        discount_threshold: float = 1500.0,
                        discount_rate: float = 0.1) -> float:
        if not self._items:
            raise ValueError("Заказ пуст")
        
        subtotal = sum(item.total for item in self._items)
        
        if self._delivery_type == "express":
            self._delivery_fee = express_fee
        else:
            self._delivery_fee = 0 if subtotal >= 1000 else delivery_fee_base
        
        discount = subtotal * discount_rate if subtotal > discount_threshold else 0
        
        self._total_price = subtotal + self._delivery_fee - discount
        return round(self._total_price, 2)
    
    def calculate_eta(self, restaurant_lat: float = 55.7558,
                      restaurant_lon: float = 37.6173,
                      user_lat: float = 55.7717,
                      user_lon: float = 37.6009,
                      base_time: int = 30) -> int:
        R = 6371
        
        lat1, lon1 = math.radians(restaurant_lat), math.radians(restaurant_lon)
        lat2, lon2 = math.radians(user_lat), math.radians(user_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2 * R * math.asin(math.sqrt(a))
        
        travel_time = distance * 5 + 10
        
        current_hour = datetime.now().hour
        is_rush_hour = (12 <= current_hour <= 14) or (19 <= current_hour <= 21)
        rush_penalty = 1.5 if is_rush_hour else 1.0
        
        self._eta_minutes = int((base_time + travel_time) * rush_penalty)
        return self._eta_minutes
    
    def get_subtotal(self) -> float:
        return round(sum(item.total for item in self._items), 2)
    
    def _get_status_ru(self) -> str:
        status_map = {
            OrderStatus.NEW: "Новый",
            OrderStatus.ACCEPTED: "Принят",
            OrderStatus.PREPARING: "Готовится",
            OrderStatus.READY: "Готов",
            OrderStatus.DELIVERING: "В пути",
            OrderStatus.DELIVERED: "Доставлен",
            OrderStatus.CANCELLED: "Отменён"
        }
        return status_map.get(self._status, str(self._status.value))
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование заказа в словарь для JSON/шаблонов"""
        items_list = []
        try:
            for item in self._items:
                items_list.append({
                    "item_id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "total": item.total
                })
        except Exception as e:
            print(f"⚠️ Ошибка при формировании списка items: {e}")
            items_list = []
        
        return {
            "order_id": self._order_id,
            "user_id": self._user_id,
            "restaurant_id": self._restaurant_id,
            "status": self._status.value,
            "status_ru": self._get_status_ru(),
            "items": items_list,
            "total_price": self.total_price,
            "subtotal": self.get_subtotal(),
            "eta_minutes": self._eta_minutes,
            "delivery_fee": self._delivery_fee,
            "delivery_type": self._delivery_type,
            "address": self._address,
            "created_at": self._created_at.isoformat(),
            "created_at_formatted": self._created_at.strftime("%d.%m.%Y %H:%M"),
            "db_id": self._db_id,
            "items_count": len(items_list),
            "total_quantity": self.get_total_quantity()
        }
    
    def __str__(self) -> str:
        return f"Заказ #{self._order_id} | Статус: {self._get_status_ru()} | Сумма: {self.total_price} руб."
    
    def is_active(self) -> bool:
        return self._status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]