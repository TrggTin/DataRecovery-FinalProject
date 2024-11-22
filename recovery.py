import os
import struct
import binascii

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
            print(f"Lỗi khi đọc volume: {e}")
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
            print(f"Đã phục hồi: {filename}")
            self.recovered_files += 1
            return True
        except IOError as e:
            print(f"Lỗi khi lưu file {filename}: {e}")
            return False

    def recover_images(self):
        """Hàm chính để phục hồi ảnh"""
        print("Bắt đầu quá trình phục hồi ảnh...")
        
        # Đọc dữ liệu từ volume
        volume_data = self.read_volume()
        if volume_data is None:
            return
        
        # Phục hồi từng loại file
        for file_type in ['jpg', 'png']:
            print(f"\nTìm kiếm các file {file_type.upper()}...")
            boundaries = self.find_file_boundaries(volume_data, file_type)
            
            for start, end in boundaries:
                image_data = volume_data[start:end]
                
                # Kiểm tra tính hợp lệ của file
                if self.validate_image(image_data, file_type):
                    self.save_recovered_file(image_data, file_type)
        
        print(f"\nĐã hoàn thành. Tổng số file phục hồi: {self.recovered_files}")

def main():
    volume_path = "Image00.Vol"
    if not os.path.exists(volume_path):
        print(f"Không tìm thấy file {volume_path}")
        return
    
    recovery = ImageRecovery(volume_path)
    recovery.recover_images()

if __name__ == "__main__":
    main()