import customtkinter as ctk


class Location:
    def __init__(self, parent, subname):
        tab = parent.tab(subname)
        self.data = parent.parent.data

        for col in range(3):
            tab.grid_columnconfigure(col, weight=1)

        helper = ctk.CTkLabel(
            tab,
            text="Номера колонок в XLSX (1 — первая). Оставьте поле пустым, чтобы колонку игнорировать.",
            anchor="w",
            justify="left",
            wraplength=520
        )
        helper.grid(row=0, column=0, columnspan=3,
                    padx=12, pady=(8, 4), sticky="w")

        self.labels_replacement = {}

        for i, n in enumerate(self.data['location'].keys()):
            col = i % 3
            base_row = 1 + (i // 3) * 2

            label = ctk.CTkLabel(tab, text=n)
            label.grid(row=base_row, column=col,
                       padx=12, pady=(8, 2), sticky="w")

            entry = ctk.CTkEntry(tab, width=90, placeholder_text="—")
            value = self.data['location'].get(n, -1)
            if value is not None and value >= 0:
                entry.insert(0, str(value + 1))
            entry.grid(row=base_row+1, column=col,
                       padx=12, pady=(0, 8), sticky="ew")

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
            value = self.data['location'].get(n, -1)
            if value is not None and value >= 0:
                entry.insert(0, value+1)
            else:
                entry.configure(placeholder_text="—")

    def update_location(self, _):
        for n, entry in self.labels_replacement.items():
            s = entry.get().strip()
            if not s:
                self.data['location'][n] = -1
                continue
            self.data['location'][n] = int(s)-1
