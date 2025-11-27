# core/utils.py
class Logger:
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        self.widget.insert("end", s)
        self.widget.see("end")
        self.widget.update_idletasks()
    def flush(self): pass