import argparse
import json
from core import scan_iocs, monitor_rdp, export_report

parser = argparse.ArgumentParser(description='Cephalus Hunter CLI v1.1.1')
parser.add_argument('--scan', action='store_true', help='Run IOC scan')
parser.add_argument('--monitor', action='store_true', help='Monitor RDP')
parser.add_argument('--export', type=str, choices=['json', 'csv'], help='Export format (json/csv)')

args = parser.parse_args()

results = {}

if args.scan:
    print("Running IOC Scan...")
    results['scan'] = scan_iocs()

if args.monitor:
    print("Monitoring RDP Sessions...")
    results['rdp'] = monitor_rdp()

if args.export:
    format = args.export
    file = export_report(results, format)
    if file:
        print(f"Exported: {file}")
    else:
        print("Export failed.")
elif not (args.scan or args.monitor):
    print("Use --scan, --monitor, or --export json/csv")