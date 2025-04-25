import customtkinter as ctk


class BirthdayTab:
    def __init__(self, parent: ctk.CTkTabview, subname: str):
        self.parent = parent
        tab = parent.tab(subname)
        self.data = self.parent.parent.data

        self.entry = ctk.CTkEntry(tab)
        self.entry.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.entry.insert(1, self.data['birthday'])
        self.entry.bind("<KeyRelease>", self.update)

    def update(self, _):
        self.data['birthday'] = self.entry.get()
