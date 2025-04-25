import customtkinter as ctk


class BaseFrame:
    def __init__(self, parent, subname, data, cmd):
        self.data = data
        self.entries = []
        self.frame = ctk.CTkScrollableFrame(
            parent.tab(subname), width=275, height=80)
        self.frame.grid(padx=10, pady=5)

        for i, (key, value) in enumerate(self.data.items()):
            entry_data = self._create_entry_box(i, key, value)
            self.entries.append(entry_data)

        self.btn_add = ctk.CTkButton(
            self.frame, width=100, text="Добавить",
            command=self.click_create_entry)
        self.btn_add.grid(row=len(self.entries),
                          columnspan=2, pady=10, padx=(15, 0))

        self.btn_save = ctk.CTkButton(
            self.frame, width=100,
            text="Сохранить", state="disabled",
            command=cmd)
        self.btn_save.grid(row=len(self.entries), column=2,
                           columnspan=2, pady=10, padx=(15, 0))

    def _create_entry_box(self, index, key, value):
        def on_edit(*args):
            self.btn_save.configure(state='normal')

        label_index = ctk.CTkLabel(self.frame, text=index + 1)
        label_index.grid(row=index, column=0, padx=(10, 0))

        entry_key = ctk.CTkEntry(self.frame, width=90)
        entry_key.insert(0, key)
        entry_key.grid(row=index, column=1, padx=(10, 0))
        entry_key.bind("<KeyRelease>", on_edit)

        entry_value = ctk.CTkEntry(self.frame, width=90)
        entry_value.insert(0, value)
        entry_value.grid(row=index, column=2, padx=(10, 0))
        entry_value.bind("<KeyRelease>", on_edit)

        button_delete = ctk.CTkButton(self.frame, text='DEL', width=25)
        button_delete.grid(row=index, column=3, padx=(10, 0))
        button_delete.configure(command=self.click_delete_entry(button_delete))

        return label_index, entry_key, entry_value, button_delete

    def click_create_entry(self):
        index = len(self.entries)
        new_entry = self._create_entry_box(index, "", "")
        self.entries.append(new_entry)

        self.btn_add.grid(row=len(self.entries),
                          columnspan=2, pady=10, padx=(15, 0))
        self.btn_save.grid(row=len(self.entries), column=2,
                           columnspan=2, pady=10, padx=(15, 0))

        self.btn_save.configure(state='normal')

    def click_delete_entry(self, button):
        def on_delete():
            row_index = button.grid_info().get('row')
            entry_to_delete = self.entries.pop(row_index)

            for widget in entry_to_delete:
                widget.destroy()

            for new_index, entry in enumerate(self.entries):
                entry[0].configure(text=new_index + 1)
                for widget in entry:
                    widget.grid(row=new_index)

            self.btn_save.configure(state='normal')

        return on_delete
