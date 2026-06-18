
import servidor
from servidor import app

print("--- Testing Dashboard Route Logic ---")

try:
    with app.test_request_context('/?page=1'):
        try:
            # Manually call the view function
            response = servidor.dashboard()
            print("Dashboard executed successfully.")
            print("Response Status:", response)
        except Exception:
            print("\n!!! ERROR IN DASHBOARD LOGIC !!!")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"Setup Error: {e}")
