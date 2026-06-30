import copy
import sys

# 1. Save the original deepcopy mechanism
_original_deepcopy = copy.deepcopy

# 2. Create the loud interceptor
def tracing_deepcopy(x, memo=None, _nil=[]):
    try:
        # Attempt the actual memory copy
        return _original_deepcopy(x, memo, _nil)
    except Exception as e:
        # 🚨 THE TRAP: If it crashes, print exactly what Pydantic choked on!
        print("\n" + "="*60, flush=True)
        print("🚨 BOOM! CRASH DETECTED ON THIS EXACT OBJECT 🚨", flush=True)
        print(f"Object Type: {type(x)}", flush=True)
        try:
            # Print a snippet of the object so you can identify where it lives
            print(f"Object Value: {repr(x)[:500]}", flush=True) 
        except Exception:
            print("Object Value: <Unprintable>", flush=True)
        print("="*60 + "\n", flush=True)
        
        # Re-raise to maintain the normal stack trace
        raise e

# 3. Hijack Python's core copy module globally
copy.deepcopy = tracing_deepcopy
