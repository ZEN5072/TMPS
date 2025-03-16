import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QComboBox, QLineEdit, 
                            QListWidget, QFileDialog, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QObject
from abc import ABC, abstractmethod
from typing import Dict

# Singleton: Менеджер настроек
class SettingsManager: 
    # первое что пришло в голову
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls) 
            # super(SettingsManager, cls) - питон момент
            cls._instance.config = {
                "theme": "Classic", 
                "version": "1.0"}
        return cls._instance
    
    def get_config(self):
        return self._instance.config


class SingletonPyQt(QObject): # Более рациональное применение паттерна
    # чудо юдо, которое не работает без QObject 
    # (слава forum.qt.io)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    

# Абстрактный UI-элемент
class UIElement(ABC): # ABC - питон момент (Абстракт Бейз Класс)
    @abstractmethod
    def to_json(self):
        pass
    
    @abstractmethod
    def render(self, parent):
        pass

# Конкретные UI-элементы
class ButtonElement(UIElement):
    def __init__(self, text="Button", style="default"):
        self.text = text
        self.style = style
    
    def to_json(self):
        return {
            "type": "button", 
            "text": self.text, 
            "style": self.style
            }
    
    def render(self, parent):
        btn = QPushButton(self.text, parent)
        btn.setStyleSheet(self._get_style())
        return btn
    
    def _get_style(self):
        return "background-color: #4CAF50; color: white;" if self.style == "material" else ""

class TextFieldElement(UIElement):
    def __init__(self, placeholder="Enter text", style="default"):
        self.placeholder = placeholder
        self.style = style
    
    def to_json(self):
        return {
            "type": "textfield", 
            "placeholder": self.placeholder
            #, "style": self.style
            }
    
    def render(self, parent: QWidget):
        field = QLineEdit(parent)
        field.setPlaceholderText(self.placeholder)
        return field

class CheckBoxElement(UIElement):
    def to_json(self):
        pass
    
    
    def render(self, parent):
        pass


# Factory Method: Фабрика элементов
class UIElementFactory: # останется в качестве исторической памятки
    @staticmethod
    def create_element(**kwargs): # Нет мозгам, слава **kwargs
        if element_type == "button":
            # Only pass relevant parameters for ButtonElement
            return ButtonElement(
                text=kwargs.get("text", "Button"),
                style=kwargs.get("style", "default")
            )
        elif element_type == "textfield":
            # Only pass relevant parameters for TextFieldElement
            return TextFieldElement(
                placeholder=kwargs.get("placeholder", "Enter text")
                #, style=kwargs.get("style", "default") # ретрофитируемость
            )
        else:
            raise ValueError(f"Unknown element type: {element_type}")


class IUIElementFactory(ABC):
    @staticmethod
    @abstractmethod
    def create_element(**kwargs) -> UIElement:
        pass

class ButtonUIElementFactory(IUIElementFactory):
    @staticmethod
    def create_element(*args, **kwargs) -> ButtonElement:
        """
        :param kwargs: 
        - text  (str): название кнопки
        - style (str): стиль кнопки
        """
        return ButtonElement(
                text =kwargs.get("text",  "Button"),
                style=kwargs.get("style", "default")
            )

class TextBoxUIElementFactory(IUIElementFactory):
    @staticmethod
    def create_element(*args, **kwargs) -> TextFieldElement:
        """
        :param kwargs: 
        - placeholder  (str): текст в поле ввода
        """
        return TextFieldElement(
                placeholder =kwargs.get("placeholder", "Enter text"),
                style       =kwargs.get("style",       "default")
            )

class CheckBoxUIElementFactory(IUIElementFactory):
    """
    :param kwargs: 
    - name  (str): текст в поле ввода
    """
    @staticmethod
    def create_element(*args, **kwargs):
        return CheckBoxElement()

# Bridge (покакал фабриками, теперь "убирай")
class UIElementCreator: # формально является полной заменой UIElementFactory
    def __init__(self, **kwargs):
        """
        :param kwargs: 
        - btn_factory  (IUIElementFactory): фабрика кнопок
        - text_factory (IUIElementFactory): фабрика текстовых окон
        """
        self._element_map : Dict[str, IUIElementFactory] = {
            "button":  kwargs.get("btn_factory",  ButtonUIElementFactory),
            "textfield": kwargs.get("text_factory", TextBoxUIElementFactory),
            "checkbox" : kwargs.get("check_factory", CheckBoxUIElementFactory())
        }
        # Маппинг типов элементов на функции создания
    def create_element(self, element_type: str, **kwargs) -> UIElement | None:
        factory = self._element_map.get(element_type)
        if not factory:
            raise ValueError(f"Unknown element type: {element_type}")
            return None  # Зависит от того что будет дальше
        return factory.create_element(**kwargs)



# Abstract Factory: Фабрика стилей
class UIStyleFactory(ABC): # ABC - питон момент (Абстракт Бейз Класс)
    @abstractmethod
    def create_button(self, text):
        pass
    
    @abstractmethod
    def create_textfield(self, placeholder):
        pass

class MaterialStyleFactory(UIStyleFactory):
    def create_button(self, text):
        return ButtonUIElementFactory.create_element("button", text=text, style="material")
    
    def create_textfield(self, placeholder):
        return TextBoxUIElementFactory.create_element("textfield", placeholder=placeholder, style="material")

class ClassicStyleFactory(UIStyleFactory):
    def create_button(self, text):
        return ButtonUIElementFactory.create_element("button", text=text, style="classic")
    
    def create_textfield(self, placeholder):
        return TextBoxUIElementFactory.create_element("textfield", placeholder=placeholder, style="classic")

# Builder: Построитель фрейма
class FrameBuilder(ABC):
    @abstractmethod
    def set_name(self, name):
        pass
    
    @abstractmethod
    def add_element(self, element):
        pass

    @abstractmethod
    def build(self):
        pass

class FrameJSONBuilder(FrameBuilder):
    def __init__(self):
        self.elements = []
        self.name = "Untitled Frame"
    
    def set_name(self, name):
        self.name = name
        return self
    
    # Буквально единственная причина почему тут оправданно использование Builder
    def add_element(self, element):
        self.elements.append(element)
        return self
    
    def build(self):
        return FrameJSON(self.name, self.elements)


# Prototype паттерн:
class Prototype(ABC):
# Ну, не я такой. Таков паттерн
    @abstractmethod
    def clone(self):
        pass 
        

class FrameJSON(Prototype): # Prototype: Класс фрейма с возможностью клонирования
    # Иммутабельность - для л0х0в, пацаны сами следят за данными
    def __init__(self, name, elements: TextFieldElement):
        self.name = name
        self.elements = elements
    
    def to_json(self):
        return {
            "name": self.name,
            "elements": [element.to_json() for element in self.elements]
        }
    
    def clone(self):
        # Shit magic code
        return FrameJSON(self.name + " (Copy)", [element for element in self.elements])

# Memento: Для сохранения и восстановления состояния фрейма
class FrameMemento:
    def __init__(self, frame: FrameJSON):
        self.state = frame.to_json()
    
    def get_state(self):
        return self.state

class FrameCaretaker: # Паттерн Memento (отчим)
    # undo - для лохов
    # save и restore - для богов

    def __init__(self):
        # Одно из немногих мест с анотацией типа
        self.mementos: Dict[str, FrameMemento] = {} # Теоретически они могут повторятся, но всё вроде пашет
    
    def save(self, frame_name, frame):
        self.mementos[frame_name] = FrameMemento(frame)
    
    def restore(self, frame_name):
        if frame_name in self.mementos:
            return self.mementos[frame_name].get_state()
        return None


# Главное окно и приложение
class UIBuilderApp(QMainWindow, SingletonPyQt): # тут живут демоны...
    """ Трогать этот класс только в крайнем случае"""

    def __init__(self): 
        super().__init__() # super() сам разрулит вызов нужных __init__
        # в том числе и __new__ c инитами для крутого Singleton
        self.setWindowTitle("UI Frame Builder")
        self.setGeometry(100, 100, 600, 400)
        
        # Инициализация менеджеров
        self.settings = SettingsManager() # шутки ради
        self.current_frame_builder = FrameJSONBuilder()
        self.element_creator = UIElementCreator()
        self.frames = []
        self.caretaker = FrameCaretaker()
        
        # Инициализация UI
        self.init_ui()
        
        # Фабрика стилей
        self.style_factory = ClassicStyleFactory()
        self.update_style_factory()

    def init_ui(self):  # Тут живут иниты pyqt, и я их не трогаю
    # Основное окно и разметка
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Левая панель (управление)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Выбор типа элемента
        self.element_type = QComboBox()
        self.element_type.addItems(["Button", "Text Field"])
        left_layout.addWidget(self.element_type)
        
        # Поле ввода текста
        self.element_text = QLineEdit("New Element")
        left_layout.addWidget(self.element_text)
        
        # Кнопка добавления
        add_btn = QPushButton("Add Element")
        add_btn.clicked.connect(self.add_element)
        left_layout.addWidget(add_btn)
        
        # Выбор стиля
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Classic", "Material"])
        self.style_combo.currentTextChanged.connect(self.update_style_factory)
        left_layout.addWidget(self.style_combo)
        
        # Кнопка экспорта
        export_btn = QPushButton("Export to JSON")
        export_btn.clicked.connect(self.export_to_json)
        left_layout.addWidget(export_btn)
        
        # Кнопка загрузки
        load_btn = QPushButton("Load from JSON")
        load_btn.clicked.connect(self.load_from_json)
        left_layout.addWidget(load_btn)
        
        # Кнопка клонирования (по факту сохранения)
        clone_btn = QPushButton("Clone Frame")
        clone_btn.clicked.connect(self.clone_frame)
        left_layout.addWidget(clone_btn)
        
        # Кнопка удаления
        delete_btn = QPushButton("Delete Frame")
        delete_btn.clicked.connect(self.delete_frame)
        left_layout.addWidget(delete_btn)
        
        # Правая панель (превью)
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        
        # Список фреймов
        self.frame_list = QListWidget()
        self.frame_list.itemClicked.connect(self.show_frame_preview)
        
        # Компоновка
        layout.addWidget(left_panel, 1)
        layout.addWidget(self.frame_list, 1)
        layout.addWidget(self.preview_widget, 2)

    def update_style_factory(self): # Приватной бы сделать, но лучше не дышать
        style = self.style_combo.currentText()
        self.style_factory = MaterialStyleFactory() if style == "Material" else ClassicStyleFactory()

    def add_element(self): 
        text = self.element_text.text()
        element_type = self.element_type.currentText().lower().replace(" ", "")
        
        if element_type == "button":
            element = self.style_factory.create_button(text)
        else:
            element = self.style_factory.create_textfield(text)
        
        self.current_frame_builder.add_element(element)
        self.update_preview()

    def update_preview(self):
        while self.preview_layout.count():
            child = self.preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        frame = self.current_frame_builder.build()
        for element in frame.elements:
            widget = element.render(self.preview_widget)
            self.preview_layout.addWidget(widget)
        
        self.preview_layout.addStretch()

    def export_to_json(self):
        frame = self.current_frame_builder.build()
        data = frame.to_json()
        
        file_name, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'w') as f: # ну типо режим write
                json.dump(data, f, indent=4) # без понятия как это пашет

    def load_from_json(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as f:
                data = json.load(f)
                self.restore_frame_from_json(data)

    def restore_frame_from_json(self, data):
            builder = FrameJSONBuilder().set_name(data["name"])
            for elem_data in data["elements"]:
                element = self.element_creator.create_element(
                    elem_data["type"],
                    text=elem_data.get("text"),
                    placeholder=elem_data.get("placeholder"),
                    style=elem_data.get("style", "default")
                )
                builder.add_element(element)
            
            # Only add to frames list if it's not already there
            frame = builder.build()
            # Проверяем уникальность имени
            if any(f.name == frame.name for f in self.frames):
                QMessageBox.warning(self, "Error", 
                                f"Frame '{frame.name}' already exists. Please rename it in the JSON file.")
                return
            
            self.frames.append(frame)
            self.frame_list.addItem(frame.name)
            
            # Set as current frame and save state
            self.current_frame_builder = builder
            self.caretaker.save(frame.name, frame)
            self.update_preview()

    def clone_frame(self):
        frame = self.current_frame_builder.build()
        while True:
            name, ok = QInputDialog.getText(self, "Clone Frame", "Enter new frame name:", 
                                        QLineEdit.EchoMode.Normal, frame.name + " (Copy)")
            if not ok:
                return  # Пользователь отменил действие
            
            # Проверяем, существует ли уже фрейм с таким именем
            if any(f.name == name for f in self.frames):
                QMessageBox.warning(self, "Error", "Frame with this name already exists. Please choose a different name.")
                continue
            break
        
        # Clone the frame
        cloned_frame = frame.clone()
        cloned_frame.name = name
        
        # Save the cloned frame
        self.frames.append(cloned_frame)
        self.frame_list.addItem(name)
        self.caretaker.save(name, cloned_frame)
        
        # Clear the current working area
        self.current_frame_builder = FrameJSONBuilder()
        self.element_text.setText("New Element")
        self.update_preview()

    def delete_frame(self):
        current_item = self.frame_list.currentItem()
        if current_item:
            frame_name = current_item.text()
            reply = QMessageBox.question(self, "Delete Frame", 
                                       f"Are you sure you want to delete '{frame_name}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) # Тёмная магия QT
            if reply == QMessageBox.StandardButton.Yes:
                self.frames = [f for f in self.frames if f.name != frame_name]
                self.frame_list.takeItem(self.frame_list.row(current_item))
                if frame_name in self.caretaker.mementos:
                    del self.caretaker.mementos[frame_name]
                self.current_frame_builder = FrameJSONBuilder()
                self.update_preview()

    def show_frame_preview(self, item):
            frame_name = item.text()
            state = self.caretaker.restore(frame_name)
            if state:
                # Load the frame exactly as it was saved, without cloning
                builder = FrameJSONBuilder().set_name(state["name"])
                for elem_data in state["elements"]:
                    element = self.element_creator.create_element(
                        elem_data["type"],
                        text=elem_data.get("text"),
                        placeholder=elem_data.get("placeholder"),
                        style=elem_data.get("style", "default")
                    )
                    builder.add_element(element)
                self.current_frame_builder = builder
                self.update_preview()
            else:
                # Fallback to find frame in frames list
                for frame in self.frames:
                    if frame.name == frame_name:
                        self.current_frame_builder = FrameJSONBuilder().set_name(frame.name)
                        for element in frame.elements:
                            self.current_frame_builder.add_element(element)
                        self.update_preview()
                        break


# Оставь бога, всяк сюда входящий, он тут не поможет...
# YAGNI - плачет по этому коду
# KISS  - невозможен
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UIBuilderApp()
    window2 = UIBuilderApp()
    window4 = UIBuilderApp()
    window.show()
    window4.show()
    sys.exit(app.exec())