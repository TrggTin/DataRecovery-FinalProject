import os
import struct
import binascii
import sys
import codecs
import shutil
import random

# Đảm bảo đầu ra UTF-8 để hỗ trợ các ký tự tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.platform.startswith('win'):
        os.system('chcp 65001')

class ImageCorruptor:
    """
    Lớp để tạo ra một tập tin bị hỏng giả lập việc mất mát dữ liệu
    Mục đích: Mô phỏng các tình huống khôi phục tập tin
    """
    def __init__(self, source_file):
        self.source_file = source_file
    
    def corrupt_file(self, output_volume):
        """
        Tạo ra một tập tin bị 'hỏng' bằng cách thêm các byte ngẫu nhiên
        và một phần của dữ liệu gốc
        """
        try:
            # Đọc toàn bộ dữ liệu của tập tin nguồn
            with open(self.source_file, 'rb') as src:
                file_data = src.read()
            
            # Ghi vào tập tin volume với cấu trúc phức tạp
            with open(output_volume, 'wb') as vol:
                # Thêm các byte ngẫu nhiên ở đầu
                vol.write(os.urandom(1024))
                # Ghi toàn bộ dữ liệu gốc
                vol.write(file_data)
                # Thêm thêm byte ngẫu nhiên
                vol.write(os.urandom(512))
                # Ghi một phần của dữ liệu gốc
                vol.write(file_data[:len(file_data)//2])
                # Thêm byte ngẫu nhiên cuối cùng
                vol.write(os.urandom(1024))
            
            return True
        except Exception as e:
            print(f"Lỗi khi tạo volume bị hỏng: {e}")
            return False

class ImageRecovery:
    """
    Lớp chuyên trách việc khôi phục các tập tin hình ảnh từ dữ liệu bị hỏng
    Hỗ trợ nhiều định dạng tập tin
    """
    # Chữ ký mở rộng để nhận dạng các định dạng tập tin
    SIGNATURES = {
        'jpg': (
            b'\xFF\xD8\xFF\xE0',  # JFIF
            b'\xFF\xD8\xFF\xE1',  # Exif
            b'\xFF\xD8\xFF\xDB',  # JPEG với bảng lượng tử hóa
            b'\xFF\xD8\xFF\xEE'   # JPEG với phân đoạn ứng dụng
        ),
        'png': (b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',),
        'gif': (
            b'GIF87a',  # Phiên bản GIF 87a
            b'GIF89a'   # Phiên bản GIF 89a
        ),
        'bmp': (b'BM',),  # Chữ ký của tập tin BMP
        'webp': (b'RIFF', b'WEBP')  # Chữ ký của WebP
    }
    
    # Ký hiệu kết thúc tập tin cho từng định dạng
    EOF_MARKERS = {
        'jpg': b'\xFF\xD9',
        'png': b'\x49\x45\x4E\x44\xAE\x42\x60\x82',
        'gif': b'\x3B',  # Ký tự kết thúc của GIF
        'bmp': None,     # BMP không có ký tự kết thúc chuẩn
        'webp': b'WEBP'
    }

    def __init__(self, volume_path):
        self.volume_path = volume_path
        self.recovered_files = 0
        
    def read_volume(self):
        """Đọc toàn bộ nội dung của tập tin volume"""
        try:
            with open(self.volume_path, 'rb') as f:
                return f.read()
        except IOError as e:
            print(f"Lỗi đọc volume: {e}")
            return None

    def find_file_boundaries(self, data, file_type):
        """
        Tìm các ranh giới của tập tin trong dữ liệu
        Trả về danh sách các vị trí bắt đầu và kết thúc
        """
        boundaries = []
        start_positions = []
        
        # Tìm tất cả các vị trí bắt đầu có thể
        for sig in self.SIGNATURES[file_type]:
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1:
                    break
                start_positions.append(pos)
                pos += 1
        
        start_positions.sort()
        
        # Tìm các điểm kết thúc tương ứng
        for start in start_positions:
            # Giới hạn kích thước để tránh các kết quả sai
            MAX_SIZE = 20 * 1024 * 1024  # 20MB kích thước tối đa
            search_end = min(start + MAX_SIZE, len(data))
            
            # Xử lý các định dạng khác nhau
            if self.EOF_MARKERS[file_type] is None:
                # Với các định dạng không có ký tự kết thúc (như BMP)
                # Sử dụng kích thước tối đa
                boundaries.append((start, start + MAX_SIZE))
            else:
                end = data.find(self.EOF_MARKERS[file_type], start, search_end)
                
                if end != -1:
                    end += len(self.EOF_MARKERS[file_type])
                    boundaries.append((start, end))
        
        return boundaries

    def validate_image(self, data, file_type):
        """
        Kiểm tra tính hợp lệ của tập tin hình ảnh
        Sử dụng các quy tắc kiểm tra cụ thể cho từng định dạng
        """
        if len(data) < 64:  # Kiểm tra kích thước tối thiểu
            return False
            
        if file_type == 'jpg':
            # Kiểm tra cấu trúc JPEG
            return (data[0:2] == b'\xFF\xD8' and 
                    data[-2:] == b'\xFF\xD9' and
                    b'\xFF\xDA' in data)  # Có dữ liệu nén
            
        elif file_type == 'png':
            # Kiểm tra chữ ký PNG và các phần quan trọng
            return (data.startswith(b'\x89PNG\r\n\x1a\n') and
                    data.endswith(b'IEND\xAE\x42\x60\x82') and
                    b'IHDR' in data and b'IDAT' in data)
        
        elif file_type == 'gif':
            # Kiểm tra chữ ký và kết thúc GIF
            return (data.startswith(b'GIF87a') or data.startswith(b'GIF89a')) and \
                   data.endswith(b'\x3B')
        
        elif file_type == 'bmp':
            # Kiểm tra chữ ký BMP
            return data.startswith(b'BM')
        
        elif file_type == 'webp':
            # Kiểm tra chữ ký WebP
            return data.startswith(b'RIFF') and b'WEBP' in data
            
        return False

    def save_recovered_file(self, data, file_type):
        """Lưu tập tin đã khôi phục với tên duy nhất"""
        filename = f"recovered_{self.recovered_files}.{file_type}"
        try:
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"Đã khôi phục: {filename}")
            self.recovered_files += 1
            return True
        except IOError as e:
            print(f"Lỗi lưu {filename}: {e}")
            return False

    def recover_images(self):
        """
        Quy trình chính của việc khôi phục hình ảnh
        Thử khôi phục cho các định dạng khác nhau
        """
        print("Bắt đầu quá trình khôi phục hình ảnh...")
        
        volume_data = self.read_volume()
        if volume_data is None:
            return
        
        # Danh sách các định dạng hỗ trợ
        file_types = ['jpg', 'png', 'gif', 'bmp', 'webp']
        
        for file_type in file_types:
            print(f"\nTìm kiếm tập tin {file_type.upper()}...")
            boundaries = self.find_file_boundaries(volume_data, file_type)
            
            for start, end in boundaries:
                image_data = volume_data[start:end]
                if self.validate_image(image_data, file_type):
                    self.save_recovered_file(image_data, file_type)
        
        print(f"\nHoàn tất. Tổng số tập tin đã khôi phục: {self.recovered_files}")

def cleanup_files():
    """Xóa các tập tin tạm và kết quả từ các lần chạy trước"""
    files_to_remove = ['corrupted.vol'] + [f for f in os.listdir() if f.startswith('recovered_')]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

def print_file_info(filepath):
    """In thông tin chi tiết của tập tin"""
    size = os.path.getsize(filepath)
    print(f"- Tên tập tin: {filepath}")
    print(f"- Kích thước: {size} byte")
    print(f"- Định dạng: {os.path.splitext(filepath)[1].upper()}")

def run_demo_with_real_image(image_path):
    """
    Chạy demo khôi phục tập tin 
    Mô phỏng quá trình mất mát và khôi phục dữ liệu
    """
    print("=== BẮT ĐẦU DEMO KHÔI PHỤC HÌNH ẢNH ===")
    
    if not os.path.exists(image_path):
        print(f"Không tìm thấy tập tin hình ảnh: {image_path}")
        return
    
    print("\nThông tin tập tin gốc:")
    print_file_info(image_path)
    
    print("\nXóa các tập tin cũ...")
    cleanup_files()
    
    print("\nTạo volume bị hỏng...")
    corruptor = ImageCorruptor(image_path)
    if not corruptor.corrupt_file('corrupted.vol'):
        print("Không thể tạo volume bị hỏng!")
        return
    
    print("Đã tạo volume bị hỏng:")
    print_file_info('corrupted.vol')
    
    print("\nBắt đầu quá trình khôi phục...")
    recovery = ImageRecovery('corrupted.vol')
    recovery.recover_images()
    
    recovered_files = [f for f in os.listdir() if f.startswith('recovered_')]
    print("\nKết quả khôi phục:")
    for file in recovered_files:
        print_file_info(file)
    
    print("\n=== DEMO HOÀN TẤT ===")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Cách sử dụng: python script.py <đường_dẫn_tập_tin_hình_ảnh>")
        print("Ví dụ: python script.py image.jpg")
        sys.exit(1)
    
    run_demo_with_real_image(sys.argv[1])