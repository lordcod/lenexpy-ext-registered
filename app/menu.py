import json
import customtkinter as ctk

from .header.view import HeaderView
from .footer.view import FooterView


class App(ctk.CTk):
    def __init__(self, data: dict):
        super().__init__()

        self.data = data

        self.geometry("620x500")
        self.resizable(False, False)

        self.header_view = HeaderView(self)
        self.header_view.grid(row=0, column=0, padx=20,
                              pady=(0, 0), sticky="nsew")

        self.footer_frame = ctk.CTkFrame(
            self, width=540, height=550)
        self.footer_frame.grid(row=1, column=0, padx=20,
                               pady=(10, 0), sticky="nsew")

        self.footer_view = FooterView(self, self.footer_frame)
        self.footer_view.grid(row=1, padx=115, pady=(10, 20), sticky="nsew")


if __name__ == '__main__':
    with open('config.json') as file:
        config = json.loads(file.read())

    app = App(config)
    app.mainloop()
