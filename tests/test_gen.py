from uprobe.gen import hello


def test_gen():
    s = hello()
    assert s == "Hello, world!"
