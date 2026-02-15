
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.effects_panel import EffectsPanel, EffectButton, PresetItem

def test_search_deselect_extended():
    app = QApplication(sys.argv)
    panel = EffectsPanel()
    panel.show()
    panel.resize(400, 600)

    # Helper function to reset focus to search bar
    def focus_search():
        panel._search.setFocus()
        if not panel._search.hasFocus():
            print("FAIL: Could not focus search bar.")
            sys.exit(1)

    # 1. Test clicking background (already fixed)
    focus_search()
    QTest.mouseClick(panel._scroll.widget(), Qt.MouseButton.LeftButton)
    if panel._search.hasFocus():
        print("FAIL: Search bar kept focus after clicking background.")
    else:
        print("PASS: Search bar lost focus after clicking background.")

    # 2. Test clicking an EffectButton
    # Add a dummy effect button to the panel for testing
    effect_btn = EffectButton("A", "#FF0000", "Test Effect", "test_id")
    # We need to add it to the layout temporarily or interact with it independently
    # For simplicity, let's just show it and click it
    effect_btn.setParent(panel._scroll.widget()) # Add to container
    effect_btn.move(10, 10) # Position ensures it's clickable
    effect_btn.show()
    
    focus_search()
    QTest.mouseClick(effect_btn, Qt.MouseButton.LeftButton)
    if panel._search.hasFocus():
        print("FAIL: Search bar kept focus after clicking EffectButton.")
    else:
        print("PASS: Search bar lost focus after clicking EffectButton.")

    # 3. Test clicking a PresetItem
    preset_item = PresetItem("Test Preset", "Desc")
    preset_item.setParent(panel._scroll.widget())
    preset_item.move(10, 60)
    preset_item.show()

    focus_search()
    QTest.mouseClick(preset_item, Qt.MouseButton.LeftButton)
    if panel._search.hasFocus():
        print("FAIL: Search bar kept focus after clicking PresetItem.")
    else:
        print("PASS: Search bar lost focus after clicking PresetItem.")

    sys.exit(0)

if __name__ == "__main__":
    test_search_deselect_extended()
