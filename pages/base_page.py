from abc import ABC, abstractmethod
import gradio as gr
from utils.i18n import translate_text

class BasePage(ABC):
    page_id: str = ""
    icon: str = ""
    
    @abstractmethod
    def build(self, lang: str = "zh"):
        pass
    
    def get_title(self, lang: str = "zh") -> str:
        return f"### {self.icon} {translate_text(f'nav.{self.page_id}', lang)}"
    
    def create_page(self, lang: str = "zh"):
        with gr.Column():
            gr.Markdown(self.get_title(lang))
            return self.build(lang)
