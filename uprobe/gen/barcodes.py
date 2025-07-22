"""
Barcode generation module using seqwalk for orthogonal DNA sequence design.
"""

import typing as T
from pathlib import Path
from seqwalk import design, analysis
import numpy as np
from ..utils import get_logger, reverse_complement

logger = get_logger(__name__)


class BarcodeGenerator:
    """
    Barcode generator class that provides different strategies for generating
    orthogonal DNA barcodes using seqwalk.
    """
    
    def __init__(self, strategy: str = "max_orthogonality"):
        """
        Initialize the barcode generator.
        
        Args:
            strategy: Generation strategy ("max_orthogonality" or "max_size")
        """
        self.strategy = strategy
        self.generated_barcodes: T.List[str] = []
        
    def generate_max_orthogonality(
        self,
        num_barcodes: int,
        length: int,
        alphabet: str = "ACT",  # Default 3-letter alphabet excluding G
        rc_free: bool = True,
        gc_limits: T.Optional[T.Tuple[int, int]] = None,
        prevent_patterns: T.Optional[T.List[str]] = None
    ) -> T.List[str]:
        """
        Generate barcodes with maximum orthogonality for given number and length.
        
        Args:
            num_barcodes: Number of barcodes to generate
            length: Length of each barcode
            alphabet: Allowable nucleotide alphabet (default: "ACT")
            rc_free: Whether to prevent reverse complementary sequences
            gc_limits: Tuple of (min_gc, max_gc) for GC content constraints
            prevent_patterns: List of patterns to prevent in sequences
            
        Returns:
            List of generated barcode sequences
        """
        logger.info(f"Generating {num_barcodes} barcodes of length {length} with max orthogonality")
        logger.info(f"Parameters: alphabet={alphabet}, RC-free={rc_free}, GC limits={gc_limits}")
        
        try:
            # Generate barcodes using seqwalk
            barcodes = design.max_orthogonality(
                num_barcodes,
                length,
                alphabet=alphabet,
                RCfree=rc_free,
                GClims=gc_limits
            )
            
            # Apply additional pattern filters if specified
            if prevent_patterns:
                barcodes = self._filter_patterns(barcodes, prevent_patterns)
            
            self.generated_barcodes = barcodes
            logger.info(f"Successfully generated {len(barcodes)} barcodes")
            return barcodes
            
        except Exception as e:
            logger.error(f"Error generating barcodes: {e}")
            raise
    
    def generate_max_size(
        self,
        length: int,
        k_constraint: int,
        alphabet: str = "ACT",
        rc_free: bool = True,
        gc_limits: T.Optional[T.Tuple[int, int]] = None,
        prevent_patterns: T.Optional[T.List[str]] = None
    ) -> T.List[str]:
        """
        Generate maximum number of barcodes with given orthogonality constraint.
        
        Args:
            length: Length of each barcode
            k_constraint: Minimum substring length for uniqueness (SSM k value)
            alphabet: Allowable nucleotide alphabet
            rc_free: Whether to prevent reverse complementary sequences
            gc_limits: Tuple of (min_gc, max_gc) for GC content constraints
            prevent_patterns: List of patterns to prevent in sequences
            
        Returns:
            List of generated barcode sequences
        """
        logger.info(f"Generating max size barcode library with k={k_constraint}, length={length}")
        logger.info(f"Parameters: alphabet={alphabet}, RC-free={rc_free}, GC limits={gc_limits}")
        
        try:
            # Generate barcodes using seqwalk
            barcodes = design.max_size(
                length,
                k_constraint,
                alphabet=alphabet,
                RCfree=rc_free,
                GClims=gc_limits
            )
            
            # Apply additional pattern filters if specified
            if prevent_patterns:
                barcodes = self._filter_patterns(barcodes, prevent_patterns)
            
            self.generated_barcodes = barcodes
            logger.info(f"Successfully generated {len(barcodes)} barcodes with k={k_constraint}")
            return barcodes
            
        except Exception as e:
            logger.error(f"Error generating barcodes: {e}")
            raise
    
    def _filter_patterns(self, barcodes: T.List[str], prevent_patterns: T.List[str]) -> T.List[str]:
        """
        Filter out barcodes containing specified patterns.
        
        Args:
            barcodes: List of barcode sequences
            prevent_patterns: List of patterns to filter out
            
        Returns:
            Filtered list of barcode sequences
        """
        filtered_barcodes = []
        removed_count = 0
        
        for barcode in barcodes:
            contains_pattern = False
            for pattern in prevent_patterns:
                if pattern in barcode or pattern in reverse_complement(barcode):
                    contains_pattern = True
                    removed_count += 1
                    break
            
            if not contains_pattern:
                filtered_barcodes.append(barcode)
        
        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} barcodes containing prohibited patterns")
        
        return filtered_barcodes
    
    def analyze_quality(self, barcodes: T.Optional[T.List[str]] = None) -> dict:
        """
        Analyze the quality of generated barcodes.
        
        Args:
            barcodes: List of barcodes to analyze (uses last generated if None)
            
        Returns:
            Dictionary containing quality metrics
        """
        if barcodes is None:
            barcodes = self.generated_barcodes
        
        if not barcodes:
            logger.warning("No barcodes to analyze")
            return {}
        
        logger.info(f"Analyzing quality of {len(barcodes)} barcodes")
        
        # Calculate Hamming distance matrix
        hamming_matrix = analysis.hamming_matrix(barcodes)
        
        # Calculate statistics
        min_hamming = np.min(hamming_matrix[hamming_matrix > 0])
        max_hamming = np.max(hamming_matrix)
        mean_hamming = np.mean(hamming_matrix[hamming_matrix > 0])
        
        # Calculate GC content statistics
        gc_contents = [self._calculate_gc_content(barcode) for barcode in barcodes]
        
        quality_metrics = {
            "num_barcodes": len(barcodes),
            "barcode_length": len(barcodes[0]) if barcodes else 0,
            "min_hamming_distance": min_hamming,
            "max_hamming_distance": max_hamming,
            "mean_hamming_distance": mean_hamming,
            "min_gc_content": min(gc_contents),
            "max_gc_content": max(gc_contents),
            "mean_gc_content": np.mean(gc_contents),
            "hamming_matrix": hamming_matrix.tolist()
        }
        
        logger.info(f"Quality analysis complete. Min Hamming distance: {min_hamming}")
        return quality_metrics
    
    def _calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content of a sequence."""
        gc_count = sequence.count('G') + sequence.count('C')
        return gc_count / len(sequence) if sequence else 0.0
    
    def save_barcodes(self, filepath: Path, barcodes: T.Optional[T.List[str]] = None) -> None:
        """
        Save barcodes to a file.
        
        Args:
            filepath: Path to save the barcodes
            barcodes: List of barcodes to save (uses last generated if None)
        """
        if barcodes is None:
            barcodes = self.generated_barcodes
        
        if not barcodes:
            logger.warning("No barcodes to save")
            return
        
        with open(filepath, 'w') as f:
            for barcode in barcodes:
                f.write(f"{barcode}\n")
        
        logger.info(f"Saved {len(barcodes)} barcodes to {filepath}")


def load_precomputed_library(library_name: str) -> T.List[str]:
    """
    Load a precomputed orthogonal library from seqwalk.
    
    Args:
        library_name: Name of the library to load (e.g., "kishi2018")
        
    Returns:
        List of sequences from the library
    """
    try:
        from seqwalk import io
        library = io.load_library(library_name)
        logger.info(f"Loaded precomputed library '{library_name}' with {len(library)} sequences")
        return library
    except Exception as e:
        logger.error(f"Error loading library '{library_name}': {e}")
        raise


def generate_barcodes_from_config(config: dict, workdir: Path) -> T.Dict[str, T.List[str]]:
    """
    Generate barcodes based on configuration dictionary.
    
    Args:
        config: Configuration dictionary with barcode generation parameters
        workdir: Working directory for output files
        
    Returns:
        Dictionary mapping barcode set names to generated sequences
    """
    barcode_sets = {}
    
    if 'barcode_generation' not in config:
        logger.warning("No barcode_generation configuration found")
        return barcode_sets
    
    barcode_config = config['barcode_generation']
    
    for set_name, set_config in barcode_config.items():
        logger.info(f"Generating barcode set: {set_name}")
        
        generator = BarcodeGenerator(strategy=set_config.get('strategy', 'max_orthogonality'))
        
        # Extract parameters
        strategy = set_config.get('strategy', 'max_orthogonality')
        
        # Generate barcodes based on strategy
        if strategy == 'precomputed':
            library_name = set_config['library_name']
            barcodes = load_precomputed_library(library_name)
        elif strategy == 'max_orthogonality':
            # Extract parameters for max_orthogonality strategy
            num_barcodes = set_config['num_barcodes']
            length = set_config['length']
            alphabet = set_config.get('alphabet', 'ACT')
            rc_free = set_config.get('rc_free', True)
            gc_limits = set_config.get('gc_limits')
            prevent_patterns = set_config.get('prevent_patterns')
            
            barcodes = generator.generate_max_orthogonality(
                num_barcodes=num_barcodes,
                length=length,
                alphabet=alphabet,
                rc_free=rc_free,
                gc_limits=gc_limits,
                prevent_patterns=prevent_patterns
            )
        elif strategy == 'max_size':
            # Extract parameters for max_size strategy
            length = set_config['length']
            k_constraint = set_config['k_constraint']
            alphabet = set_config.get('alphabet', 'ACT')
            rc_free = set_config.get('rc_free', True)
            gc_limits = set_config.get('gc_limits')
            prevent_patterns = set_config.get('prevent_patterns')
            
            barcodes = generator.generate_max_size(
                length=length,
                k_constraint=k_constraint,
                alphabet=alphabet,
                rc_free=rc_free,
                gc_limits=gc_limits,
                prevent_patterns=prevent_patterns
            )
        else:
            logger.error(f"Unknown strategy: {strategy}")
            continue
        
        # Save barcodes if requested
        if set_config.get('save_file'):
            output_file = workdir / set_config['save_file']
            generator.save_barcodes(output_file, barcodes)
        
        # Analyze quality if requested
        if set_config.get('analyze_quality', False):
            quality_metrics = generator.analyze_quality(barcodes)
            # Save quality metrics
            import json
            quality_file = workdir / f"{set_name}_quality.json"
            with open(quality_file, 'w') as f:
                json.dump(quality_metrics, f, indent=2)
            logger.info(f"Quality metrics saved to {quality_file}")
        
        barcode_sets[set_name] = barcodes
    
    return barcode_sets


# Convenience functions for common use cases
def quick_generate(num_barcodes: int, length: int, **kwargs) -> T.List[str]:
    """
    Quick barcode generation with sensible defaults.
    
    Args:
        num_barcodes: Number of barcodes to generate
        length: Length of each barcode
        **kwargs: Additional parameters for generation
        
    Returns:
        List of generated barcode sequences
    """
    generator = BarcodeGenerator()
    return generator.generate_max_orthogonality(num_barcodes, length, **kwargs)


def generate_pcr_barcodes(num_barcodes: int, length: int = 8) -> T.List[str]:
    """
    Generate barcodes optimized for PCR amplification.
    
    Args:
        num_barcodes: Number of barcodes to generate
        length: Length of each barcode (default: 8)
        
    Returns:
        List of PCR-optimized barcode sequences
    """
    # PCR-optimized parameters: 4-letter alphabet, RC-free, balanced GC content
    generator = BarcodeGenerator()
    return generator.generate_max_orthogonality(
        num_barcodes=num_barcodes,
        length=length,
        alphabet="ACGT",
        rc_free=True,
        gc_limits=(length//4, 3*length//4),  # 25-75% GC content
        prevent_patterns=["AAAA", "TTTT", "CCCC", "GGGG"]  # Prevent homopolymers
    )


def generate_sequencing_barcodes(num_barcodes: int, length: int = 12) -> T.List[str]:
    """
    Generate barcodes optimized for sequencing applications.
    
    Args:
        num_barcodes: Number of barcodes to generate
        length: Length of each barcode (default: 12)
        
    Returns:
        List of sequencing-optimized barcode sequences
    """
    # Sequencing-optimized parameters: longer length, strict constraints
    generator = BarcodeGenerator()
    return generator.generate_max_orthogonality(
        num_barcodes=num_barcodes,
        length=length,
        alphabet="ACGT",
        rc_free=True,
        gc_limits=(length//3, 2*length//3),  # 33-67% GC content
        prevent_patterns=["AAA", "TTT", "CCC", "GGG"]  # Prevent short homopolymers
    )
