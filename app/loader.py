import customtkinter as ctk


class LoadingScreen(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Загрузка...")
        self.geometry("300x150")

        self.loading_label = ctk.CTkLabel(
            self, text="Загрузка, пожалуйста, подождите...", padx=20, pady=20)
        self.loading_label.pack(pady=20)


def load():
    app = LoadingScreen()
    return app.destroy
