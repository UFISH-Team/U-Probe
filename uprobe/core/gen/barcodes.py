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

    def __init__(self, strategy: str = "max_orthogonality"): # "max_orthogonality" or "max_size"
        self.strategy = strategy
        self.generated_barcodes: T.List[str] = []
        
    def generate_max_orthogonality(
        self,
        num_barcodes: int,
        length: int,
        alphabet: str = "ACT", 
        rc_free: bool = True,
        gc_limits: T.Optional[T.Tuple[int, int]] = None,
        prevent_patterns: T.Optional[T.List[str]] = None
    ) -> T.List[str]:
        gclims_abs = None
        if gc_limits:
            min_gc_pct, max_gc_pct = gc_limits
            gclims_abs = (
                int(np.floor(min_gc_pct / 100 * length)),
                int(np.ceil(max_gc_pct / 100 * length))
            )
        try:
            barcodes = design.max_orthogonality(
                num_barcodes,
                length,
                alphabet=alphabet,
                RCfree=rc_free,
                GClims=gclims_abs
            )
            if len(barcodes) > num_barcodes:
                barcodes = barcodes[:num_barcodes]
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
        try:
            barcodes = design.max_size(
                length,
                k_constraint,
                alphabet=alphabet,
                RCfree=rc_free,
                GClims=gc_limits
            )
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

def quick_generate(num_barcodes: int, length: int, **kwargs) -> T.List[str]:
    generator = BarcodeGenerator()
    return generator.generate_max_orthogonality(num_barcodes, length, **kwargs)
