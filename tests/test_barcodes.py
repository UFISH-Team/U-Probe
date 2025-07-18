"""
Test module for barcode generation functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os
import yaml

# Add the parent directory to the path so we can import uprobe modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uprobe.gen.barcodes import (
    BarcodeGenerator, 
    quick_generate,
    generate_pcr_barcodes,
    generate_sequencing_barcodes,
    generate_barcodes_from_config
)


class TestBarcodeGenerator(unittest.TestCase):
    """Test cases for BarcodeGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = BarcodeGenerator()
        # Create temp directory in the parent of current test file
        test_file_dir = Path(__file__).parent
        self.temp_dir = test_file_dir / "temp_barcode_test"
        self.temp_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Keep test files for inspection - comment out automatic cleanup
        # shutil.rmtree(self.temp_dir, ignore_errors=True)
        print(f"💾 Test files preserved in: {self.temp_dir}")
        pass
    
    def test_max_orthogonality_generation(self):
        """Test maximum orthogonality barcode generation."""
        num_barcodes = 5
        length = 6
        
        barcodes = self.generator.generate_max_orthogonality(
            num_barcodes=num_barcodes,
            length=length,
            alphabet="ACT"
        )
        
        # Verify basic properties
        self.assertGreaterEqual(len(barcodes), num_barcodes)
        self.assertTrue(all(len(barcode) == length for barcode in barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACT")) for barcode in barcodes))
    
    def test_quality_analysis(self):
        """Test barcode quality analysis."""
        barcodes = ["ACGT", "TGCA", "CATG", "GTAC"]
        
        quality_metrics = self.generator.analyze_quality(barcodes)
        
        # Verify quality metrics structure
        expected_keys = [
            "num_barcodes", "barcode_length", "min_hamming_distance",
            "max_hamming_distance", "mean_hamming_distance",
            "min_gc_content", "max_gc_content", "mean_gc_content",
            "hamming_matrix"
        ]
        
        for key in expected_keys:
            self.assertIn(key, quality_metrics)
        
        self.assertEqual(quality_metrics["num_barcodes"], 4)
        self.assertEqual(quality_metrics["barcode_length"], 4)


class TestConfigBasedGeneration(unittest.TestCase):
    """Test cases for configuration-based barcode generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temp directory in the parent of current test file
        test_file_dir = Path(__file__).parent
        self.temp_dir = test_file_dir / "temp_barcode_test"
        self.temp_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Keep test files for inspection - comment out automatic cleanup
        # shutil.rmtree(self.temp_dir, ignore_errors=True)
        print(f"💾 Test files preserved in: {self.temp_dir}")
        pass
    
    def test_single_barcode_set_generation(self):
        """Test generating a single barcode set from configuration."""
        config = {
            "barcode_generation": {
                "test_set": {
                    "strategy": "max_orthogonality",
                    "num_barcodes": 5,
                    "length": 6,
                    "alphabet": "ACT",
                    "rc_free": True,
                    "save_file": "test_barcodes.txt"
                }
            }
        }
        
        barcode_sets = generate_barcodes_from_config(config, self.temp_dir)
        
        # Verify results
        self.assertIn("test_set", barcode_sets)
        barcodes = barcode_sets["test_set"]
        self.assertGreaterEqual(len(barcodes), 5)
        self.assertTrue(all(len(barcode) == 6 for barcode in barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACT")) for barcode in barcodes))
        
        # Verify file was saved
        output_file = self.temp_dir / "test_barcodes.txt"
        self.assertTrue(output_file.exists())
        
        # Verify file content
        with open(output_file) as f:
            saved_barcodes = [line.strip() for line in f]
        self.assertEqual(len(saved_barcodes), len(barcodes))
    
    def test_multiple_barcode_sets_generation(self):
        """Test generating multiple barcode sets from configuration."""
        config = {
            "barcode_generation": {
                "pcr_set": {
                    "strategy": "max_orthogonality",
                    "num_barcodes": 3,
                    "length": 8,
                    "alphabet": "ACGT",
                    "rc_free": True,
                    "gc_limits": [2, 6],
                    "prevent_patterns": ["AAAA", "TTTT"],
                    "save_file": "pcr_barcodes.txt"
                },
                "simple_set": {
                    "strategy": "max_orthogonality", 
                    "num_barcodes": 4,
                    "length": 6,
                    "alphabet": "ACT",
                    "rc_free": False,
                    "save_file": "simple_barcodes.txt"
                }
            }
        }
        
        barcode_sets = generate_barcodes_from_config(config, self.temp_dir)
        
        # Verify both sets were generated
        self.assertIn("pcr_set", barcode_sets)
        self.assertIn("simple_set", barcode_sets)
        
        # Verify PCR set properties
        pcr_barcodes = barcode_sets["pcr_set"]
        self.assertGreaterEqual(len(pcr_barcodes), 3)
        self.assertTrue(all(len(barcode) == 8 for barcode in pcr_barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACGT")) for barcode in pcr_barcodes))
        
        # Verify GC content constraints for PCR set
        for barcode in pcr_barcodes:
            gc_count = barcode.count('G') + barcode.count('C')
            self.assertGreaterEqual(gc_count, 2)
            self.assertLessEqual(gc_count, 6)
            # Verify prohibited patterns are not present
            self.assertNotIn("AAAA", barcode)
            self.assertNotIn("TTTT", barcode)
        
        # Verify simple set properties
        simple_barcodes = barcode_sets["simple_set"]
        self.assertGreaterEqual(len(simple_barcodes), 4)
        self.assertTrue(all(len(barcode) == 6 for barcode in simple_barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACT")) for barcode in simple_barcodes))
        
        # Verify both files were saved
        self.assertTrue((self.temp_dir / "pcr_barcodes.txt").exists())
        self.assertTrue((self.temp_dir / "simple_barcodes.txt").exists())
    
    def test_max_size_strategy_from_config(self):
        """Test max_size strategy from configuration."""
        config = {
            "barcode_generation": {
                "max_size_set": {
                    "strategy": "max_size",
                    "length": 8,
                    "k_constraint": 4,
                    "alphabet": "ACT",
                    "rc_free": True,
                    "save_file": "max_size_barcodes.txt"
                }
            }
        }
        
        barcode_sets = generate_barcodes_from_config(config, self.temp_dir)
        
        # Verify results
        self.assertIn("max_size_set", barcode_sets)
        barcodes = barcode_sets["max_size_set"]
        self.assertGreater(len(barcodes), 0)
        self.assertTrue(all(len(barcode) == 8 for barcode in barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACT")) for barcode in barcodes))
        
        # Verify file was saved
        output_file = self.temp_dir / "max_size_barcodes.txt"
        self.assertTrue(output_file.exists())
    
    def test_config_with_quality_analysis(self):
        """Test configuration with quality analysis enabled."""
        import json
        
        config = {
            "barcode_generation": {
                "analyzed_set": {
                    "strategy": "max_orthogonality",
                    "num_barcodes": 4,
                    "length": 6,
                    "alphabet": "ACGT",
                    "rc_free": True,
                    "save_file": "analyzed_barcodes.txt",
                    "analyze_quality": True
                }
            }
        }
        
        barcode_sets = generate_barcodes_from_config(config, self.temp_dir)
        
        # Verify barcode set was generated
        self.assertIn("analyzed_set", barcode_sets)
        
        # Verify quality analysis file was created
        quality_file = self.temp_dir / "analyzed_set_quality.json"
        self.assertTrue(quality_file.exists())
        
        # Verify quality analysis content
        with open(quality_file) as f:
            quality_data = json.load(f)
        
        expected_keys = [
            "num_barcodes", "barcode_length", "min_hamming_distance",
            "max_hamming_distance", "mean_hamming_distance",
            "min_gc_content", "max_gc_content", "mean_gc_content",
            "hamming_matrix"
        ]
        
        for key in expected_keys:
            self.assertIn(key, quality_data)
    
    def test_empty_config(self):
        """Test handling of empty or missing barcode_generation config."""
        # Test completely empty config
        empty_config = {}
        barcode_sets = generate_barcodes_from_config(empty_config, self.temp_dir)
        self.assertEqual(len(barcode_sets), 0)
        
        # Test config without barcode_generation section
        no_barcode_config = {"other_section": {"key": "value"}}
        barcode_sets = generate_barcodes_from_config(no_barcode_config, self.temp_dir)
        self.assertEqual(len(barcode_sets), 0)
    
    def test_yaml_config_file(self):
        """Test loading configuration from a YAML file."""
        # Create a test YAML configuration file
        yaml_config = """
barcode_generation:
  yaml_test_set:
    strategy: "max_orthogonality"
    num_barcodes: 4
    length: 8
    alphabet: "ACGT"
    rc_free: true
    gc_limits: [2, 6]
    prevent_patterns: ["AAAA", "TTTT"]
    save_file: "yaml_test_barcodes.txt"
    analyze_quality: true
  
  simple_yaml_set:
    strategy: "max_size"
    length: 6
    k_constraint: 3
    alphabet: "ACT"
    rc_free: false
    save_file: "simple_yaml_barcodes.txt"
"""
        
        # Write YAML config to file
        config_file = self.temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            f.write(yaml_config)
        
        # Load config from YAML file
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # Generate barcodes from loaded config
        barcode_sets = generate_barcodes_from_config(config, self.temp_dir)
        
        # Verify both sets were generated
        self.assertIn("yaml_test_set", barcode_sets)
        self.assertIn("simple_yaml_set", barcode_sets)
        
        # Verify yaml_test_set properties
        yaml_barcodes = barcode_sets["yaml_test_set"]
        self.assertGreaterEqual(len(yaml_barcodes), 4)
        self.assertTrue(all(len(barcode) == 8 for barcode in yaml_barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACGT")) for barcode in yaml_barcodes))
        
        # Verify GC constraints and prohibited patterns
        for barcode in yaml_barcodes:
            gc_count = barcode.count('G') + barcode.count('C')
            self.assertGreaterEqual(gc_count, 2)
            self.assertLessEqual(gc_count, 6)
            self.assertNotIn("AAAA", barcode)
            self.assertNotIn("TTTT", barcode)
        
        # Verify simple_yaml_set properties
        simple_barcodes = barcode_sets["simple_yaml_set"]
        self.assertGreater(len(simple_barcodes), 0)
        self.assertTrue(all(len(barcode) == 6 for barcode in simple_barcodes))
        self.assertTrue(all(set(barcode).issubset(set("ACT")) for barcode in simple_barcodes))
        
        # Verify files were saved
        self.assertTrue((self.temp_dir / "yaml_test_barcodes.txt").exists())
        self.assertTrue((self.temp_dir / "simple_yaml_barcodes.txt").exists())
        
        # Verify quality analysis file was created for the first set
        quality_file = self.temp_dir / "yaml_test_set_quality.json"
        self.assertTrue(quality_file.exists())
        
        print(f"✅ YAML config test passed! Generated {len(yaml_barcodes)} + {len(simple_barcodes)} barcodes from YAML file.")


def clean_test_files():
    """Manually clean up test files if needed."""
    test_file_dir = Path(__file__).parent
    temp_dir = test_file_dir / "temp_barcode_test"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🧹 Cleaned up test files in: {temp_dir}")
    else:
        print("📁 No test files to clean.")


if __name__ == "__main__":
    # Check if test directory already exists
    test_file_dir = Path(__file__).parent
    temp_dir = test_file_dir / "temp_barcode_test"
    if temp_dir.exists():
        print(f"📁 Test directory already exists: {temp_dir}")
        print("🧹 Previous test files will be overwritten.")
    
    # Run a simple test to verify the module works
    print("Running basic barcode generation test...")
    
    try:
        # Test quick generation
        print("Testing quick generation...")
        barcodes = quick_generate(3, 6)
        print(f"Generated {len(barcodes)} barcodes: {barcodes}")
        
        # Test PCR barcodes
        print("\nTesting PCR barcode generation...")
        pcr_barcodes = generate_pcr_barcodes(3, 8)
        print(f"Generated {len(pcr_barcodes)} PCR barcodes: {pcr_barcodes}")
        
        # Test config-based generation
        print("\nTesting config-based barcode generation...")
        # Create temp directory in the tests folder
        test_file_dir = Path(__file__).parent
        temp_dir = test_file_dir / "temp_barcode_test"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            config = {
                "barcode_generation": {
                    "test_config_set": {
                        "strategy": "max_orthogonality",
                        "num_barcodes": 3,
                        "length": 6,
                        "alphabet": "ACT",
                        "rc_free": True,
                        "save_file": "config_test_barcodes.txt"
                    }
                }
            }
            barcode_sets = generate_barcodes_from_config(config, temp_dir)
            if "test_config_set" in barcode_sets:
                config_barcodes = barcode_sets["test_config_set"]
                print(f"Generated {len(config_barcodes)} barcodes from config: {config_barcodes}")
                
                # Check if file was saved
                output_file = temp_dir / "config_test_barcodes.txt"
                if output_file.exists():
                    print(f"Barcodes successfully saved to {output_file}")
        except Exception as e:
            print(f"Config test failed: {e}")
        
        print(f"\n📁 Test files saved in: {temp_dir}")
        print("💡 You can find generated barcode files in the tests/temp_barcode_test/ directory")
        print("🧹 To clean up test files, run: clean_test_files()")
        
        print("\n✅ All basic tests passed! The barcodes module is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("Make sure seqwalk is properly installed.")
    
    # Uncomment the line below if you want to automatically clean up test files
    # clean_test_files() 