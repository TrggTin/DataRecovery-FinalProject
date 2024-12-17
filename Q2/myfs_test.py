import unittest
import os
import tempfile
import time
import random
from myfs import MyFS, SmartOTP  # Assuming the previous implementation is in myfs.py

class TestMyFSFileSystem(unittest.TestCase):
    def setUp(self):
        """Set up test environment with temporary volumes"""
        self.temp_dir = tempfile.mkdtemp()
        self.volume_x_path = os.path.join(self.temp_dir, 'MyFS.Dat')
        self.volume_y_path = os.path.join(self.temp_dir, 'MyFS_Metadata.dat')
        self.myfs = MyFS(self.volume_x_path, self.volume_y_path)
        self.system_password = 'test_password_123'

    def tearDown(self):
        """Clean up temporary files after each test"""
        if os.path.exists(self.volume_x_path):
            os.remove(self.volume_x_path)
        if os.path.exists(self.volume_y_path):
            os.remove(self.volume_y_path)

    def test_create_myfs(self):
        """Test MyFS volume creation"""
        result = self.myfs.create_myfs(self.system_password)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.volume_x_path))
        self.assertTrue(os.path.exists(self.volume_y_path))

    def test_system_password_change(self):
        """Test changing system password"""
        # First create the MyFS
        self.myfs.create_myfs(self.system_password)
        
        # Change password
        new_password = 'new_test_password_456'
        self.myfs.change_system_password(self.system_password, new_password)
        
        # Verify password change (this would require additional method in MyFS)
        # For now, we'll just ensure no exception is raised

    def test_file_import_limits(self):
        """Test file import limitations"""
        self.myfs.create_myfs(self.system_password)
        
        # Create test files
        test_files = []
        for i in range(100):  # Try to exceed 99 file limit
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(f'Test content {i}')
                test_files.append(temp_file.name)
        
        # Try importing files
        imported_count = 0
        for file_path in test_files:
            try:
                self.myfs.import_file(file_path)
                imported_count += 1
            except ValueError:
                break
        
        self.assertEqual(imported_count, 99)  # Should not exceed 99 files

    def test_large_file_import(self):
        """Test large file import warning"""
        self.myfs.create_myfs(self.system_password)
        
        # Create a large file (> 100MB)
        large_file_path = os.path.join(self.temp_dir, 'large_file.bin')
        with open(large_file_path, 'wb') as f:
            f.write(os.urandom(150 * 1024 * 1024))  # 150MB file
        
        # Import should work but with a warning
        try:
            result = self.myfs.import_file(large_file_path)
            self.assertTrue(result)
        except Exception as e:
            self.fail(f"Large file import failed: {e}")

    def test_dynamic_password_mechanism(self):
        """Test dynamic password verification mechanism"""
        # Mock the input mechanism for testing
        def mock_input(prompt):
            x = 1234  # predefined test input
            return str(SmartOTP.generate_otp(x))
        
        # Temporarily replace input
        original_input = __builtins__.get('input')
        __builtins__['input'] = mock_input
        
        try:
            result = self.myfs.check_dynamic_password()
            self.assertTrue(result)
        finally:
            # Restore original input
            __builtins__['input'] = original_input

    def test_file_encryption(self):
        """Test file import with optional encryption"""
        self.myfs.create_myfs(self.system_password)
        
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, 'encrypted_test.txt')
        with open(test_file_path, 'w') as f:
            f.write('Sensitive information')
        
        # Import with file-level encryption
        file_password = 'file_specific_password'
        result = self.myfs.import_file(test_file_path, file_password)
        self.assertTrue(result)

    def test_metadata_preservation(self):
        """Test metadata preservation during import"""
        self.myfs.create_myfs(self.system_password)
        
        # Create a test file with known metadata
        test_file_path = os.path.join(self.temp_dir, 'metadata_test.txt')
        with open(test_file_path, 'w') as f:
            f.write('Metadata test content')
        
        # Import file
        self.myfs.import_file(test_file_path)
        
        # Check if metadata is preserved
        file_name = os.path.basename(test_file_path)
        file_metadata = self.myfs.metadata.files.get(file_name)
        
        self.assertIsNotNone(file_metadata)
        self.assertEqual(file_metadata['original_path'], test_file_path)
        self.assertIn('import_time', file_metadata)
        self.assertIn('size', file_metadata)

def run_tests():
    """Run all tests and provide a detailed report"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMyFSFileSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\nTest Summary:")
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_tests()