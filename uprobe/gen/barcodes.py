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
