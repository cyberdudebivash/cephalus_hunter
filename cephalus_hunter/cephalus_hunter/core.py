import os
import psutil
import hashlib
import winreg  # Windows registry
import win32evtlog  # Windows event logs
import win32evtlogutil
import subprocess
import bleach
from dotenv import load_dotenv
import logging
import json
from datetime import datetime

load_dotenv()
SECRET_KEY = os.getenv('APP_SECRET', 'cyberdudebivash_secure_key')  # Env only

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Known IOCs from Cephalus intel
KNOWN_HASHES = {
    'SentinelBrowserNativeHost.exe': '0d9dfc113712054d8595b50975efd9c68f4cb8960eca010076b46d2fba3d2754',
    'SentinelAgentCore.dll': '82f5fb086d15a8079c79275c2d4a6152934e2dd61cc6a4976b492f74062773a7'
}
SUSPICIOUS_FILES = ['data.bin', 'recover.txt']
SUSPICIOUS_PROCESSES = ['MEGAcmdUpdater.exe', 'vssadmin.exe', 'powershell.exe']  # With context
SUSPICIOUS_REGS = [
    r'SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths',
    r'SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection'
]
SUSPICIOUS_COMMANDS = ['vssadmin delete shadows', 'Add-MpPreference', 'reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender']

def sanitize_input(input_str):
    return bleach.clean(input_str, strip=True)

def hash_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def scan_iocs():
    results = {'files': [], 'processes': [], 'registry': [], 'hashes': []}
    
    # File scan
    for root, _, files in os.walk(os.path.expanduser('~')):  # User dirs focus
        for file in files:
            if file in SUSPICIOUS_FILES or file.endswith('.sss'):
                path = os.path.join(root, file)
                results['files'].append({'path': path, 'alert': 'Suspicious file found'})
    
    # Process scan
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] in SUSPICIOUS_PROCESSES:
            if 'Downloads' in proc.info['exe']:  # Anomalous path
                results['processes'].append({'name': proc.info['name'], 'path': proc.info['exe'], 'alert': 'Anomalous process'})
    
    # Registry scan (Windows only)
    if os.name == 'nt':
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows Defender')
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, i)
                    if any(sub in subkey for sub in SUSPICIOUS_REGS):
                        results['registry'].append({'key': subkey, 'alert': 'Defender tampering'})
                    i += 1
                except OSError:
                    break
        except Exception as e:
            logger.error(f'Registry scan error: {e}')
    
    # Hash check
    for file, known_hash in KNOWN_HASHES.items():
        path = os.path.join(os.path.expanduser('~/Downloads'), file)
        if os.path.exists(path):
            calc_hash = hash_file(path)
            if calc_hash != known_hash:
                results['hashes'].append({'file': file, 'hash': calc_hash, 'alert': 'Hash mismatch - possible sideload'})
    
    return results

def monitor_rdp():
    if os.name != 'nt':
        return {'error': 'RDP monitoring Windows-only'}
    
    server = 'localhost'
    logtype = 'Security'
    hand = win32evtlog.OpenEventLog(server, logtype)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    total = win32evtlog.GetNumberOfEventLogRecords(hand)
    events = win32evtlog.ReadEventLog(hand, flags, 0)
    
    alerts = []
    for event in events[:100]:  # Last 100 for perf
        if event.EventID == 4624:  # Logon
            data = win32evtlogutil.SafeFormatMessage(event, logtype)
            if 'Remote Desktop' in data and 'anonymous' in data.lower():  # Heuristic for weak auth
                alerts.append({'event': data, 'alert': 'Potential RDP hijack - weak auth'})
        elif event.EventID == 4648:  # Explicit creds
            data = win32evtlogutil.SafeFormatMessage(event, logtype)
            alerts.append({'event': data, 'alert': 'Suspicious RDP login attempt'})
    
    win32evtlog.CloseEventLog(hand)
    return {'rdp_alerts': alerts}

def run_command_safe(cmd_list):
    try:
        subprocess.run(cmd_list, check=True, shell=False, capture_output=True)
    except Exception as e:
        logger.error(f'Command error: {e}')

# More funcs: export_report(json/csv), etc.
def export_report(results, format='json'):
    timestamp = datetime.now().isoformat()
    file_name = f'cephalus_report_{timestamp}.{format}'
    if format == 'json':
        with open(file_name, 'w') as f:
            json.dump(results, f, indent=2)
    return file_name