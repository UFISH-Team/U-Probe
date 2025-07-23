 #!/usr/bin/env python3
"""
Simple test script for barcode generation using real configuration file.
"""

import sys
import os
from pathlib import Path
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from uprobe.gen.barcodes import generate_barcodes_from_config


def test_real_config():
    """Test barcode generation using the real configuration file."""
    
    # Get paths
    test_dir = Path(__file__).parent
    config_file = test_dir / "data" / "barcode_example.yaml"
    output_dir = test_dir / "temp_barcode_test"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("🧬 Simple Barcode Generation Test")
    print("=" * 50)
    print(f"📄 Config file: {config_file}")
    print(f"📁 Output dir: {output_dir}")
    print()
    
    # Check if config file exists
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return
    
    try:
        # Load configuration from YAML file
        print("📖 Loading configuration...")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Generate barcodes from config
        print("🚀 Generating barcodes...")
        barcode_sets = generate_barcodes_from_config(config, output_dir)
        
        # Display results
        print("\n✅ Generation completed!")
        print(f"Generated {len(barcode_sets)} barcode sets:")
        
        for set_name, barcodes in barcode_sets.items():
            print(f"\n🧬 {set_name}:")
            print(f"   Count: {len(barcodes)}")
            if barcodes:
                print(f"   Length: {len(barcodes[0])}")
                print(f"   Sample: {barcodes[0]}")
                if len(barcodes) > 1:
                    print(f"   Preview: {', '.join(barcodes[:3])}")
                    if len(barcodes) > 3:
                        print(f"            ...and {len(barcodes) - 3} more")
        
        # List output files
        output_files = list(output_dir.glob("*"))
        if output_files:
            print(f"\n📁 Generated files in {output_dir}:")
            for file in sorted(output_files):
                file_size = file.stat().st_size if file.is_file() else 0
                print(f"   📄 {file.name} ({file_size} bytes)")
        
        print(f"\n💡 Check the files in: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_config()