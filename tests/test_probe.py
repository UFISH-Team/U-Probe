from uprobe.gen.probe import circle_probe, amp_probe

def test_circle_probe():
    target_part1 = "AAGG"
    target_part2 = "TTCC"
    barcode1 = "CGCG"
    barcode2 = "CGCG"
    probe = circle_probe(target_part1, target_part2, barcode1, barcode2)
    assert probe == "CCTTCGCGACGCGGGAA"

def test_amp_probe():
    target_region = "AAGGTTCCCGGGG"
    target_part1 = "AAGG"
    target_part2 = "TTCC"
    target_part3 = "GGAA"
    barcode2 = "CGTA"
    probe = amp_probe(target_region, target_part1, target_part2, target_part3, barcode2)
    assert probe == "TTCCCTACG"
