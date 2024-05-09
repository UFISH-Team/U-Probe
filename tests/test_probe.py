from uprobe.gen.probe import circle_probe, amp_probe

def test_circle_probe():
    target_part1 = "AAAA"
    target_part2 = "TTTT"
    barcode1 = "CGCG"
    barcode2 = "CGCG"
    probe = circle_probe(target_part1, target_part2, barcode1, barcode2)
    assert probe == "TTTTGCGCGACGCGAAAA"

def test_amp_probe():
    target_region = "AAAATTTTCGGGG"
    target_part1 = "AAAA"
    target_part2 = "TTTT"
    target_part3 = "GGGG"
    barcode2 = "CGTA"
    probe = amp_probe(target_region, target_part1, target_part2, target_part3, barcode2)
    assert probe == "GGGGCTACG"
