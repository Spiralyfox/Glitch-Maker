
import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.effects_panel import EffectsPanel

def test_search_global_blur():
    app = QApplication(sys.argv)
    
    # Create a main window mock
    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    
    # 1. Effects Panel (with search bar)
    panel = EffectsPanel()
    layout.addWidget(panel)
    
    # 2. Dummy "Timeline" widget (outside Effects Panel)
    timeline_mock = QLabel("Timeline Area")
    timeline_mock.setStyleSheet("background: blue; min-height: 200px;")
    layout.addWidget(timeline_mock)
    
    main_window.show()
    main_window.resize(400, 600)
    
    # Helper: Focus search
    def focus_search():
        panel._search.setFocus()
        if not panel._search.hasFocus():
            print("FAIL: Could not focus search bar.")
            sys.exit(1)
            
    # Test: Click on Timeline (outside EffectsPanel)
    focus_search()
    
    # Click center of timeline mock
    QTest.mouseClick(timeline_mock, Qt.MouseButton.LeftButton)
    
    if panel._search.hasFocus():
        print("FAIL: Search bar KEPT focus after clicking outside (Timeline mock).")
    else:
        print("PASS: Search bar LOST focus after clicking outside.")
        
    sys.exit(0)

if __name__ == "__main__":
    test_search_global_blur()
