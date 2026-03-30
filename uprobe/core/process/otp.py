import typing as t
from collections import defaultdict
from intervaltree import IntervalTree, Interval
import pysam

GenomicRegion = t.Tuple[str, int, int]
Aln = t.Tuple[str, int, int]
Block = t.Tuple[str, str, t.List[Aln]]

def parse_region(region: str) -> GenomicRegion:
    chr_, r_ = region.split(":")
    s, e = r_.split("-")
    s, e = int(s), int(e)
    return chr_, s - 1, e

def read_align_blocks(
        sam_path: str
        ) -> t.Iterable[Block]:
    def yield_cond(old, rec, block, end=False):
        res = (old is not None) and (len(block) > 0)
        if res and not end:
            res &= rec.query_name != old.query_name
        return res
    with pysam.AlignmentFile(sam_path, mode='r') as sam:
        alns = []
        old = None
        for rec in sam.fetch():
            # is correct use this to represent the align position?
            aln = rec.reference_name, rec.reference_start, rec.reference_end
            if yield_cond(old, rec, alns):
                yield old.query_name, old.query_sequence, alns
                alns = []
            if aln[0] is not None:
                alns.append(aln)
            old = rec
        if yield_cond(old, rec, alns, end=True):
            yield old.query_name, old.query_sequence, alns

def is_in_region(target_region: GenomicRegion,
                 r2: GenomicRegion) -> bool:
    r = target_region
    return (r[0] == r2[0]) & (r2[1] >= r[1]) & (r2[2] <= r[2])


def is_overlap(r1: GenomicRegion, r2: GenomicRegion) -> bool:
    if r1[0] != r2[0]:
        return False
    # r1[1] < r2[2] and r2[1] < r1[2] for 0-based half-open intervals
    return r1[1] < r2[2] and r2[1] < r1[2]


def count_overlap_with_region(
        block: Block,
        target_region: GenomicRegion) -> t.Tuple[int, int]:
    _, _, alns = block
    n_in = 0
    for n, s, e in alns:
        if is_overlap(target_region, (n, s, e)):
            n_in += 1
    return n_in, len(alns) - n_in

class AvoidOTP(object):
    """Avoid Out of Target Peak."""
    def __init__(self,
                 target_regions: t.List[t.Tuple[str, int, int]],
                 density_thresh: float = 1e-3,
                 search_range: t.Tuple[int, int] = (-10**6, 10**6),
                 avoid_target_overlap: bool = True):
        self.trees = defaultdict(IntervalTree)
        self.target_region = target_regions
        self.density_thresh = density_thresh
        self.search_range = search_range
        self.avoid_target_overlap = avoid_target_overlap

    def add(self, alns: t.Iterable[Aln]):
        for aln in alns:
            rname, start, end = aln
            tree = self.trees[rname]
            tree[start:end] = rname

    def remove_from_tree(self, inserted: t.Iterable[t.Tuple[str, Interval]]):
        for rname, itv in list(set(inserted)):
            self.trees[rname].remove(itv)

    def overlap_with_targets(self, r: GenomicRegion):
        return [tr for tr in self.target_region if is_overlap(tr, r)]

    def filter(self, g: t.Iterable[Block]) -> t.Iterable[Block]:
        for qname, seq, alns in g:
            inserted = []
            for aln in alns:
                search = True
                rname, start, end = aln
                tree = self.trees[rname]

                if self.overlap_with_targets((rname, start, end)):
                    if self.avoid_target_overlap and tree[start:end]:
                        # avoid overlap in target region
                        self.remove_from_tree(inserted)
                        break
                    else:
                        search = False

                if search:
                    range_ = (start+self.search_range[0], end+self.search_range[1])
                    in_range = tree[range_[0]:range_[1]]
                    density = len(in_range) / (self.search_range[1] - self.search_range[0])
                    if density >= self.density_thresh:
                        # avoid peak
                        self.remove_from_tree(inserted)
                        break

                itv = Interval(start, end, qname)
                tree.add(itv)
                inserted.append((rname, itv))
            else:
                yield qname, seq, alns


# Main function
def avoid_otp(
        blocks: t.Iterable[Block],
        target_regions: t.List[GenomicRegion],
        density_thresh: float = 1e-5,
        avoid_target_overlap: bool = True,
        search_range: t.Tuple[int, int] = (-1e5, 1e5)
        ):
    regions = [parse_region(r) for r in target_regions]

    def sort_key(b):
        return sum([count_overlap_with_region(b, r)[0] for r in regions])

    if regions:
        blocks.sort(key=sort_key, reverse=True)

    acc = AvoidOTP(regions, density_thresh, search_range, avoid_target_overlap)
    blocks = acc.filter(blocks)

    counted = []
    for b in blocks:
        if regions:
            c = [0, 0]
            for r in regions:
                c_ = count_overlap_with_region(b, r)
                c[0] += c_[0]
                c[1] += c_[1]
            if c[0] > 0:
                counted.append((b, c))
        else:
            c = (0, len(b[2]))
            counted.append((b, c))

    counted.sort(key=lambda t: t[1][0]/(t[1][0] + t[1][1]), reverse=True)

    return counted
