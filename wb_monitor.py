import requests
import time
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WildberriesMonitor:
    def __init__(self, telegram_bot_token, telegram_chat_id):
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def send_telegram_message(self, message):
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            logging.info("Сообщение отправлено в Telegram")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False
    
    def test_telegram_connection(self):
        test_message = "🤖 Бот запущен на сервере Render!\n\nМониторинг скидок на Wildberries активирован 24/7."
        return self.send_telegram_message(test_message)
    
    def search_discounted_products(self):
        try:
            search_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
            params = {
                'appType': 1,
                'couponsGeo': '12,3,18,15,21',
                'curr': 'rub',
                'dest': '-1257786',
                'query': 'скидка распродажа',
                'resultset': 'catalog',
                'sort': 'pricedown',
                'spp': 30,
                'page': 1
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('data', {}).get('products', [])
            
            found_deals = []
            
            for product in products[:100]:
                try:
                    product_id = product.get('id')
                    current_price = product.get('salePriceU', 0) / 100
                    original_price = product.get('priceU', 0) / 100
                    
                    if original_price == 0 or current_price == 0:
                        continue
                    
                    discount_percent = ((original_price - current_price) / original_price * 100)
                    
                    if discount_percent >= 90 and original_price >= 5000:
                        product_info = {
                            'id': product_id,
                            'name': product.get('name', 'Неизвестный товар')[:100],
                            'current_price': current_price,
                            'original_price': original_price,
                            'discount_percent': round(discount_percent, 1),
                            'brand': product.get('brand', 'Неизвестный бренд'),
                            'rating': product.get('rating', 0),
                            'url': f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
                        }
                        found_deals.append(product_info)
                        
                except Exception as e:
                    logging.error(f"Ошибка при обработке товара: {e}")
                    continue
            
            return found_deals
            
        except Exception as e:
            logging.error(f"Ошибка при поиске товаров: {e}")
            return []
    
    def format_deal_message(self, product):
        savings = product['original_price'] - product['current_price']
        
        message = f"""🔥 <b>СУПЕР СКИДКА!</b> 🔥

📦 <b>{product['name']}</b>
🏷️ Бренд: {product['brand']}

💰 Цена: <b>{product['current_price']:,.0f} ₽</b>
💸 Было: <s>{product['original_price']:,.0f} ₽</s>
📉 Скидка: <b>{product['discount_percent']}%</b>
💵 Экономия: <b>{savings:,.0f} ₽</b>

⭐ Рейтинг: {product['rating']}/5

🔗 <a href="{product['url']}">КУПИТЬ СЕЙЧАС</a>

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
🖥️ Работает на сервере 24/7"""
        
        return message
    
    def run_monitoring(self, check_interval=600):
        logging.info("🚀 Запуск мониторинга Wildberries на сервере...")
        
        if not self.test_telegram_connection():
            logging.error("❌ Не удалось подключиться к Telegram!")
            return
        
        while True:
            try:
                logging.info("🔍 Поиск товаров со скидками...")
                deals = self.search_discounted_products()
                
                if deals:
                    logging.info(f"✅ Найдено {len(deals)} товаров со скидками >= 90%")
                    
                    for deal in deals:
                        message = self.format_deal_message(deal)
                        if self.send_telegram_message(message):
                            logging.info(f"📱 Отправлено уведомление о товаре: {deal['name'][:50]}...")
                        time.sleep(3)
                else:
                    logging.info("😔 Товары с подходящими скидками не найдены")
                
                logging.info(f"⏰ Следующая проверка через {check_interval//60} минут...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info("⛔ Мониторинг остановлен")
                break
            except Exception as e:
                logging.error(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(60)

if __name__ == "__main__":
    TELEGRAM_BOT_TOKEN = "8401916969:AAEw4eexj2Xz9URN2fLpxlo-4Uepqr6y7Vg"
    TELEGRAM_CHAT_ID = "754859869"
    
    print("🤖 Wildberries Price Monitor Bot - Server Version")
    print("=" * 50)
    print(f"📱 Telegram Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"👤 Chat ID: {TELEGRAM_CHAT_ID}")
    print("🖥️ Running on Render.com server")
    print("=" * 50)
    
    monitor = WildberriesMonitor(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    monitor.run_monitoring(check_interval=600)
