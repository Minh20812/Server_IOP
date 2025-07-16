import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import re
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
from dotenv import load_dotenv
import os

class ProductHuntScraper:
    def __init__(self):
        self.base_url = "https://www.producthunt.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Khởi tạo Firebase
        self.db = None
        self.init_firebase()
        
    def init_firebase(self):
        """Khởi tạo Firebase Admin SDK từ biến môi trường"""
        try:
            # Load biến môi trường
            load_dotenv()
            service_account_json = os.getenv("SERVICE_ACCOUNT_KEY")
            
            if not service_account_json:
                print("⚠️ Cảnh báo: Không tìm thấy biến SERVICE_ACCOUNT_KEY trong .env")
                print("📋 Hướng dẫn cấu hình:")
                print("   1. Tạo file .env trong thư mục gốc")
                print("   2. Thêm dòng: SERVICE_ACCOUNT_KEY='{json_content}'")
                print("   3. Script sẽ chạy mà không lưu vào Firebase")
                return
            
            if not firebase_admin._apps:
                # Parse JSON chuỗi thành dict
                service_account_dict = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_dict)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase đã được khởi tạo từ biến môi trường")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Firebase: {str(e)}")
            print("💡 Script sẽ tiếp tục chạy nhưng không lưu vào Firebase")
        
    def get_yesterday_date(self):
        """Lấy ngày hôm qua theo múi giờ Việt Nam (UTC+7)"""
        # Tạo timezone Việt Nam
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        # Lấy thời gian hiện tại theo múi giờ Việt Nam
        now_vietnam = datetime.now(vietnam_tz)
        
        # Lấy ngày hôm qua
        yesterday = now_vietnam - timedelta(days=1)
        
        # Format theo định dạng YYYY/M/D (không có số 0 đầu)
        year = yesterday.year
        month = yesterday.month
        day = yesterday.day
        
        print(f"🕐 Thời gian hiện tại (VN): {now_vietnam.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Ngày cần lấy dữ liệu: {year}/{month}/{day}")
        
        return f"{year}/{month}/{day}"
    
    def build_url(self, date_str=None):
        """Tạo URL cho trang leaderboard theo ngày"""
        if date_str is None:
            date_str = self.get_yesterday_date()
        
        # Chuyển đổi từ YYYY/M/D sang YYYY/M/D format cho URL
        url = f"{self.base_url}/leaderboard/daily/{date_str}?ref=header_nav"
        return url
    
    def scrape_products(self, url):
        """Lấy dữ liệu các sản phẩm từ trang leaderboard"""
        try:
            print(f"🌐 Đang truy cập: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            print(f"✅ Truy cập thành công! Status code: {response.status_code}")
            print(f"📊 Kích thước response: {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Tìm các section chứa thông tin sản phẩm với data-test="post-item-*"
            product_elements = soup.find_all('section', {'data-test': re.compile(r'post-item-\d+')})
            
            if not product_elements:
                print("⚠️ Không tìm thấy section với data-test='post-item-*', thử tìm cách khác...")
                # Fallback: tìm sections có class chứa thông tin sản phẩm
                product_elements = soup.find_all('section', class_=re.compile(r'.*group.*relative.*flex.*'))
                print(f"🔍 Tìm được {len(product_elements)} elements với fallback method")
            
            print(f"🎯 Tìm thấy {len(product_elements)} sản phẩm")
            
            for i, element in enumerate(product_elements[:20]):  # Giới hạn 20 sản phẩm đầu
                try:
                    print(f"🔄 Đang xử lý sản phẩm #{i+1}...")
                    product_data = self.extract_product_info(element, rank=i+1)  # Truyền rank vào
                    if product_data and product_data['title'] != 'N/A':
                        products.append(product_data)
                        print(f"✅ Thành công: #{product_data['rank']} - {product_data['title']}")
                    else:
                        print(f"⚠️ Bỏ qua sản phẩm #{i+1} (không lấy được tên)")
                except Exception as e:
                    print(f"❌ Lỗi khi xử lý sản phẩm #{i+1}: {str(e)}")
                    continue
            
            print(f"🏁 Hoàn thành! Đã lấy được {len(products)} sản phẩm hợp lệ")
            return products
            
        except requests.RequestException as e:
            print(f"❌ Lỗi khi truy cập trang: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Lỗi không xác định: {str(e)}")
            return []
    
    def extract_product_info(self, element, rank):
        """Trích xuất thông tin sản phẩm từ element HTML - bao gồm rank"""
        product = {
            'rank': rank,  # Thêm field rank
            'title': 'N/A',
            'description': 'N/A',
            'link': 'N/A',
            'topics': [],
            'image': 'N/A',
            'date': self.get_yesterday_date()
        }
        
        try:
            # Tìm tên sản phẩm từ link với data-test="post-name-*"
            name_link = element.find('a', {'data-test': re.compile(r'post-name-\d+')})
            if name_link:
                product['title'] = name_link.get_text(strip=True)
                # Lấy href để tạo link đầy đủ
                href = name_link.get('href')
                if href:
                    product['link'] = f"{self.base_url}{href}" if href.startswith('/') else href
                print(f"  📝 Tên: {product['title']}")
            
            # Tìm mô tả (text-secondary trong cấu trúc)
            desc_element = element.find('a', class_=re.compile(r'.*text-secondary.*'))
            if desc_element:
                product['description'] = desc_element.get_text(strip=True)
                print(f"  📄 Mô tả: {product['description'][:50]}...")
            
            # Tìm topics/tags
            topic_links = element.find_all('a', href=re.compile(r'/topics/'))
            for link in topic_links:
                topic_name = link.get_text(strip=True)
                if topic_name:
                    product['topics'].append(topic_name)
            
            if product['topics']:
                print(f"  🏷️ Topics: {', '.join(product['topics'])}")
            
            # Tìm hình ảnh
            img_element = element.find('img')
            if img_element:
                product['image'] = img_element.get('src') or img_element.get('srcset', '').split(' ')[0]
                print(f"  🖼️ Có hình ảnh: {product['image'][:50]}...")
            
            print(f"  🏆 Rank: {product['rank']}")
            
        except Exception as e:
            print(f"  ❌ Lỗi khi trích xuất thông tin: {str(e)}")
        
        return product
    
    def clear_collection(self, collection_name):
        """Xóa toàn bộ documents trong collection"""
        if not self.db:
            print("❌ Firebase chưa được khởi tạo")
            return False
            
        try:
            print(f"🗑️ Đang xóa collection '{collection_name}'...")
            
            # Lấy tất cả documents
            docs = self.db.collection(collection_name).stream()
            
            # Xóa từng document
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            print(f"✅ Đã xóa {deleted_count} documents từ collection '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi xóa collection: {str(e)}")
            return False
    
    def save_to_firestore(self, products, collection_name="producthunt", clear_existing=True):
        """Lưu danh sách sản phẩm vào Firestore - bao gồm field rank"""
        if not self.db:
            print("❌ Firebase chưa được khởi tạo - bỏ qua việc lưu vào database")
            return False
            
        if not products:
            print("⚠️ Không có sản phẩm nào để lưu")
            return False
        
        try:
            # LUÔN xóa collection cũ trước khi lưu dữ liệu mới
            print(f"🗑️ Đang xóa toàn bộ dữ liệu cũ trong collection '{collection_name}'...")
            clear_success = self.clear_collection(collection_name)
            
            if not clear_success:
                print("⚠️ Có lỗi khi xóa dữ liệu cũ, nhưng vẫn tiếp tục lưu dữ liệu mới...")
            
            print(f"💾 Đang lưu {len(products)} sản phẩm mới vào Firestore...")
            
            saved_count = 0
            for product in products:
                doc_data = {
                    'rank': product['rank'],
                    'date': product['date'],
                    'description': product['description'],
                    'title': product['title'],
                    'image': product['image'],
                    'link': product['link'],
                    'topics': product['topics']
                }
                
                # Lưu vào Firestore
                doc_ref = self.db.collection(collection_name).document()
                doc_ref.set(doc_data)
                saved_count += 1
                
                print(f"  ✅ Đã lưu: #{product['rank']} - {product['title']}")
            
            print(f"🎉 Thành công! Đã thay thế toàn bộ dữ liệu cũ bằng {saved_count} sản phẩm mới trong collection '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi lưu vào Firestore: {str(e)}")
            return False
    
    def save_to_json(self, products, filename=None):
        """Lưu dữ liệu ra file JSON (backup method) - bao gồm field rank"""
        if not products:
            print("⚠️ Không có sản phẩm nào để lưu")
            return False
        
        try:
            if filename is None:
                date_str = self.get_yesterday_date().replace('/', '-')
                filename = f"producthunt_{date_str}.json"
            
            # Chuẩn bị dữ liệu bao gồm rank
            data = {
                'date': self.get_yesterday_date(),
                'scraped_at': datetime.now().isoformat(),
                'total_products': len(products),
                'products': [{
                    'rank': product['rank'],  # Thêm rank vào JSON
                    'date': product['date'],
                    'description': product['description'],
                    'title': product['title'],
                    'image': product['image'],
                    'link': product['link'],
                    'topics': product['topics']
                } for product in products]
            }
            
            # Lưu file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Đã lưu {len(products)} sản phẩm vào file: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi lưu file JSON: {str(e)}")
            return False
    
    def print_detailed_results(self, products):
        """In kết quả chi tiết ra console - bao gồm rank"""
        if not products:
            print("❌ Không tìm thấy sản phẩm nào!")
            return
        
        date_str = self.get_yesterday_date()
        print(f"\n{'='*80}")
        print(f"🏆 SẢN PHẨM HOT NHẤT NGÀY {date_str}")
        print(f"📊 Tổng số sản phẩm tìm thấy: {len(products)}")
        print(f"{'='*80}")
        
        for product in products:
            print(f"\n🏆 #{product['rank']} - {product['title']}")
            print(f"   📅 Ngày: {product['date']}")
            print(f"   📝 Mô tả: {product['description']}")
            if product['topics']:
                print(f"   🏷️ Topics: {', '.join(product['topics'])}")
            print(f"   🔗 Link: {product['link']}")
            if product['image'] != 'N/A':
                print(f"   🖼️ Image: {product['image']}")
            print(f"   {'-'*70}")
        
        print(f"\n🎉 Hoàn thành! Đã hiển thị {len(products)} sản phẩm hàng đầu")
        print(f"⏰ Thời gian xử lý: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run(self, save_to_db=True, save_to_file=True):
        """Chạy script chính"""
        print("🚀 BẮT ĐẦU LẤY DỮ LIỆU TỪ PRODUCT HUNT")
        print("="*50)
        
        # Tạo URL cho ngày hôm qua
        print("📅 Đang xác định ngày cần lấy dữ liệu...")
        url = self.build_url()
        print(f"🔗 URL được tạo: {url}")
        
        # Lấy dữ liệu
        print("\n🔍 Bắt đầu quá trình scraping...")
        products = self.scrape_products(url)
        
        if products:
            print(f"\n✅ THÀNH CÔNG! Đã lấy được {len(products)} sản phẩm")
            
            # In kết quả chi tiết
            self.print_detailed_results(products)
            
            # Lưu vào Firestore nếu được yêu cầu
            if save_to_db:
                print(f"\n💾 Đang thay thế dữ liệu cũ và lưu dữ liệu mới vào Firestore...")
                success = self.save_to_firestore(products)
                if success:
                    print("✅ Dữ liệu đã được thay thế thành công trong Firestore!")
                else:
                    print("❌ Có lỗi khi thay thế dữ liệu trong Firestore")
            
            # Lưu vào file JSON như backup
            if save_to_file:
                print(f"\n📄 Đang lưu backup vào file JSON...")
                self.save_to_json(products)
            
        else:
            print("\n❌ THẤT BẠI! Không thể lấy dữ liệu")
            print("🔍 Có thể do các nguyên nhân sau:")
            print("   • Trang web thay đổi cấu trúc HTML")
            print("   • Server chặn request (anti-bot)")
            print("   • Kết nối internet không ổn định")
            print("   • URL không chính xác hoặc trang không tồn tại")
            print("\n💡 Gợi ý khắc phục:")
            print("   • Thử lại sau vài phút")
            print("   • Kiểm tra kết nối internet")
            print("   • Cập nhật User-Agent header")

# Chạy script
if __name__ == "__main__":
    print("🔧 CẤU HÌNH FIREBASE")
    print("="*30)
    print("💡 Sử dụng biến môi trường:")
    print("   1. Tạo file .env trong thư mục gốc")
    print("   2. Thêm: SERVICE_ACCOUNT_KEY='{nội dung JSON service account key}'")
    print("   3. Chạy script")
    print("\n🎯 CHÍNH SÁCH LƯU TRỮ:")
    print("   • Mỗi lần chạy sẽ XÓA TOÀN BỘ dữ liệu cũ")
    print("   • Sau đó lưu dữ liệu mới vào collection 'producthunt'")
    print("   • Đảm bảo dữ liệu luôn là mới nhất")
    print("\n🎯 CÁC FIELD ĐƯỢC LƯU:")
    print("   • rank (mới)")
    print("   • date")
    print("   • description") 
    print("   • title")
    print("   • image")
    print("   • link")
    print("   • topics")
    print("\n" + "="*50)
    
    # Khởi tạo scraper
    scraper = ProductHuntScraper()
    
    # Chạy với cả hai tùy chọn lưu trữ
    scraper.run(save_to_db=True, save_to_file=True)