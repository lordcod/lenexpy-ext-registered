import customtkinter as ctk


class Location:
    def __init__(self, parent, subname):
        tab = parent.tab(subname)
        self.data = parent.parent.data

        self.labels_replacement = {}

        for i, n in enumerate(self.data['location'].keys()):
            label = ctk.CTkLabel(tab, text=n)
            label.grid(row=i//3*2, column=i % 3, padx=(25, 0), pady=(10, 0))

            entry = ctk.CTkEntry(tab, width=70)
            entry.insert(0, str(self.data['location'].get(n) + 1))
            entry.grid(row=i//3*2+1, column=i % 3, padx=(25, 0), pady=0)

            entry.configure(validate='all', validatecommand=(
                parent.register(self.validate_location_config), '%P'))
            entry.bind("<KeyRelease>", self.update_location)

            self.labels_replacement[n] = entry

    def validate_location_config(self, value):
        if value == '':
            return True
        return value.isdigit()

    def upload_location(self):
        for n, entry in self.labels_replacement.items():
            entry.select_clear()
            entry.delete(0, ctk.END)
            entry.insert(0, self.data['location'].get(n)+1)

    def update_location(self, _):
        for n, entry in self.labels_replacement.items():
            s = entry.get()
            if not s:
                continue
            self.data['location'][n] = int(s)-1
