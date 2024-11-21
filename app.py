import flet as ft

def main(page: ft.Page):
    page.title = "Muhangiki Wallet"
    page.add(ft.Text("Bonjour !"))

ft.app(target=main, view=ft.WEB_BROWSER, host="0.0.0.0", port=800)