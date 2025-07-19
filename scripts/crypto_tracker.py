import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

class CryptoTracker:
    def __init__(self):
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.session = requests.Session()
        # Thêm headers để tránh bị block
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        self.usd_to_vnd_rate = None
        self.db = None
        self.collection_name = "crypto & finance"
        
        # Initialize Firebase
        self.init_firebase()

    def init_firebase(self):
        """Khởi tạo Firebase connection"""
        try:
            # Lấy service account key từ environment variable
            service_account_key = os.getenv('SERVICE_ACCOUNT_KEY')
            
            if not service_account_key:
                print("❌ Không tìm thấy SERVICE_ACCOUNT_KEY trong .env file")
                return False
                
            # Parse JSON string thành dict
            service_account_info = json.loads(service_account_key)
            
            # Khởi tạo Firebase app nếu chưa có
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            
            # Khởi tạo Firestore client
            self.db = firestore.client()
            print("✅ Đã kết nối thành công với Firestore")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo Firebase: {e}")
            return False

    def save_to_firestore(self, document_name, data):
        """Lưu dữ liệu vào Firestore"""
        if not self.db:
            print("❌ Chưa kết nối với Firestore")
            return False
            
        try:
            # Thêm timestamp
            data['timestamp'] = datetime.now()
            data['last_updated'] = datetime.now().isoformat()
            
            # Lưu vào collection
            doc_ref = self.db.collection(self.collection_name).document(document_name)
            doc_ref.set(data)
            
            print(f"✅ Đã lưu {document_name} vào Firestore")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi lưu {document_name} vào Firestore: {e}")
            return False

    def get_usd_to_vnd_rate(self):
        """Lấy tỷ giá USD/VND từ API"""
        try:
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'rates' in data and 'VND' in data['rates']:
                self.usd_to_vnd_rate = data['rates']['VND']
                print(f"✅ Tỷ giá USD/VND: {self.usd_to_vnd_rate:,.0f}")
                
                # Lưu tỷ giá vào Firestore
                exchange_rate_data = {
                    'usd_to_vnd': self.usd_to_vnd_rate,
                    'source': 'exchangerate-api.com',
                    'currency_pair': 'USD/VND'
                }
                self.save_to_firestore('exchange_rates', exchange_rate_data)
                
                return True
            else:
                print("❌ Không thể lấy tỷ giá USD/VND")
                return False

        except Exception as e:
            print(f"❌ Lỗi khi lấy tỷ giá: {e}")
            # Fallback rate nếu không lấy được
            self.usd_to_vnd_rate = 24000  # Rate dự phòng
            print(f"⚠️ Sử dụng tỷ giá dự phòng: {self.usd_to_vnd_rate:,.0f}")
            return False

    def get_top_cryptocurrencies(self, limit=10):
        """Lấy top cryptocurrency theo market cap từ CoinGecko"""
        url = f'{self.base_url}/coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': limit,
            'page': 1,
            'sparkline': False
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Tạo mapping từ CoinGecko sang Yahoo Finance symbols
            yahoo_symbols = []
            coin_info = {}

            for coin in data:
                # Mapping các coin phổ biến sang Yahoo Finance symbol
                yahoo_symbol = self.get_yahoo_symbol(coin['symbol'], coin['name'])
                if yahoo_symbol:
                    yahoo_symbols.append(yahoo_symbol)
                    coin_info[yahoo_symbol] = {
                        'name': coin['name'],
                        'symbol': coin['symbol'].upper(),
                        'rank': coin['market_cap_rank'],
                        'coingecko_id': coin['id'],
                        'market_cap': coin.get('market_cap'),
                        'total_volume': coin.get('total_volume')
                    }

            return yahoo_symbols, coin_info

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi lấy top crypto: {e}")
            return None, None
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi parse JSON: {e}")
            return None, None

    def get_yahoo_symbol(self, symbol, name):
        """Mapping cryptocurrency symbols sang Yahoo Finance format"""
        # Mapping các coin phổ biến
        symbol_mapping = {
            'btc': 'BTC-USD',
            'eth': 'ETH-USD',
            'bnb': 'BNB-USD',
            'sol': 'SOL-USD',
            'ada': 'ADA-USD',
            'xrp': 'XRP-USD',
            'dot': 'DOT-USD',
            'doge': 'DOGE-USD',
            'avax': 'AVAX-USD',
            'link': 'LINK-USD',
            'matic': 'MATIC-USD',
            'ltc': 'LTC-USD',
            'bch': 'BCH-USD',
            'xlm': 'XLM-USD',
            'vet': 'VET-USD',
            'fil': 'FIL-USD',
            'trx': 'TRX-USD',
            'etc': 'ETC-USD',
            'atom': 'ATOM-USD',
            'icp': 'ICP-USD',
            'uni': 'UNI-USD',
            'algo': 'ALGO-USD',
            'hbar': 'HBAR-USD',
            'apt': 'APT-USD',
            'near': 'NEAR-USD',
            'op': 'OP-USD',
            'arb': 'ARB-USD',
            'ldo': 'LDO-USD',
            'rpl': 'RPL-USD',
            'mkr': 'MKR-USD'
        }

        symbol_lower = symbol.lower()

        # Kiểm tra mapping trước
        if symbol_lower in symbol_mapping:
            return symbol_mapping[symbol_lower]

        # Nếu không có trong mapping, tạo symbol mặc định
        return f"{symbol.upper()}-USD"

    def get_crypto_data_from_yahoo(self, symbol):
        """Lấy dữ liệu crypto từ Yahoo Finance"""
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']

                current_price = meta.get('regularMarketPrice', meta.get('previousClose', 0))
                previous_close = meta.get('previousClose', 0)

                if current_price and previous_close:
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100
                else:
                    change = 0
                    change_percent = 0

                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'change': change,
                    'change_percent': change_percent,
                    'market_time': meta.get('regularMarketTime', int(time.time())),
                    'currency': meta.get('currency', 'USD')
                }
            else:
                print(f"❌ Không thể parse dữ liệu {symbol}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi lấy dữ liệu {symbol}: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi xử lý dữ liệu {symbol}: {e}")
            return None

    def get_all_crypto_data(self, yahoo_symbols):
        """Lấy dữ liệu tất cả crypto từ Yahoo Finance"""
        crypto_data = {}

        for symbol in yahoo_symbols:
            data = self.get_crypto_data_from_yahoo(symbol)
            if data:
                crypto_data[symbol] = data

        return crypto_data

    def get_stock_data(self, symbol):
        """Lấy dữ liệu chỉ số chứng khoán từ Yahoo Finance API"""
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']

                current_price = meta['regularMarketPrice']
                previous_close = meta['previousClose']
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100

                # Mapping tên chỉ số
                index_names = {
                    '^GSPC': 'S&P 500',
                    '^NDX': 'NASDAQ-100',
                    '^IXIC': 'NASDAQ Composite'
                }

                return {
                    'name': index_names.get(symbol, symbol),
                    'symbol': symbol,
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'change': change,
                    'change_percent': change_percent,
                    'market_time': meta.get('regularMarketTime', int(time.time())),
                    'currency': meta.get('currency', 'USD')
                }
            else:
                print(f"❌ Không thể parse dữ liệu {symbol}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi lấy dữ liệu {symbol}: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi xử lý dữ liệu {symbol}: {e}")
            return None

    def get_gold_data(self):
        """Lấy dữ liệu giá vàng từ Yahoo Finance API"""
        try:
            url = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']

                current_price = meta['regularMarketPrice']
                previous_close = meta['previousClose']
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100

                return {
                    'name': 'Spot Gold',
                    'symbol': 'XAU/USD',
                    'current_price': current_price,
                    'previous_close': previous_close,
                    'change': change,
                    'change_percent': change_percent,
                    'market_time': meta.get('regularMarketTime', int(time.time())),
                    'currency': 'USD'
                }
            else:
                print("❌ Không thể parse dữ liệu Gold")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi lấy dữ liệu Gold: {e}")
            return None
        except Exception as e:
            print(f"❌ Lỗi xử lý dữ liệu Gold: {e}")
            return None

    def get_all_stock_indices(self):
        """Lấy dữ liệu tất cả chỉ số chứng khoán"""
        indices = {}

        # Lấy dữ liệu từng chỉ số
        sp500 = self.get_stock_data('^GSPC')
        nasdaq100 = self.get_stock_data('^NDX')
        nasdaq_composite = self.get_stock_data('^IXIC')

        if sp500:
            indices['SP500'] = sp500
        if nasdaq100:
            indices['NASDAQ100'] = nasdaq100
        if nasdaq_composite:
            indices['NASDAQ_COMPOSITE'] = nasdaq_composite

        return indices

    def get_all_commodities(self):
        """Lấy dữ liệu tất cả hàng hóa"""
        commodities = {}

        # Lấy dữ liệu vàng
        gold = self.get_gold_data()

        if gold:
            commodities['GOLD'] = gold

        return commodities

    def format_price(self, price, currency='usd'):
        """Format giá tiền"""
        if currency.lower() == 'vnd':
            return f"{price:,.0f} ₫"
        elif currency.lower() == 'usd':
            return f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
        else:
            return f"{price:,.2f} {currency.upper()}"

    def format_dual_price(self, usd_price):
        """Format giá USD và VND"""
        usd_formatted = self.format_price(usd_price, 'usd')

        if self.usd_to_vnd_rate:
            vnd_price = usd_price * self.usd_to_vnd_rate
            vnd_formatted = self.format_price(vnd_price, 'vnd')
            return f"{usd_formatted} | {vnd_formatted}"
        else:
            return usd_formatted

    def format_change(self, change):
        """Format % thay đổi"""
        if change is None:
            return "N/A"
        symbol = "📈" if change > 0 else "📉"
        color = "\033[92m" if change > 0 else "\033[91m"  # Xanh lá cho tăng, đỏ cho giảm
        reset = "\033[0m"
        return f"{color}{symbol} {change:+.2f}%{reset}"

    def display_stock_data(self, stock_data):
        """Hiển thị dữ liệu chỉ số chứng khoán"""
        if not stock_data:
            print("❌ Không có dữ liệu chứng khoán")
            return

        # Icon cho từng chỉ số
        icons = {
            'S&P 500': '🏛️',
            'NASDAQ-100': '🚀',
            'NASDAQ Composite': '💻'
        }

        print(f"\n{icons.get(stock_data['name'], '📊')} {stock_data['name']} ({stock_data['symbol']})")
        print(f"   💵 Giá hiện tại: {self.format_dual_price(stock_data['current_price'])}")
        print(f"   📊 Thay đổi: {self.format_change(stock_data['change_percent'])}")
        print(f"   📈 Điểm thay đổi: {stock_data['change']:+.2f}")
        print(f"   🔒 Giá đóng cửa hôm trước: {self.format_dual_price(stock_data['previous_close'])}")

        market_time = datetime.fromtimestamp(stock_data['market_time'])
        print(f"   ⏰ Thời gian thị trường: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def display_commodity_data(self, commodity_data):
        """Hiển thị dữ liệu hàng hóa"""
        if not commodity_data:
            print("❌ Không có dữ liệu hàng hóa")
            return

        # Icon cho hàng hóa
        icons = {
            'Spot Gold': '🥇'
        }

        print(f"\n{icons.get(commodity_data['name'], '📦')} {commodity_data['name']} ({commodity_data['symbol']})")
        print(f"   💵 Giá hiện tại: {self.format_dual_price(commodity_data['current_price'])}/oz")
        print(f"   📊 Thay đổi: {self.format_change(commodity_data['change_percent'])}")
        print(f"   📈 Điểm thay đổi: {commodity_data['change']:+.2f}")
        print(f"   🔒 Giá đóng cửa hôm trước: {self.format_dual_price(commodity_data['previous_close'])}/oz")

        market_time = datetime.fromtimestamp(commodity_data['market_time'])
        print(f"   ⏰ Thời gian thị trường: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def display_all_commodities(self, commodities_data):
        """Hiển thị tất cả hàng hóa"""
        if not commodities_data:
            print("❌ Không có dữ liệu hàng hóa")
            return

        print(f"\n{'='*70}")
        print(f"🥇 HÀNG HÓA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        # Hiển thị vàng
        if 'GOLD' in commodities_data:
            self.display_commodity_data(commodities_data['GOLD'])

    def display_all_stock_indices(self, indices_data):
        """Hiển thị tất cả chỉ số chứng khoán"""
        if not indices_data:
            print("❌ Không có dữ liệu chỉ số chứng khoán")
            return

        print(f"\n{'='*70}")
        print(f"📊 CÁC CHỈ SỐ CHỨNG KHOÁN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        # Hiển thị theo thứ tự: S&P 500, NASDAQ-100, NASDAQ Composite
        order = ['SP500', 'NASDAQ100', 'NASDAQ_COMPOSITE']

        for key in order:
            if key in indices_data:
                self.display_stock_data(indices_data[key])

    def display_crypto_data_yahoo(self, crypto_data, coin_info):
        """Hiển thị dữ liệu crypto từ Yahoo Finance với thứ hạng"""
        if not crypto_data or not coin_info:
            print("❌ Không có dữ liệu crypto để hiển thị")
            return

        print(f"\n{'='*120}")
        print(f"💰 TOP 10 CRYPTOCURRENCY (Yahoo Finance) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*120}")

        # Sắp xếp theo thứ hạng market cap
        sorted_coins = sorted(coin_info.items(), key=lambda x: x[1]['rank'])

        for yahoo_symbol, info in sorted_coins:
            if yahoo_symbol in crypto_data:
                data = crypto_data[yahoo_symbol]

                # Header với thứ hạng
                print(f"\n#{info['rank']} 🪙 {info['name']} ({info['symbol']})")
                print(f"   📊 Yahoo Symbol: {yahoo_symbol}")

                # Giá hiện tại (USD và VND)
                current_price = data['current_price']
                print(f"   💵 Giá hiện tại: {self.format_dual_price(current_price)}")

                # Thay đổi
                print(f"   📊 Thay đổi: {self.format_change(data['change_percent'])}")

                # Điểm thay đổi (USD và VND)
                change_usd = data['change']
                if self.usd_to_vnd_rate:
                    change_vnd = change_usd * self.usd_to_vnd_rate
                    print(f"   📈 Điểm thay đổi: {change_usd:+.4f} USD | {change_vnd:+,.0f} ₫")
                else:
                    print(f"   📈 Điểm thay đổi: {change_usd:+.4f} USD")

                # Giá đóng cửa hôm trước
                print(f"   🔒 Giá đóng cửa hôm trước: {self.format_dual_price(data['previous_close'])}")

                # Thời gian cập nhật
                market_time = datetime.fromtimestamp(data['market_time'])
                print(f"   ⏰ Thời gian cập nhật: {market_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"\n#{info['rank']} ❌ {info['name']} ({info['symbol']}) - Không có dữ liệu từ Yahoo Finance")

    def save_all_data_to_firestore(self, crypto_data, coin_info, stock_indices, commodities):
        """Lưu tất cả dữ liệu vào Firestore"""
        saved_count = 0
        
        # Lưu dữ liệu cryptocurrency
        if crypto_data and coin_info:
            # Kết hợp crypto_data với coin_info
            combined_crypto_data = {}
            for yahoo_symbol, data in crypto_data.items():
                if yahoo_symbol in coin_info:
                    combined_crypto_data[yahoo_symbol] = {
                        **data,
                        **coin_info[yahoo_symbol],
                        'usd_to_vnd_rate': self.usd_to_vnd_rate
                    }
            
            if self.save_to_firestore('cryptocurrencies', {
                'data': combined_crypto_data,
                'total_coins': len(combined_crypto_data),
                'source': 'Yahoo Finance + CoinGecko'
            }):
                saved_count += 1
        
        # Lưu dữ liệu chỉ số chứng khoán
        if stock_indices:
            if self.save_to_firestore('stock_indices', {
                'data': stock_indices,
                'total_indices': len(stock_indices),
                'source': 'Yahoo Finance',
                'usd_to_vnd_rate': self.usd_to_vnd_rate
            }):
                saved_count += 1
        
        # Lưu dữ liệu hàng hóa
        if commodities:
            if self.save_to_firestore('commodities', {
                'data': commodities,
                'total_commodities': len(commodities),
                'source': 'Yahoo Finance',
                'usd_to_vnd_rate': self.usd_to_vnd_rate
            }):
                saved_count += 1
        
        # Lưu tổng quan thị trường
        market_overview = {
            'crypto_count': len(crypto_data) if crypto_data else 0,
            'stock_indices_count': len(stock_indices) if stock_indices else 0,
            'commodities_count': len(commodities) if commodities else 0,
            'usd_to_vnd_rate': self.usd_to_vnd_rate,
            'data_sources': ['Yahoo Finance', 'CoinGecko', 'Exchange Rate API']
        }
        
        if self.save_to_firestore('market_overview', market_overview):
            saved_count += 1
        
        return saved_count

    def get_data_from_firestore(self, document_name):
            """Lấy dữ liệu từ Firestore"""
            try:
                if not hasattr(self, 'db') or not self.db:
                    if not self.init_firebase():
                        return None
                
                doc_ref = self.db.collection(self.collection_name).document(document_name)
                doc = doc_ref.get()
                
                if doc.exists:
                    print(f"✅ Đã lấy dữ liệu {document_name} từ Firestore")
                    return doc.to_dict()
                else:
                    print(f"❌ Không tìm thấy document {document_name} trong Firestore")
                    return None
                    
            except Exception as e:
                print(f"❌ Lỗi khi lấy dữ liệu từ Firestore: {e}")
                return None

    def list_all_documents(self):
        """Liệt kê tất cả documents trong collection 'crypto & finance'"""
        try:
            if not hasattr(self, 'db') or not self.db:
                if not self.init_firebase():
                    return None
            
            docs = self.db.collection(self.collection_name).stream()
            
            print(f"\n📋 Danh sách documents trong collection '{self.collection_name}':")
            print("-" * 60)
            
            for doc in docs:
                data = doc.to_dict()
                timestamp = data.get('timestamp', 'N/A')
                print(f"📄 {doc.id} - {timestamp}")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi liệt kê documents: {e}")
            return False

    def clear_collection(self, batch_size=500):
        """Xóa toàn bộ dữ liệu cũ trong collection trước khi ghi mới."""
        if not self.db:
            if not self.init_firebase():
                print("❌ Không thể kết nối Firestore để xóa dữ liệu.")
                return False

        coll_ref = self.db.collection(self.collection_name)

        total_deleted = 0
        while True:
            docs = coll_ref.limit(batch_size).stream()
            deleted_in_batch = 0
            for doc in docs:
                doc.reference.delete()
                deleted_in_batch += 1
            total_deleted += deleted_in_batch
            if deleted_in_batch < batch_size:
                break  # đã hết document

        print(f"🧹 Đã xóa {total_deleted} documents cũ trong collection '{self.collection_name}'.")
        return True
    
    def full_market_overview(self):
        """Hiển thị tổng quan thị trường và lưu vào Firestore"""
        # Khởi tạo Firebase
        if not self.init_firebase():
            print("❌ Không thể khởi tạo Firebase. Tiếp tục mà không lưu dữ liệu.")
        
        # Lấy tỷ giá USD/VND trước
        print("🔄 Đang lấy tỷ giá USD/VND...")
        self.get_usd_to_vnd_rate()

        print("🔄 Đang lấy top 10 cryptocurrency từ CoinGecko...")

        # Lấy top 10 crypto từ CoinGecko
        yahoo_symbols, coin_info = self.get_top_cryptocurrencies(10)

        if not yahoo_symbols or not coin_info:
            print("❌ Không thể lấy danh sách top 10 crypto")
            return False

        print(f"✅ Đã lấy được {len(yahoo_symbols)} coin symbols cho Yahoo Finance")
        print(f"📋 Danh sách: {', '.join(yahoo_symbols)}")

        print("🔄 Đang lấy dữ liệu từ Yahoo Finance...")

        # Lấy dữ liệu crypto từ Yahoo Finance
        crypto_data = self.get_all_crypto_data(yahoo_symbols)

        # Lấy dữ liệu các chỉ số chứng khoán
        stock_indices = self.get_all_stock_indices()

        # Lấy dữ liệu hàng hóa
        commodities = self.get_all_commodities()

        print(f"\n{'='*120}")
        print(f"🌍 TỔNG QUAN THỊ TRƯỜNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.usd_to_vnd_rate:
            print(f"💱 Tỷ giá USD/VND: {self.usd_to_vnd_rate:,.0f}")
        print(f"{'='*120}")

        # Hiển thị các chỉ số chứng khoán
        if stock_indices:
            self.display_all_stock_indices(stock_indices)
        else:
            print("❌ Không thể lấy dữ liệu chỉ số chứng khoán")

        # Hiển thị hàng hóa
        if commodities:
            self.display_all_commodities(commodities)
        else:
            print("❌ Không thể lấy dữ liệu hàng hóa")

        # Hiển thị crypto từ Yahoo Finance
        if crypto_data and coin_info:
            self.display_crypto_data_yahoo(crypto_data, coin_info)
            success_count = len(crypto_data)
            total_count = len(yahoo_symbols)
            print(f"\n📊 Thống kê: {success_count}/{total_count} coin có dữ liệu từ Yahoo Finance")
        else:
            print("❌ Không thể lấy dữ liệu crypto từ Yahoo Finance")

        # Lưu dữ liệu vào Firestore
        if hasattr(self, 'db') and self.db:
            print("\n🧹 Đang xóa dữ liệu cũ trong Firestore...")
            self.clear_collection()

            print("\n🔄 Đang lưu dữ liệu mới vào Firestore...")
            saved_count = self.save_all_data_to_firestore(crypto_data, coin_info, stock_indices, commodities)
            if saved_count > 0:
                print(f"✅ Đã lưu {saved_count} documents vào Firestore thành công!")
            else:
                print("❌ Có lỗi khi lưu dữ liệu vào Firestore")
        else:
            print("⚠️ Không thể lưu vào Firestore do lỗi khởi tạo")

        return crypto_data and coin_info

if __name__ == "__main__":
    tracker = CryptoTracker()
    
    # Test chạy full market overview
    success = tracker.full_market_overview()
    
    if success:
        print("\n✅ Chương trình chạy thành công!")
        
        # Optional: List all documents
        print("\n🔍 Liệt kê tất cả documents:")
        tracker.list_all_documents()
    else:
        print("\n❌ Chương trình gặp lỗi!")