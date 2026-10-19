import os
import time
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageDraw, ImageFont

# مسیر حافظه اندروید
ROOT_PATH = "/storage/emulated/0/DCIM/Camera/"
if not os.path.exists(ROOT_PATH):
    ROOT_PATH = "/storage/emulated/0/Pictures/"
    if not os.path.exists(ROOT_PATH):
        ROOT_PATH = "/storage/emulated/0/"

TEMP_IMG = "temp_pixelpro.jpg"
OUTPUT_DIR = "PixelPro_Edits"
if not os.path.exists(OUTPUT_DIR): 
    os.makedirs(OUTPUT_DIR)

class ModernButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.2, 0.26, 1)
        self.color = (0.95, 0.95, 0.95, 1)
        self.font_size = '13sp'
        self.bold = True

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=25)
        
        title_label = Label(
            text="[b]PIXELPRO[/b]\n[size=16]Professional Photo Studio v3.0[/size]", 
            markup=True, 
            font_size='36sp', 
            halign='center',
            color=(0.1, 0.7, 1.0, 1)
        )
        layout.add_widget(title_label)
        
        btn_gallery = ModernButton(text="📂  OPEN GALLERY & EDIT", size_hint_y=None, height=85)
        btn_gallery.background_color = (0.12, 0.55, 0.9, 1)
        btn_gallery.bind(on_press=self.goto_gallery)
        layout.add_widget(btn_gallery)
        
        layout.add_widget(Label(text="Added: Crop, Polaroid Frame & Watermark", font_size='11sp', halign='center', color=(0.4, 0.4, 0.4, 1)))
        self.add_widget(layout)

    def goto_gallery(self, instance):
        self.manager.get_screen('import_screen').load_images_grid()
        self.manager.current = 'import_screen'

class ImportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=8, spacing=8)
        
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        btn_back = ModernButton(text="◀  Back", size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        header.add_widget(btn_back)
        
        self.title_label = Label(text="Tap an Image to Preview & Edit", font_size='14sp', bold=True)
        header.add_widget(self.title_label)
        self.layout.add_widget(header)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=3, spacing=10, padding=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def load_images_grid(self):
        self.grid.clear_widgets()
        try:
            files = [f for f in os.listdir(ROOT_PATH) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not files:
                self.grid.add_widget(Label(text="No images found in gallery folder!", font_size='14sp'))
                return

            for filename in files:
                full_path = os.path.join(ROOT_PATH, filename)
                btn = ModernButton(text=filename[:12] + "...", size_hint_y=None, height=90)
                btn.background_color = (0.18, 0.18, 0.24, 1)
                btn.bind(on_press=lambda x, p=full_path: self.show_preview_popup(p))
                self.grid.add_widget(btn)
        except Exception as e:
            self.grid.add_widget(Label(text=f"Error loading path: {str(e)}", font_size='12sp'))

    def show_preview_popup(self, image_path):
        content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        preview_img = KivyImage(source=image_path, allow_stretch=True, keep_ratio=True)
        content_layout.add_widget(preview_img)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_cancel = ModernButton(text="Cancel")
        btn_cancel.background_color = (0.6, 0.2, 0.2, 1)
        
        btn_confirm = ModernButton(text="✔ EDIT THIS PHOTO")
        btn_confirm.background_color = (0.1, 0.7, 0.35, 1)
        
        popup = Popup(title='Image Review', content=content_layout, size_hint=(0.9, 0.9))
        btn_cancel.bind(on_press=popup.dismiss)
        btn_confirm.bind(on_press=lambda x: self.confirm_and_open_editor(image_path, popup))
        
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_confirm)
        content_layout.add_widget(btn_layout)
        popup.open()

    def confirm_and_open_editor(self, path, popup):
        popup.dismiss()
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((1200, 1200))
            img.save(TEMP_IMG, "JPEG", quality=90)
            
            self.manager.get_screen('editor').load_image(TEMP_IMG)
            self.manager.current = 'editor'
        except Exception as e:
            err_popup = Popup(title='Error', content=Label(text=str(e)), size_hint=(0.8, 0.3))
            err_popup.open()

class EditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_pil_img = None
        self.original_pil_img = None
        
        self.main_layout = BoxLayout(orientation='vertical', spacing=4, padding=4)
        
        self.image_display = KivyImage(source="", allow_stretch=True, keep_ratio=True)
        self.main_layout.add_widget(self.image_display)

        control_area = BoxLayout(orientation='vertical', size_hint_y=0.52, spacing=5)
        
        # نوار ابزار بالا (شامل ابزارهای جدید Crop، Frame، Text)
        ops_layout = BoxLayout(size_hint_y=None, height=45, spacing=3)
        
        btn_back = ModernButton(text="◀ Menu")
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'import_screen'))
        
        btn_reset = ModernButton(text="↺ Reset")
        btn_reset.bind(on_press=self.reset_image)
        
        btn_rotate = ModernButton(text="↻ Rotate")
        btn_rotate.bind(on_press=self.rotate_image)

        btn_crop = ModernButton(text="✂ Crop")
        btn_crop.background_color = (0.7, 0.4, 0.1, 1)
        btn_crop.bind(on_press=self.crop_image)

        btn_frame = ModernButton(text="🖼 Frame")
        btn_frame.background_color = (0.4, 0.2, 0.6, 1)
        btn_frame.bind(on_press=self.add_polaroid_frame)

        btn_text = ModernButton(text="✍ Text")
        btn_text.background_color = (0.1, 0.5, 0.6, 1)
        btn_text.bind(on_press=self.open_text_popup)
        
        btn_save = ModernButton(text="💾 Save")
        btn_save.background_color = (0.0, 0.5, 0.85, 1)
        btn_save.bind(on_press=self.save_image)
        
        for b in [btn_back, btn_reset, btn_rotate, btn_crop, btn_frame, btn_text, btn_save]:
            ops_layout.add_widget(b)
        
        control_area.add_widget(ops_layout)

        # اسلایدرهای روشنایی و کنتراست
        bright_layout = BoxLayout(size_hint_y=None, height=32, spacing=8, padding=[10, 0])
        bright_layout.add_widget(Label(text="Brightness", size_hint_x=0.3, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.bright_slider = Slider(min=0.5, max=2.0, value=1.0)
        self.bright_slider.bind(on_release=self.apply_brightness)
        bright_layout.add_widget(self.bright_slider)
        control_area.add_widget(bright_layout)

        contrast_layout = BoxLayout(size_hint_y=None, height=32, spacing=8, padding=[10, 0])
        contrast_layout.add_widget(Label(text="Contrast", size_hint_x=0.3, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.contrast_slider = Slider(min=0.5, max=2.0, value=1.0)
        self.contrast_slider.bind(on_release=self.apply_contrast)
        contrast_layout.add_widget(self.contrast_slider)
        control_area.add_widget(contrast_layout)

        # فیلترها
        scroll = ScrollView()
        self.filter_grid = GridLayout(cols=3, spacing=6, padding=[2, 8], size_hint_y=None)
        self.filter_grid.bind(minimum_height=self.filter_grid.setter('height'))

        filters = [
            ("Grayscale", "bw"), ("Sepia (Classic)", "sepia"), ("Vivid (Color+)", "vivid"),
            ("Gaussian Blur", "blur"), ("Sharpen+", "sharp"), ("Denoise (Smooth)", "smooth"),
            ("High Contrast", "high_contrast"), ("Posterize (Art)", "posterize"), ("Invert Colors", "invert"),
            ("Contour (Outline)", "contour"), ("Detail Enhance", "detail"), ("Edge Detect", "edge"),
            ("Warm Glow", "warm"), ("Cool Tone", "cool"), ("Vignette (Legacy)", "vignette"),
            ("Emboss (3D)", "emboss"), ("Find Edges", "find_edges"), ("Solarize FX", "solarize"), ("Soft Glow", "soft_glow")
        ]

        for name, mode in filters:
            btn = ModernButton(text=name, size_hint_y=None, height=50)
            btn.font_size = '11sp'
            btn.background_color = (0.24, 0.24, 0.31, 1)
            btn.bind(on_press=lambda x, m=mode: self.apply_filter_preview(m))
            self.filter_grid.add_widget(btn)

        scroll.add_widget(self.filter_grid)
        control_area.add_widget(scroll)
        
        self.main_layout.add_widget(control_area)
        self.add_widget(self.main_layout)

    def load_image(self, path):
        self.original_pil_img = Image.open(path).convert("RGB")
        self.current_pil_img = self.original_pil_img.copy()
        self.bright_slider.value = 1.0
        self.contrast_slider.value = 1.0
        self.update_display()

    def update_display(self):
        if self.current_pil_img:
            temp_path = "preview_pixelpro.jpg"
            self.current_pil_img.save(temp_path, "JPEG", quality=85)
            self.image_display.source = temp_path
            self.image_display.reload()

    # --- ابزار جدید: برش تصویر (Crop Center) ---
    def crop_image(self, instance):
        if not self.current_pil_img: return
        w, h = self.current_pil_img.size
        # برش 15 درصد از اطراف به عنوان Crop استاندارد مرکزی
        crop_box = (int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9))
        self.current_pil_img = self.current_pil_img.crop(crop_box)
        self.original_pil_img = self.current_pil_img.copy()
        self.update_display()

    # --- ابزار جدید: فریم پولاروید کلاسیک ---
    def add_polaroid_frame(self, instance):
        if not self.current_pil_img: return
        w, h = self.current_pil_img.size
        # ایجاد یک قاب سفید رنگ در اطراف عکس
        border_size = int(max(w, h) * 0.08)
        bottom_extra = int(border_size * 2.5) # حاشیه پایین پهن‌تر شبیه پولاروید
        
        framed_img = ImageOps.expand(self.current_pil_img, border=(border_size, border_size, border_size, bottom_extra), fill='white')
        self.current_pil_img = framed_img
        self.original_pil_img = self.current_pil_img.copy()
        self.update_display()

    # --- ابزار جدید: نوشتن متن / واترمارک روی عکس ---
    def open_text_popup(self, instance):
        if not self.current_pil_img: return
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="Enter Watermark / Custom Text:", font_size='13sp'))
        
        text_input = TextInput(text="PixelPro Studio", multiline=False, font_size='16sp', size_hint_y=None, height=45)
        content.add_widget(text_input)
        
        btn_apply = ModernButton(text="Add to Image", size_hint_y=None, height=50)
        btn_apply.background_color = (0.1, 0.7, 0.35, 1)
        
        popup = Popup(title='Watermark Tool', content=content, size_hint=(0.8, 0.35))
        
        def apply_text(btn):
            txt = text_input.text
            popup.dismiss()
            if txt:
                draw = ImageDraw.Draw(self.current_pil_img)
                w, h = self.current_pil_img.size
                # قرار دادن متن در گوشه پایین سمت راست عکس
                # استفاده از فونت پیش‌فرض سیستم برای عدم وابستگی به فایل خارجی
                draw.text((int(w * 0.05), int(h * 0.90)), txt, fill=(255, 255, 0))
                self.original_pil_img = self.current_pil_img.copy()
                self.update_display()

        btn_apply.bind(on_press=apply_text)
        content.add_widget(btn_apply)
        popup.open()

    def apply_filter_preview(self, mode):
        if not self.original_pil_img: return
        img = self.original_pil_img.copy()
        
        self.bright_slider.value = 1.0
        self.contrast_slider.value = 1.0

        if mode == "bw": 
            self.current_pil_img = ImageOps.grayscale(img).convert("RGB")
        elif mode == "sepia": 
            grayscale = ImageOps.grayscale(img)
            self.current_pil_img = ImageOps.colorize(grayscale, '#704214', '#FFF8DC')
        elif mode == "vivid": 
            self.current_pil_img = ImageEnhance.Color(img).enhance(1.8)
        elif mode == "blur": 
            self.current_pil_img = img.filter(ImageFilter.GaussianBlur(3))
        elif mode == "sharp": 
            self.current_pil_img = img.filter(ImageFilter.SHARPEN)
        elif mode == "smooth":
            self.current_pil_img = img.filter(ImageFilter.SMOOTH_MORE)
        elif mode == "high_contrast":
            self.current_pil_img = ImageEnhance.Contrast(img).enhance(2.0)
        elif mode == "posterize":
            self.current_pil_img = ImageOps.posterize(img, 3)
        elif mode == "invert":
            self.current_pil_img = ImageOps.invert(img)
        elif mode == "contour":
            self.current_pil_img = img.filter(ImageFilter.CONTOUR)
        elif mode == "detail":
            self.current_pil_img = img.filter(ImageFilter.DETAIL)
        elif mode == "edge":
            self.current_pil_img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        elif mode == "warm":
            gs = ImageOps.grayscale(img)
            warm_img = ImageOps.colorize(gs, '#8B4513', '#FFD700')
            self.current_pil_img = ImageEnhance.Color(warm_img).enhance(1.2)
        elif mode == "cool":
            gs = ImageOps.grayscale(img)
            cool_img = ImageOps.colorize(gs, '#191970', '#E0FFFF')
            self.current_pil_img = ImageEnhance.Color(cool_img).enhance(0.9)
        elif mode == "vignette":
            gs = ImageOps.grayscale(img)
            duotone_vignette = ImageOps.colorize(gs, '#121212', '#F0F0F0')
            self.current_pil_img = ImageEnhance.Contrast(duotone_vignette).enhance(1.3)
        elif mode == "emboss":
            self.current_pil_img = img.filter(ImageFilter.EMBOSS)
        elif mode == "find_edges":
            self.current_pil_img = img.filter(ImageFilter.FIND_EDGES)
        elif mode == "solarize":
            self.current_pil_img = ImageOps.solarize(img, threshold=128)
        elif mode == "soft_glow":
            blurred = img.filter(ImageFilter.GaussianBlur(5))
            self.current_pil_img = Image.blend(img, blurred, alpha=0.3)
            
        self.update_display()

    def apply_brightness(self, slider):
        if not self.original_pil_img: return
        enhancer = ImageEnhance.Brightness(self.current_pil_img)
        self.current_pil_img = enhancer.enhance(slider.value)
        self.update_display()

    def apply_contrast(self, slider):
        if not self.original_pil_img: return
        enhancer = ImageEnhance.Contrast(self.current_pil_img)
        self.current_pil_img = enhancer.enhance(slider.value)
        self.update_display()

    def rotate_image(self, instance):
        if self.current_pil_img:
            self.current_pil_img = self.current_pil_img.rotate(270, expand=True)
            self.original_pil_img = self.original_pil_img.rotate(270, expand=True)
            self.update_display()

    def reset_image(self, instance):
        if self.original_pil_img:
            self.current_pil_img = self.original_pil_img.copy()
            self.bright_slider.value = 1.0
            self.contrast_slider.value = 1.0
            self.update_display()

    def save_image(self, instance):
        if self.current_pil_img:
            ts = int(time.time())
            path = os.path.join(OUTPUT_DIR, f"PixelPro_{ts}.jpg")
            self.current_pil_img.save(path, "JPEG", quality=95)
            
            popup = Popup(
                title='Export Successful', 
                content=Label(text=f"Image saved to:\n/{OUTPUT_DIR}", halign='center'), 
                size_hint=(0.8, 0.4)
            )
            popup.open()

class PixelProApp(App):
    def build(self):
        self.title = "PixelPro Studio v3.0"
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='menu'))
        sm.add_widget(ImportScreen(name='import_screen'))
        sm.add_widget(EditorScreen(name='editor'))
        return sm

if __name__ == '__main__':
    PixelProApp().run()
