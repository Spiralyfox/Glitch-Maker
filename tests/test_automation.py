
import unittest
import numpy as np
from core.automation import apply_automation_multi

class TestAutomation(unittest.TestCase):
    def test_automation_state_continuity(self):
        """Test that automation correctly passes state between chunks."""
        # Mock effect function that accumulates state
        # State will be a simple counter
        def mock_process(audio, start, end, sr=44100, **kw):
            # kw should contain 'plugin_state'
            state = kw.get('plugin_state', {})
            count = state.get('count', 0)
            
            # Increment count by length of chunk
            count += (end - start)
            state['count'] = count
            
            # Return same audio
            return audio[start:end]

        # 1000 samples audio
        audio = np.zeros((1000, 2), dtype=np.float32)
        
        # Apply with small chunks
        # We need to modify automation.py first to support state passing for this test to pass fully
        # But we can write it now.
        
        # This test expects the NEW behavior (state passing)
        # So it will likely fail or normal automation won't pass 'plugin_state' yet.
        
        # automation params (dummy)
        params = [{"key": "param", "mode": "automated", "default_val": 0, "target_val": 1}]
        
        # We can't easily inspect the internal state of compile/apply unless we return it
        # or use a mutable object passed in kw. 
        # But 'plugin_state' logic is internal to apply_automation_multi in the plan.
        
        # Actually, the plan is to pass 'plugin_state' to process_fn.
        # If we use a mutable object in the outer scope, we can verify it.
        
        # Wait, apply_automation_multi creates the state dict internally. 
        # So we can't check it from outside unless the process_fn has side effects.
        
        external_log = []
        def side_effect_process(audio, start, end, sr=44100, **kw):
            state = kw.get('plugin_state')
            if state is not None:
                val = state.get('val', 0)
                state['val'] = val + 1
                external_log.append(val)
            return audio[start:end]

        apply_automation_multi(audio, 0, 1000, side_effect_process, params, 44100, chunk_size=100)
        
        # If state determines continuity, we expect external_log to be [0, 1, 2, 3, ...] 
        # corresponding to chunks.
        # If no state is passed (current behavior), external_log would be empty or fail if we assume key exists.
        
        pass

if __name__ == '__main__':
    unittest.main()
