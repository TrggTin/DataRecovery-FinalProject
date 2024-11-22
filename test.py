import os
import struct
import binascii
import sys
import codecs

# Thiết lập encoding cho stdout để hỗ trợ tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.platform.startswith('win'):
        os.system('chcp 65001')

class ImageRecovery:
    # Định nghĩa signature của JPG và PNG
    SIGNATURES = {
        'jpg': (b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1'),  # SOI markers cho JPEG
        'png': (b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',)  # Signature cho PNG
    }
    
    # Định nghĩa EOF markers
    EOF_MARKERS = {
        'jpg': b'\xFF\xD9',  # EOI marker cho JPEG
        'png': b'\x49\x45\x4E\x44\xAE\x42\x60\x82'  # IEND chunk cho PNG
    }

    def __init__(self, volume_path):
        self.volume_path = volume_path
        self.recovered_files = 0
        
    def read_volume(self):
        """Đọc dữ liệu từ volume"""
        try:
            with open(self.volume_path, 'rb') as f:
                return f.read()
        except IOError as e:
            print(f"Loi khi doc volume: {e}")
            return None

    def find_file_boundaries(self, data, file_type):
        """Tìm vị trí bắt đầu và kết thúc của các file ảnh"""
        boundaries = []
        
        # Tìm tất cả các signature phù hợp
        start_positions = []
        for sig in self.SIGNATURES[file_type]:
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1:
                    break
                start_positions.append(pos)
                pos += 1
        
        start_positions.sort()
        
        # Với mỗi điểm bắt đầu, tìm EOF marker
        for start in start_positions:
            end = data.find(self.EOF_MARKERS[file_type], start)
            if end != -1:
                # Thêm độ dài của EOF marker
                end += len(self.EOF_MARKERS[file_type])
                boundaries.append((start, end))
                
        return boundaries

    def validate_image(self, data, file_type):
        """Kiểm tra tính hợp lệ của dữ liệu ảnh"""
        if file_type == 'jpg':
            # Kiểm tra basic JPEG structure
            return data[0:2] == b'\xFF\xD8' and data[-2:] == b'\xFF\xD9'
        elif file_type == 'png':
            # Kiểm tra PNG signature và IEND chunk
            return (data.startswith(b'\x89PNG\r\n\x1a\n') and
                    data.endswith(b'IEND\xAE\x42\x60\x82'))
        return False

    def save_recovered_file(self, data, file_type):
        """Lưu file đã phục hồi"""
        filename = f"recovered_{self.recovered_files}.{file_type}"
        try:
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"Da phuc hoi: {filename}")
            self.recovered_files += 1
            return True
        except IOError as e:
            print(f"Loi khi luu file {filename}: {e}")
            return False

    def recover_images(self):
        """Hàm chính để phục hồi ảnh"""
        print("Bat dau qua trinh phuc hoi anh...")
        
        # Đọc dữ liệu từ volume
        volume_data = self.read_volume()
        if volume_data is None:
            return
        
        # Phục hồi từng loại file
        for file_type in ['jpg', 'png']:
            print(f"\nTim kiem cac file {file_type.upper()}...")
            boundaries = self.find_file_boundaries(volume_data, file_type)
            
            for start, end in boundaries:
                image_data = volume_data[start:end]
                
                # Kiểm tra tính hợp lệ của file
                if self.validate_image(image_data, file_type):
                    self.save_recovered_file(image_data, file_type)
        
        print(f"\nDa hoan thanh. Tong so file phuc hoi: {self.recovered_files}")

def create_sample_images():
    """Tạo một số file ảnh mẫu"""
    # Tạo một JPEG file đơn giản
    jpeg_data = (
        b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46'  # SOI và JFIF marker
        b'\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'  # JFIF header
        b'\xFF\xDB\x00\x43\x00'  # DQT marker
        b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07'  # Quantization table
        b'\xFF\xC0\x00\x11\x08\x00\x10\x00\x10\x03'  # SOF marker
        b'\xFF\xC4\x00\x1F\x00'  # DHT marker
        b'\xFF\xDA'  # SOS marker
        b'\x00\x08\x01\x01\x00'  # Scan data
        b'\xFF\xD9'  # EOI marker
    )
    
    # Tạo một PNG file đơn giản
    png_data = (
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'  # PNG signature
        b'\x00\x00\x00\x0D\x49\x48\x44\x52'  # IHDR chunk
        b'\x00\x00\x00\x10\x00\x00\x00\x10'  # Width & Height
        b'\x08\x06\x00\x00\x00'  # Bit depth, color type, etc
        b'\x1F\xF3\xFF\x61'  # CRC
        b'\x00\x00\x00\x00\x49\x45\x4E\x44\xAE\x42\x60\x82'  # IEND chunk
    )
    
    # Tạo volume mẫu chứa các file ảnh
    with open('Image00.Vol', 'wb') as f:
        # Thêm một số dữ liệu rác ở đầu
        f.write(b'\x00' * 1024)
        
        # Thêm JPEG đầu tiên
        f.write(jpeg_data)
        
        # Thêm một số dữ liệu rác ở giữa
        f.write(b'\xFF' * 512)
        
        # Thêm PNG
        f.write(png_data)
        
        # Thêm JPEG thứ hai
        f.write(jpeg_data)
        
        # Thêm một số dữ liệu rác ở cuối
        f.write(b'\x00' * 1024)

def cleanup_files():
    """Dọn dẹp các file test"""
    files_to_remove = ['Image00.Vol'] + [f for f in os.listdir() if f.startswith('recovered_')]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

def run_demo():
    """Chạy demo hoàn chỉnh"""
    print("=== BAT DAU DEMO PHUC HOI ANH ===")
    
    # Dọn dẹp các file cũ
    print("\nDon dep cac file cu...")
    cleanup_files()
    
    # Tạo dữ liệu test
    print("Tao volume test voi cac file anh mau...")
    create_sample_images()
    
    # Kiểm tra kích thước volume
    size = os.path.getsize('Image00.Vol')
    print(f"Da tao Image00.Vol (kich thuoc: {size} bytes)")
    
    print("\nBat dau qua trinh phuc hoi...")
    
    # Chạy chương trình phục hồi
    recovery = ImageRecovery('Image00.Vol')
    recovery.recover_images()
    
    # Kiểm tra kết quả
    recovered_files = [f for f in os.listdir() if f.startswith('recovered_')]
    print("\nKet qua:")
    for file in recovered_files:
        size = os.path.getsize(file)
        print(f"- {file} ({size} bytes)")
    
    print("\n=== DEMO HOAN TAT ===")

if __name__ == "__main__":
    run_demo()