import subprocess
import os
from sublist3r import Sublist3r
import threading
from queue import Queue
from urllib.parse import urlparse

# Output directories
OUTPUT_DIR = "screenshots"
SUBDOMAIN_FILE = "subdomains.txt"

# Create output directory if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def enumerate_subdomains(domain):
    """
    Enumerate subdomains using Sublist3r.
    """
    print(f"[+] Enumerating subdomains for {domain}")
    subdomains = Sublist3r.main(domain, 40, SUBDOMAIN_FILE, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=None)
    return subdomains

def check_ports(subdomain):
    """
    Check if the subdomain has port 80 or 443 open.
    """
    print(f"[+] Checking ports for {subdomain}")
    for port in [80, 443]:
        try:
            response = subprocess.run(
                ["curl", "-Is", f"http://{subdomain}:{port}", "--max-time", "5"],
                capture_output=True,
                text=True
            )
            if response.returncode == 0:
                return port
        except Exception as e:
            print(f"[-] Error checking {subdomain}:{port} - {e}")
    return None

def take_screenshot(url):
    """
    Take a screenshot of a given URL using webscreenshot or Aquatone.
    """
    print(f"[+] Taking screenshot of {url}")
    try:
        # Using webscreenshot
        subprocess.run(["webscreenshot", "-o", OUTPUT_DIR, url], check=True)

        # Alternatively, for Aquatone
        # subprocess.run(["aquatone", "-scan-timeout", "5000", "-out", OUTPUT_DIR, "-url", url], check=True)
    except Exception as e:
        print(f"[-] Error taking screenshot of {url} - {e}")

def worker(queue):
    """
    Worker function for threading.
    """
    while not queue.empty():
        subdomain = queue.get()
        port = check_ports(subdomain)
        if port:
            protocol = "https" if port == 443 else "http"
            url = f"{protocol}://{subdomain}"
            take_screenshot(url)
        queue.task_done()

def main():
    domain = input("[*] Enter the target domain: ").strip()
    
    # Enumerate subdomains
    subdomains = enumerate_subdomains(domain)
    
    if not subdomains:
        print("[-] No subdomains found.")
        return

    # Use threading to speed up the process
    queue = Queue()
    for subdomain in subdomains:
        queue.put(subdomain)

    for _ in range(10):  # Number of threads
        thread = threading.Thread(target=worker, args=(queue,))
        thread.daemon = True
        thread.start()

    queue.join()
    print("[+] Screenshots saved in the screenshots directory.")

if __name__ == "__main__":
    main()
