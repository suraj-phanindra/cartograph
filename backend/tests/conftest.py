def pytest_configure(config):
    config.addinivalue_line("markers", "integration: hits the live network; skips cleanly offline")
