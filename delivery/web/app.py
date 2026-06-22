import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS

from src.database import DatabaseManager
from src.order_manager import OrderManager
from src.models import OrderStatus

app = Flask(__name__)
app.secret_key = 'delivery_secret_key_2024'
CORS(app)

db = DatabaseManager("data/delivery.db")
db.init_database()
db.insert_test_data()
manager = OrderManager(db)

STATUS_RU = {
    'new': 'Новый',
    'accepted': 'Принят',
    'preparing': 'Готовится',
    'ready': 'Готов',
    'delivering': 'В пути',
    'delivered': 'Доставлен',
    'cancelled': 'Отменён'
}

STATUS_COLORS = {
    'new': '#007bff',
    'accepted': '#17a2b8',
    'preparing': '#ffc107',
    'ready': '#28a745',
    'delivering': '#fd7e14',
    'delivered': '#6c757d',
    'cancelled': '#dc3545'
}


@app.teardown_appcontext
def close_db(error):
    db.close()


@app.route('/')
def index():
    all_orders = manager.get_all_orders()
    delivered_count = len([o for o in all_orders if o['status'] == 'delivered'])
    cancelled_count = len([o for o in all_orders if o['status'] == 'cancelled'])
    active_orders = len([o for o in all_orders if o['status'] not in ['delivered', 'cancelled']])
    
    return render_template('index.html',
                          orders=all_orders,
                          delivered_count=delivered_count,
                          cancelled_count=cancelled_count,
                          active_orders=active_orders,
                          status_ru=STATUS_RU,
                          status_colors=STATUS_COLORS)


@app.route('/orders')
def orders_list():
    all_orders = manager.get_all_orders()
    
    for order in all_orders:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM users WHERE id = ?", (order['user_id'],))
        user_row = cursor.fetchone()
        order['user_name'] = user_row[0] if user_row else 'Неизвестно'
        
        cursor.execute("SELECT name FROM restaurants WHERE id = ?", (order['restaurant_id'],))
        rest_row = cursor.fetchone()
        order['restaurant_name'] = rest_row[0] if rest_row else 'Неизвестно'
    
    return render_template('orders.html',
                          orders=all_orders,
                          status_ru=STATUS_RU,
                          status_colors=STATUS_COLORS)


@app.route('/order/<int:order_id>')
def order_detail(order_id):
    try:
        print(f"📋 Загрузка деталей заказа #{order_id}")
        
        # Получаем заказ через менеджер
        order_data = manager.get_order_info(order_id)
        
        if not order_data:
            flash('Заказ не найден', 'danger')
            return redirect(url_for('orders_list'))
        
        print(f"   Статус: {order_data.get('status')}")
        print(f"   Сумма: {order_data.get('total_price')}")
        print(f"   Позиций в данных: {len(order_data.get('items', []))}")
        
        # Если позиции пустые, пробуем загрузить напрямую из БД
        if len(order_data.get('items', [])) == 0:
            print("   ⚠️ Позиции пустые, пробуем загрузить из БД напрямую...")
            db_order = db.get_order_by_id(order_id)
            if db_order and db_order.get('items'):
                order_data['items'] = db_order['items']
                print(f"   ✅ Загружено {len(order_data['items'])} позиций из БД")
        
        # Получаем данные пользователя и ресторана
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM users WHERE id = ?", (order_data['user_id'],))
        user_row = cursor.fetchone()
        order_data['user_name'] = user_row[0] if user_row else 'Неизвестно'
        
        cursor.execute("SELECT name FROM restaurants WHERE id = ?", (order_data['restaurant_id'],))
        rest_row = cursor.fetchone()
        order_data['restaurant_name'] = rest_row[0] if rest_row else 'Неизвестно'
        
        # Убеждаемся, что items - это список
        if 'items' not in order_data or not isinstance(order_data['items'], list):
            order_data['items'] = []
        
        print(f"   Итоговое количество позиций: {len(order_data['items'])}")
        
        return render_template('order_detail.html',
                              order=order_data,
                              status_ru=STATUS_RU,
                              status_colors=STATUS_COLORS)
    
    except Exception as e:
        print(f"❌ Ошибка в order_detail: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка при загрузке заказа: {str(e)}', 'danger')
        return redirect(url_for('orders_list'))


@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        try:
            user_id = int(request.form.get('user_id', 1))
            restaurant_id = int(request.form.get('restaurant_id', 1))
            address = request.form.get('address', '')
            delivery_type = request.form.get('delivery_type', 'standard')
            
            # Собираем позиции заказа
            items = []
            item_ids = request.form.getlist('item_id[]')
            quantities = request.form.getlist('quantity[]')
            names = request.form.getlist('item_name[]')
            prices = request.form.getlist('item_price[]')
            
            print(f"📝 Создание заказа: user_id={user_id}, restaurant_id={restaurant_id}")
            print(f"   item_ids: {item_ids}")
            print(f"   quantities: {quantities}")
            
            for i in range(len(item_ids)):
                qty = int(quantities[i]) if quantities[i] else 0
                if qty > 0:
                    items.append({
                        'item_id': int(item_ids[i]),
                        'name': names[i],
                        'price': float(prices[i]),
                        'quantity': qty
                    })
                    print(f"   Позиция: {names[i]} x{qty}")
            
            if not items:
                flash('Добавьте хотя бы одну позицию в заказ', 'danger')
                return redirect(url_for('create_order'))
            
            # Создаем заказ
            order = manager.create_order(
                user_id=user_id,
                restaurant_id=restaurant_id,
                items=items,
                address=address,
                delivery_type=delivery_type
            )
            
            print(f"✅ Заказ #{order.order_id} создан")
            print(f"   Позиций в заказе: {len(order.get_items())}")
            
            # Проверка: сразу получаем заказ из БД для проверки
            check_order = manager.get_order_info(order.order_id)
            if check_order:
                items_count = len(check_order.get('items', []))
                print(f"   Проверка БД: найдено {items_count} позиций")
                if items_count == 0:
                    print("⚠️ ВНИМАНИЕ: Позиции не сохранились в БД!")
            
            flash(f'Заказ #{order.order_id} успешно создан!', 'success')
            return redirect(url_for('order_detail', order_id=order.order_id))
            
        except Exception as e:
            print(f"❌ Ошибка при создании заказа: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Ошибка: {str(e)}', 'danger')
            return redirect(url_for('create_order'))
    
    # GET запрос - показываем форму
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM users WHERE role = 'customer'")
    users = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM restaurants")
    restaurants = cursor.fetchall()
    
    cursor.execute("SELECT id, name, price FROM menu_items WHERE restaurant_id = 1 AND is_available = 1")
    menu_items = cursor.fetchall()
    
    return render_template('create_order.html',
                          users=users,
                          restaurants=restaurants,
                          menu_items=menu_items,
                          status_ru=STATUS_RU)


@app.route('/api/menu/<int:restaurant_id>')
def get_menu(restaurant_id):
    """API для получения меню ресторана"""
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, price FROM menu_items WHERE restaurant_id = ? AND is_available = 1",
            (restaurant_id,)
        )
        items = cursor.fetchall()
        
        result = [{
            'id': item[0],
            'name': item[1],
            'price': item[2]
        } for item in items]
        
        print(f"📋 Меню для ресторана {restaurant_id}: {len(result)} позиций")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Ошибка получения меню: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        order_id = int(data.get('order_id'))
        status = data.get('status')
        
        order_info = manager.get_order_info(order_id)
        if not order_info:
            return jsonify({
                'success': False,
                'message': f'Заказ #{order_id} не найден'
            }), 404
        
        current_status = order_info.get('status')
        
        if current_status == status:
            return jsonify({
                'success': True,
                'message': f'Статус уже установлен как {STATUS_RU[status]}',
                'status': status,
                'status_ru': STATUS_RU[status],
                'color': STATUS_COLORS[status],
                'no_change': True
            })
        
        valid_transitions = {
            'new': ['accepted', 'cancelled'],
            'accepted': ['preparing', 'cancelled'],
            'preparing': ['ready', 'cancelled'],
            'ready': ['delivering'],
            'delivering': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        if status not in valid_transitions.get(current_status, []):
            return jsonify({
                'success': False,
                'message': f'Невозможно перейти из статуса "{STATUS_RU[current_status]}" в "{STATUS_RU[status]}"'
            }), 400
        
        status_enum = OrderStatus(status)
        manager.update_status(order_id, status_enum)
        
        return jsonify({
            'success': True,
            'message': f'Статус обновлен на {STATUS_RU[status]}',
            'status': status,
            'status_ru': STATUS_RU[status],
            'color': STATUS_COLORS[status]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@app.route('/analytics')
def analytics():
    orders_details = manager.get_orders_with_details(30)
    restaurant_stats = manager.get_restaurant_statistics()
    high_value = manager.get_high_value_restaurants(1000)
    without_orders = manager.get_restaurants_without_orders()
    
    all_orders = manager.get_all_orders()
    total_orders = len(all_orders)
    delivered_orders = len([o for o in all_orders if o['status'] == 'delivered'])
    cancelled_orders = len([o for o in all_orders if o['status'] == 'cancelled'])
    
    total_delivery_time = 0
    delivered_count = 0
    for order in all_orders:
        if order['status'] == 'delivered' and order.get('eta_minutes'):
            total_delivery_time += order['eta_minutes']
            delivered_count += 1
    
    avg_delivery_time = total_delivery_time / delivered_count if delivered_count > 0 else 0
    cancel_percent = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
    total_revenue = sum(o['total_price'] for o in all_orders if o['status'] != 'cancelled')
    
    return render_template('analytics.html',
                          orders_details=orders_details,
                          restaurant_stats=restaurant_stats,
                          high_value=high_value,
                          without_orders=without_orders,
                          total_orders=total_orders,
                          delivered_orders=delivered_orders,
                          cancelled_orders=cancelled_orders,
                          avg_delivery_time=round(avg_delivery_time, 1),
                          cancel_percent=round(cancel_percent, 1),
                          total_revenue=round(total_revenue, 2),
                          status_ru=STATUS_RU,
                          status_colors=STATUS_COLORS)


@app.route('/api/orders')
def api_orders():
    orders = manager.get_all_orders()
    return jsonify(orders)


@app.route('/api/order/<int:order_id>')
def api_order(order_id):
    order = manager.get_order_info(order_id)
    if order:
        return jsonify(order)
    return jsonify({'error': 'Order not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)