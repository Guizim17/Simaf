import webview
import os
import sys

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

html_path = os.path.join(base_dir, 'editor.html')

TIPOS_ARQUIVO = ('Autômato SIMAF (*.json)', 'Todos os arquivos (*.*)')


def _primeiro(caminhos):
    """O pywebview pode devolver str, tupla ou lista, conforme a plataforma."""
    if not caminhos:
        return None
    if isinstance(caminhos, (list, tuple)):
        return caminhos[0]
    return caminhos


class Api:
    """Funções chamadas pelo editor.html via window.pywebview.api."""

    def salvar_arquivo(self, conteudo, nome_sugerido='automato.json'):
        caminho = _primeiro(webview.windows[0].create_file_dialog(
            webview.FileDialog.SAVE, save_filename=nome_sugerido, file_types=TIPOS_ARQUIVO))
        if not caminho:
            return None
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return os.path.basename(caminho)

    def abrir_arquivo(self):
        caminho = _primeiro(webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN, file_types=TIPOS_ARQUIVO))
        if not caminho:
            return None
        with open(caminho, encoding='utf-8') as f:
            return {'nome': os.path.basename(caminho), 'conteudo': f.read()}


webview.create_window("SIMAF", html_path, width=1280, height=800, js_api=Api())
webview.start()
