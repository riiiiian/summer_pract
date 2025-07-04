import os
import sys
from pathlib import Path
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                            QVBoxLayout, QWidget, QFileDialog, QComboBox, 
                            QMessageBox, QHBoxLayout, QInputDialog, QDialog,
                            QSpinBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

# Установка пути к плагинам Qt (необходимо для корректной работы PyQt на некоторых системах)
QT_PLUGIN_PATH = r"C:\Users\РС\Desktop\pract\kik\Lib\site-packages\PyQt5\Qt5\plugins"
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = QT_PLUGIN_PATH

class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()  
        # Инициализация главного окна приложения
        self.setWindowTitle("Обработка изображений")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация переменных для хранения изображений
        self.original_image = None  # Исходное изображение
        self.processed_image = None  # Обработанное изображение
        self.camera = None  # Объект для работы с камерой
        self.camera_timer = QTimer(self)  # Таймер для обновления кадров с камеры
        self.camera_timer.timeout.connect(self.update_camera_frame)
        self.current_operations = []  # Список текущих операций обработки
        self.image_source = None  # Источник изображения (файл или камера)
        
        self.initUI()  # Инициализация пользовательского интерфейса

    def initUI(self):
        """Инициализация пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Область отображения изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setText("Нет изображения")
        self.image_label.setStyleSheet("color: gray; font-size: 16px;")
        layout.addWidget(self.image_label)

        # Панель кнопок
        buttons_layout = QHBoxLayout()
        
        # Кнопка загрузки изображения
        self.load_button = QPushButton("Загрузить изображение")
        self.load_button.clicked.connect(self.load_image)
        buttons_layout.addWidget(self.load_button)
        
        # Кнопка работы с камерой
        self.camera_button = QPushButton("Камера")
        self.camera_button.clicked.connect(self.toggle_camera)
        buttons_layout.addWidget(self.camera_button)
        
        # Кнопка закрытия приложения
        self.close_button = QPushButton("Закрыть приложение")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)

        # Выбор канала для отображения
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Оригинал изображения", "Красный канал", "Зеленый канал", "Синий канал"])
        self.channel_combo.currentIndexChanged.connect(self.update_channel)
        layout.addWidget(self.channel_combo)

        # Выбор операции обработки
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Выберите операцию...",
            "Негатив",
            "Понижение яркости", 
            "Нарисовать красный круг"
        ])
        layout.addWidget(self.operation_combo)

        # Кнопка применения выбранной операции
        self.apply_button = QPushButton("Применить операцию")
        self.apply_button.clicked.connect(self.apply_operation)
        layout.addWidget(self.apply_button)

        self.statusBar().showMessage("Готово")

    def clear_image(self):
        """Очищает отображение изображения и сбрасывает все связанные переменные"""
        self.original_image = None
        self.processed_image = None
        self.current_operations = []
        self.image_source = None
        self.image_label.setText("Нет изображения")
        self.image_label.setStyleSheet("color: gray; font-size: 16px;")

    def update_camera_frame(self):
        """Обновляет кадр с камеры в режиме реального времени"""
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.show_image(frame, preview=True)

    def load_image(self):
        """Загружает изображение из файла"""
        # Если камера включена в режиме предпросмотра - выключаем
        if self.camera is not None:
            self.camera_timer.stop()
            self.camera.release()
            self.camera = None
            self.camera_button.setText("Камера")

        # Открытие диалога выбора файла
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Открыть изображение", "", 
            "Изображения (*.png *.jpg *)", options=options)
        
        if not file_name:  # Пользователь отменил выбор
            self.clear_image()
            self.statusBar().showMessage("Загрузка отменена")
            return

        try:
            # Чтение и декодирование изображения
            with open(file_name, 'rb') as f:
                file_bytes = bytearray(f.read())
            self.original_image = cv2.imdecode(np.asarray(file_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.processed_image = self.original_image.copy()
            self.current_operations = []
            self.image_source = 'file'
            self.show_image(self.processed_image)
            self.statusBar().showMessage(f"Загружено: {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")
            self.clear_image()

    def toggle_camera(self):
        """Переключает режим работы с камерой (включение/выключение/съемка)"""
        if self.camera is None:
            # Включение камеры
            try:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise RuntimeError("Камера недоступна")
                self.camera_button.setText("Сделать фото")
                self.camera_timer.start(30)  # Обновление каждые 30 мс
                self.statusBar().showMessage("Режим камеры: нажмите 'Сделать фото' для съемки")
                self.image_source = None  # Пока только предпросмотр, не снимок
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
                self.clear_image()
        else:
            # Создание снимка камерой
            self.camera_timer.stop()
            ret, frame = self.camera.read()
            if ret:
                self.original_image = frame.copy()
                self.processed_image = self.original_image.copy()
                self.current_operations = []
                self.image_source = 'camera'
                self.show_image(self.processed_image)
                self.statusBar().showMessage("Снимок с камеры сделан")
            else:
                self.clear_image()
                self.statusBar().showMessage("Не удалось сделать снимок")
            self.camera.release()
            self.camera = None
            self.camera_button.setText("Камера")

    def show_image(self, image, preview=False):
        """Отображает изображение в интерфейсе"""
        if image is None:
            self.image_label.setText("Нет изображения")
            self.image_label.setStyleSheet("color: gray; font-size: 16px;")
            return

        # Конвертация цветового пространства для корректного отображения
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        # Создание QImage из данных numpy массива
        h, w, ch = image_rgb.shape
        q_img = QImage(image_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        
        # Масштабирование и отображение изображения
        self.image_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.image_label.width(), self.image_label.height(), 
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setStyleSheet("") 

    def update_channel(self):
        """Обновляет отображение выбранного цветового канала"""
        if self.processed_image is None:
            return
        self.processed_image = self.original_image.copy()
        self.apply_all_operations()

    def apply_all_operations(self):
        """Применяет все текущие операции обработки к изображению"""
        if self.original_image is None:
            return
            
        # Копируем оригинальное изображение
        self.processed_image = self.original_image.copy()
        
        # Применяем все сохраненные операции по очереди
        for operation in self.current_operations:
            if operation[0] == "negative":
                self.processed_image = 255 - self.processed_image
            elif operation[0] == "brightness":
                value = operation[1]
                hsv = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                v = np.where(v > value, v - value, 0)
                self.processed_image = cv2.cvtColor(cv2.merge((h, s, v)), cv2.COLOR_HSV2BGR)
            elif operation[0] == "circle":
                x, y, diameter = operation[1]
                radius = diameter // 2
                cv2.circle(self.processed_image, (x, y), radius, (0, 0, 255), 2)

        # Применяем выбранный цветовой канал
        index = self.channel_combo.currentIndex()
        if index > 0:
            b, g, r = cv2.split(self.processed_image)
            zeros = np.zeros_like(b)
            if index == 1:
                self.processed_image = cv2.merge([zeros, zeros, r])
            elif index == 2:
                self.processed_image = cv2.merge([zeros, g, zeros])
            elif index == 3:
                self.processed_image = cv2.merge([b, zeros, zeros])
                
        self.show_image(self.processed_image)

    def apply_operation(self):
        """Применяет выбранную операцию обработки изображения"""
        if self.processed_image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображение или сделайте снимок")
            return
            
        operation = self.operation_combo.currentIndex()
        if operation == 0:
            QMessageBox.warning(self, "Ошибка", "Выберите операцию")
            return
            
        if operation == 1:  # Негатив
            self.current_operations.append(("negative", None))
        elif operation == 2:  # Понижение яркости
            value, ok = QInputDialog.getInt(
                self, "Понижение яркости", "Значение (0-100):", 10, 0, 100)
            if ok:
                self.current_operations.append(("brightness", value))
        elif operation == 3:  # Нарисовать круг
            self.add_circle()
            
        self.apply_all_operations()

    def add_circle(self):
        """Открывает диалог для добавления красного круга на изображение"""
        if self.processed_image is None:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Нарисовать красный круг")
        layout = QFormLayout(dialog)
        
        height, width = self.processed_image.shape[:2]
        max_diameter = max(height, width)

        # Координата X
        x_spin = QSpinBox()
        x_spin.setRange(0, width)
        x_spin.setValue(width // 2)
        layout.addRow("Координата X (0-{}):".format(width), x_spin)

        # Координата Y
        y_spin = QSpinBox()
        y_spin.setRange(0, height)
        y_spin.setValue(height // 2)
        layout.addRow("Координата Y (0-{}):".format(height), y_spin)

        # Размер круга
        size_spin = QSpinBox()
        size_spin.setRange(10, max_diameter)
        size_spin.setValue(max_diameter)  
        layout.addRow("Диаметр круга (10-{}):".format(max_diameter), size_spin)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec_() == QDialog.Accepted:
            x = x_spin.value()
            y = y_spin.value()
            diameter = size_spin.value()
            self.current_operations.append(("circle", (x, y, diameter)))
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec_())





    