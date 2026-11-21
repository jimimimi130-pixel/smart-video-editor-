from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from smart_editor_core import SmartVideoEditorProject


class EditorRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=8, **kwargs)
        base_dir = str(Path(App.get_running_app().user_data_dir) / "projects_data") if App.get_running_app() else "projects_data"
        self.editor = SmartVideoEditorProject(projects_root=base_dir)
        projs = self.editor.list_projects()
        self.active_pid = projs[0]["id"] if projs else None

        self.status_lbl = Label(text="استوديو المونتاج — جاهز", size_hint_y=None, height=40)
        self.add_widget(self.status_lbl)

        top_bar = BoxLayout(size_hint_y=None, height=46, spacing=6)
        top_bar.add_widget(Button(text="مشروع جديد", on_release=self.new_project_popup))
        top_bar.add_widget(Button(text="حذف المشروع", on_release=self.confirm_delete_popup))
        self.add_widget(top_bar)

        # أزرار الميزات القصيرة: لا تظهر تفاصيل الميزة إلا عند الضغط على زرها
        short_btns = [
            "قص ذكي", "مزامنة", "كشف التكرار", "ترجمة", "تعليق صوتي",
            "كرونا", "مسارات", "زوم", "تغيير الصوت", "إزالة الضجيج",
        ]
        grid = BoxLayout(orientation="vertical", size_hint_y=None, height=104, spacing=6)
        row1 = BoxLayout(spacing=6)
        row2 = BoxLayout(spacing=6)
        for idx, name in enumerate(short_btns):
            btn = Button(text=name, on_release=lambda _b, n=name: self.open_feature_popup(n))
            (row1 if idx < 5 else row2).add_widget(btn)
        grid.add_widget(row1)
        grid.add_widget(row2)
        self.add_widget(grid)

        self.projects_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6)
        self.projects_box.bind(minimum_height=self.projects_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.projects_box)
        self.add_widget(scroll)

        self.refresh_projects_ui()

    def refresh_projects_ui(self):
        self.projects_box.clear_widgets()
        projs = self.editor.list_projects()
        if not projs:
            self.active_pid = None
            self.status_lbl.text = "لا توجد مشاريع بعد — اضغط مشروع جديد"
            return
        if not self.active_pid or all(p["id"] != self.active_pid for p in projs):
            self.active_pid = projs[0]["id"]

        cur = next(p for p in projs if p["id"] == self.active_pid)
        self.status_lbl.text = f"المشروع: {cur['name']} | المقاطع: {len(cur.get('cuts', []))}"

        for p in projs:
            b = Button(
                text=f"{p['name']} ({p['id'][-6:]})",
                size_hint_y=None,
                height=44,
                on_release=lambda _b, pid=p["id"]: self.select_project(pid),
            )
            self.projects_box.add_widget(b)

    def select_project(self, pid: str):
        self.active_pid = pid
        self.refresh_projects_ui()

    def new_project_popup(self, _btn):
        box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        inp = TextInput(hint_text="اسم المشروع", multiline=False, size_hint_y=None, height=44)
        box.add_widget(inp)
        pop = Popup(title="مشروع جديد", content=box, size_hint=(0.85, 0.35))

        def create_now(_b):
            self.editor.create_project(inp.text.strip() or "مشروع جديد")
            self.refresh_projects_ui()
            pop.dismiss()

        box.add_widget(Button(text="إنشاء", size_hint_y=None, height=44, on_release=create_now))
        pop.open()

    def confirm_delete_popup(self, _btn):
        if not self.active_pid:
            return
        box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        box.add_widget(Label(text="تأكيد الحذف اليدوي النهائي للمشروع؟"))
        pop = Popup(title="حذف يدوي", content=box, size_hint=(0.85, 0.35))

        def do_delete(_b):
            self.editor.delete_project_manually(self.active_pid)
            self.active_pid = None
            self.refresh_projects_ui()
            pop.dismiss()

        box.add_widget(Button(text="تأكيد الحذف", size_hint_y=None, height=44, on_release=do_delete))
        pop.open()

    def open_feature_popup(self, feature_name: str):
        if not self.active_pid:
            self.status_lbl.text = "أنشئ أو اختر مشروعاً أولاً"
            return
        box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        box.add_widget(Label(text=f"إعدادات: {feature_name}"))
        pop = Popup(title=feature_name, content=box, size_hint=(0.85, 0.4))

        def apply_feature(_b):
            if feature_name == "قص ذكي":
                self.editor.plan_demo_cuts(self.active_pid)
            elif feature_name == "ترجمة":
                self.editor.set_feature_flag(self.active_pid, "enable_subtitles", True)
            elif feature_name == "تعليق صوتي":
                self.editor.set_feature_flag(self.active_pid, "enable_voiceover", True)
            elif feature_name == "كرونا":
                self.editor.set_feature_flag(self.active_pid, "chroma_key", True)
            elif feature_name == "زوم":
                self.editor.set_feature_flag(self.active_pid, "image_zoom", True)
            elif feature_name == "تغيير الصوت":
                self.editor.set_feature_flag(self.active_pid, "voice_changer", True)
            elif feature_name == "إزالة الضجيج":
                self.editor.set_feature_flag(self.active_pid, "noise_removal", True)
            self.refresh_projects_ui()
            pop.dismiss()

        box.add_widget(Button(text="تطبيق", size_hint_y=None, height=44, on_release=apply_feature))
        pop.open()


class StudioAndroidApp(App):
    def build(self):
        return EditorRoot()


if __name__ == "__main__":
    StudioAndroidApp().run()
