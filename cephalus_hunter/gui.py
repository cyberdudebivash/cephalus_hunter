import tkinter as tk
from tkinter import messagebox, filedialog
import json  # <-- FIXED: WAS MISSING
import os
from core import scan_iocs, monitor_rdp, export_report

class CephalusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Cephalus Hunter v1.1 by CyberDudeBivash')
        self.root.geometry('900x700')
        self.root.configure(bg='#0d1117')
        self.root.resizable(True, True)

        # Header
        header = tk.Label(root, text='Cephalus Hunter Dashboard', fg='#58a6ff', bg='#0d1117', font=('Arial', 22, 'bold'))
        header.pack(pady=20)

        # Buttons Frame
        btn_frame = tk.Frame(root, bg='#0d1117')
        btn_frame.pack(pady=10)

        self.scan_btn = tk.Button(btn_frame, text='Run IOC Scan', command=self.run_scan, bg='#238636', fg='white', font=('Arial', 10, 'bold'), width=20, height=2)
        self.scan_btn.grid(row=0, column=0, padx=10, pady=5)

        self.monitor_btn = tk.Button(btn_frame, text='Monitor RDP', command=self.monitor_rdp, bg='#238636', fg='white', font=('Arial', 10, 'bold'), width=20, height=2)
        self.monitor_btn.grid(row=0, column=1, padx=10, pady=5)

        self.export_btn = tk.Button(btn_frame, text='Export Report', command=self.export, bg='#da3633', fg='white', font=('Arial', 10, 'bold'), width=20, height=2)
        self.export_btn.grid(row=1, column=0, padx=10, pady=5, columnspan=2)

        # Results Text with Scrollbar
        text_frame = tk.Frame(root)
        text_frame.pack(pady=20, fill=tk.BOTH, expand=True, padx=20)

        self.results_text = tk.Text(text_frame, height=20, width=100, bg='#161b22', fg='#c9d1d9', font=('Consolas', 10))
        scrollbar = tk.Scrollbar(text_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status Bar
        self.status = tk.Label(root, text='Ready. Click a button to begin.', fg='#8b949e', bg='#0d1117', anchor='w')
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    def set_status(self, msg, color='#58a6ff'):
        self.status.config(text=msg, fg=color)
        self.root.update()

    def run_scan(self):
        self.set_status('Scanning for IOCs... Please wait.', '#f0ad4e')
        self.scan_btn.config(state='disabled')
        try:
            results = scan_iocs()
            self.display_results(results, "IOC Scan Complete")
        except Exception as e:
            self.display_results({"error": str(e)}, "Scan Failed")
        finally:
            self.scan_btn.config(state='normal')

    def monitor_rdp(self):
        self.set_status('Monitoring RDP sessions...', '#f0ad4e')
        self.monitor_btn.config(state='disabled')
        try:
            results = monitor_rdp()
            self.display_results(results, "RDP Monitoring Complete")
        except Exception as e:
            self.display_results({"error": str(e)}, "Monitor Failed")
        finally:
            self.monitor_btn.config(state='normal')

    def display_results(self, results, title):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"=== {title} ===\n\n")
        try:
            pretty = json.dumps(results, indent=2)
            self.results_text.insert(tk.END, pretty)
            self.set_status(f'{title} — View results below.', '#58a6ff')
        except:
            self.results_text.insert(tk.END, str(results))
            self.set_status('Results displayed (raw).', '#f0ad4e')

    def export(self):
        results = {
            'scan': scan_iocs(),
            'rdp_monitor': monitor_rdp(),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Cephalus Report"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                self.set_status(f'Report saved: {os.path.basename(file_path)}', '#238636')
                messagebox.showinfo("Success", f"Report exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
                self.set_status('Export failed.', '#da3633')

if __name__ == '__main__':
    # Check pywin32 on Windows
    if os.name == 'nt':
        try:
            import win32evtlog
        except ImportError:
            messagebox.showerror("Missing Dependency", "pywin32 is required for RDP monitoring.\nRun: pip install pywin32")
            exit(1)

    root = tk.Tk()
    app = CephalusGUI(root)
    root.mainloop()