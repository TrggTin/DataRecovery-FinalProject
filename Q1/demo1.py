import os
import shutil
import sys
import codecs

# Thiết lập encoding cho stdout để hỗ trợ tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.platform.startswith('win'):
        os.system('chcp 65001')

def create_sample_images():
    """Tao mot so file anh mau"""
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
    """Don dep cac file test"""
    files_to_remove = ['Image00.Vol'] + [f for f in os.listdir() if f.startswith('recovered_')]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

def run_demo():
    """Chay demo hoan chinh"""
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
    
    # Import và chạy chương trình phục hồi
    from image_recovery import ImageRecovery
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