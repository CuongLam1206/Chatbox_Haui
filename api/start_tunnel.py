import os
import sys
from pyngrok import ngrok, conf
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / ".env")

def start_tunnel():
    print("--- Ngrok Tunnel Starter ---")
    
    # Check for authtoken (can be in .env or manual)
    auth_token = os.getenv("NGROK_AUTHTOKEN")
    if not auth_token:
        print("Lỗi: Không tìm thấy NGROK_AUTHTOKEN trong tệp .env")
        print("Vui lòng lấy token tại: https://dashboard.ngrok.com/get-started/your-authtoken")
        auth_token = input("Nhập Ngrok Authtoken của bạn: ").strip()
    
    if auth_token:
        conf.get_default().auth_token = auth_token
        
    try:
        # Start a tunnel on port 8000
        public_url = ngrok.connect(8000).public_url
        print(f"\n[SUCCESS] Tunnel đã được tạo!")
        print(f"URL công khai của bạn là: {public_url}")
        print(f"Dán link này vào Facebook Webhook: {public_url}/webhook")
        print("\nGiữ cửa sổ này mở để duy trì kết nối.")
        
        # Keep the script running
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
    except Exception as e:
        print(f"Lỗi khi khởi tạo tunnel: {e}")
        print("Đảm bảo bạn đã nhập đúng Authtoken và máy chủ FastAPI đang chạy ở cổng 8000.")

if __name__ == "__main__":
    start_tunnel()
