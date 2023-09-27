from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.screen import MDScreen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.lang import Builder

# Load a KV file that defines the main layout
kv_string = '''
BoxLayout:
    orientation: 'vertical'
    MDTabs:
        id: tabs
        on_tab_switch: app.on_tab_switch(*args)
'''


class Tab1Content(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(MDLabel(text="Tab 1 Content"))
        self.add_widget(MDRaisedButton(text="Button in Tab 1"))


class Tab2Content(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(MDLabel(text="Tab 2 Content"))
        self.add_widget(MDRaisedButton(text="Button in Tab 2"))


class TabbedPanelApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.screen_manager = Builder.load_string(kv_string)
        tabs = self.screen_manager.ids.tabs
        tabs.tab_display_mode = "text"

        tab1 = Tab1Content(name="tab1")
        tab2 = Tab2Content(name="tab2")

        tabs_panel1 = MDTabsBase(text="Tab 1")
        tabs_panel1. = tab1

        tabs_panel2 = MDTabsBase(text="Tab 2")
        tabs_panel2.content = tab2

        tabs.add_widget(tabs_panel1)
        tabs.add_widget(tabs_panel2)

        return self.screen_manager

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        # Handle tab switch events here
        pass


if __name__ == '__main__':
    TabbedPanelApp().run()
