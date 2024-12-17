import os
import struct
import binascii
import sys
import codecs
import shutil
import random

if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.platform.startswith('win'):
        os.system('chcp 65001')

class ImageCorruptor:
    def __init__(self, source_file):
        self.source_file = source_file
    
    def corrupt_file(self, output_volume):
        try:
            with open(self.source_file, 'rb') as src:
                file_data = src.read()
                
            with open(output_volume, 'wb') as vol:
                vol.write(os.urandom(1024))
                vol.write(file_data)
                vol.write(os.urandom(512))
                vol.write(file_data[:len(file_data)//2])
                vol.write(os.urandom(1024))
            
            return True
        except Exception as e:
            print(f"Error creating corrupted volume: {e}")
            return False

class ImageRecovery:
    # Extended signatures for better detection
    SIGNATURES = {
        'jpg': (
            b'\xFF\xD8\xFF\xE0',  # JFIF
            b'\xFF\xD8\xFF\xE1',  # Exif
            b'\xFF\xD8\xFF\xDB',  # JPEG with quantization table
            b'\xFF\xD8\xFF\xEE'   # JPEG with application segment
        ),
        'png': (b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',)
    }
    
    EOF_MARKERS = {
        'jpg': b'\xFF\xD9',
        'png': b'\x49\x45\x4E\x44\xAE\x42\x60\x82'
    }

    def __init__(self, volume_path):
        self.volume_path = volume_path
        self.recovered_files = 0
        
    def read_volume(self):
        try:
            with open(self.volume_path, 'rb') as f:
                return f.read()
        except IOError as e:
            print(f"Error reading volume: {e}")
            return None

    def find_file_boundaries(self, data, file_type):
        boundaries = []
        start_positions = []
        
        # Find all possible start positions
        for sig in self.SIGNATURES[file_type]:
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1:
                    break
                start_positions.append(pos)
                pos += 1
        
        start_positions.sort()
        
        # Find corresponding end markers
        for start in start_positions:
            # Look for EOF marker within reasonable size limits
            MAX_SIZE = 20 * 1024 * 1024  # 20MB max size for reasonable images
            search_end = min(start + MAX_SIZE, len(data))
            end = data.find(self.EOF_MARKERS[file_type], start, search_end)
            
            if end != -1:
                end += len(self.EOF_MARKERS[file_type])
                boundaries.append((start, end))
        
        return boundaries

    def validate_image(self, data, file_type):
        """Enhanced image validation"""
        if len(data) < 64:  # Minimum size check
            return False
            
        if file_type == 'jpg':
            # Check JPEG structure
            if not (data[0:2] == b'\xFF\xD8' and data[-2:] == b'\xFF\xD9'):
                return False
                
            # Verify JPEG markers
            i = 2
            while i < len(data) - 2:
                if data[i] == 0xFF:
                    if data[i + 1] in [0xC0, 0xC2, 0xC4, 0xDB, 0xDD, 0xDA]:
                        return True
                    i += 2
                else:
                    i += 1
            return False
            
        elif file_type == 'png':
            # Verify PNG signature and IEND chunk
            if not (data.startswith(b'\x89PNG\r\n\x1a\n') and
                   data.endswith(b'IEND\xAE\x42\x60\x82')):
                return False
                
            # Check for essential PNG chunks
            essential_chunks = [b'IHDR', b'IDAT']
            for chunk in essential_chunks:
                if chunk not in data:
                    return False
            
            return True
            
        return False

    def save_recovered_file(self, data, file_type):
        filename = f"recovered_{self.recovered_files}.{file_type}"
        try:
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"Recovered: {filename}")
            self.recovered_files += 1
            return True
        except IOError as e:
            print(f"Error saving {filename}: {e}")
            return False

    def recover_images(self):
        print("Starting image recovery process...")
        
        volume_data = self.read_volume()
        if volume_data is None:
            return
        
        for file_type in ['jpg', 'png']:
            print(f"\nSearching for {file_type.upper()} files...")
            boundaries = self.find_file_boundaries(volume_data, file_type)
            
            for start, end in boundaries:
                image_data = volume_data[start:end]
                if self.validate_image(image_data, file_type):
                    self.save_recovered_file(image_data, file_type)
        
        print(f"\nComplete. Total files recovered: {self.recovered_files}")

def cleanup_files():
    files_to_remove = ['corrupted.vol'] + [f for f in os.listdir() if f.startswith('recovered_')]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)

def print_file_info(filepath):
    size = os.path.getsize(filepath)
    print(f"- Filename: {filepath}")
    print(f"- Size: {size} bytes")
    print(f"- Format: {os.path.splitext(filepath)[1].upper()}")

def run_demo_with_real_image(image_path):
    print("=== STARTING IMAGE RECOVERY DEMO ===")
    
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return
    
    print("\nOriginal file information:")
    print_file_info(image_path)
    
    print("\nCleaning up old files...")
    cleanup_files()
    
    print("\nCreating corrupted volume...")
    corruptor = ImageCorruptor(image_path)
    if not corruptor.corrupt_file('corrupted.vol'):
        print("Could not create corrupted volume!")
        return
    
    print("Created corrupted volume:")
    print_file_info('corrupted.vol')
    
    print("\nStarting recovery process...")
    recovery = ImageRecovery('corrupted.vol')
    recovery.recover_images()
    
    recovered_files = [f for f in os.listdir() if f.startswith('recovered_')]
    print("\nRecovery results:")
    for file in recovered_files:
        print_file_info(file)
    
    print("\n=== DEMO COMPLETE ===")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <image_file_path>")
        print("Example: python script.py image.jpg")
        sys.exit(1)
    
    run_demo_with_real_image(sys.argv[1])