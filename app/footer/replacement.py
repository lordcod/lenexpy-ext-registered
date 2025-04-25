from .baseframe import BaseFrame


class Replacement(BaseFrame):
    def __init__(self, parent, subname):
        self.config = parent.parent.data
        super().__init__(parent, subname,
                         self.config['replacement'],
                         self.save_replacement)

    def save_replacement(self):
        self.config['replacement'].clear()
        for _, a, b, _ in self.entries:
            self.config['replacement'][a.get()] = b.get()
        self.btn_save.configure(state='disabled')
