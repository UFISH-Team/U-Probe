"""
Barcode generation using seqwalk for orthogonal DNA sequence design.
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
        if barcodes is None:
            barcodes = self.generated_barcodes
        
        if not barcodes:
            logger.warning("No barcodes to save")
            return
        
        with open(filepath, 'w') as f:
            for barcode in barcodes:
                f.write(f"{barcode}\n")
        
        logger.info(f"Saved {len(barcodes)} barcodes to {filepath}")


# Convenience functions for common use cases
def quick_generate(num_barcodes: int, length: int, **kwargs) -> T.List[str]:
    """
    Quick barcode generation with sensible defaults.
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
