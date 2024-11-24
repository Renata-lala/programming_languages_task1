import http.client
import urllib.parse
import os
import argparse
import threading
import time

# python main.py https://f1.2rsload.ru/files/load4/061/MathType-RSLOAD.NET-.rar


class FileDownloader:
    def __init__(self, url):
        """
        Инициализация загрузчика файла.
        :param url: URL для скачивания.
        """
        self.url = url
        self.parsed_url = urllib.parse.urlparse(url)
        # Получаем имя файла из пути URL, если оно отсутствует, используем дефолтное имя.
        self.file_name = os.path.basename(self.parsed_url.path) or "downloaded_file"
        self.downloaded_bytes = 0  # Общее количество загруженных байтов.
        self.stop_event = threading.Event()  # Событие для остановки потоков.
        self.lock = threading.Lock()  # Блокировка для синхронизации доступа к общим данным.

    def download(self):
        """
        Метод скачивания файла.
        """
        try:
            # Выбор класса соединения (HTTP или HTTPS).
            conn_class = http.client.HTTPSConnection if self.parsed_url.scheme == 'https' else http.client.HTTPConnection
            conn = conn_class(self.parsed_url.netloc)

            # Отправляем GET-запрос.
            conn.request("GET", self.parsed_url.path or "/")
            response = conn.getresponse()

            # Проверяем статус ответа. Если не 200, завершаем с ошибкой.
            if response.status != 200:
                print(f"Неудалось скачать файл: {response.status} {response.reason}")
                return

            # Открываем файл для записи в бинарном режиме.
            with open(self.file_name, "wb") as f:
                while not self.stop_event.is_set():
                    # Читаем данные по частям (1024 байта).
                    chunk = response.read(1024)
                    if not chunk:
                        break  # Если данных больше нет, завершаем загрузку.
                    # Синхронизация доступа к счетчику загруженных байтов.
                    with self.lock:
                        self.downloaded_bytes += len(chunk)
                    f.write(chunk)  # Записываем данные в файл.

            print(f"Загрузка завершенна: {self.file_name}")
        except Exception as e:
            # Обрабатываем ошибки и выводим сообщение.
            print(f"Ошибка во время скачивания файла: {e}")
        finally:
            # Устанавливаем событие остановки потоков.
            self.stop_event.set()

    def report_progress(self):
        """
        Метод для отображения прогресса загрузки.
        Каждую секунду выводит количество загруженных байтов.
        """
        while not self.stop_event.is_set():
            # Синхронизация доступа к счетчику.
            with self.lock:
                print(f"Загружено {self.downloaded_bytes} байтов")
            time.sleep(1)  # Задержка на 1 секунду.

    def start(self):
        """
        Запуск потоков для скачивания файла и отображения прогресса.
        """
        # Создаем потоки для скачивания и вывода прогресса.
        download_thread = threading.Thread(target=self.download)
        progress_thread = threading.Thread(target=self.report_progress)

        # Запускаем потоки.
        download_thread.start()
        progress_thread.start()

        # Ожидаем завершения потока скачивания.
        download_thread.join()
        # Устанавливаем событие остановки для потока прогресса.
        self.stop_event.set()
        # Ожидаем завершения потока прогресса.
        progress_thread.join()


def main():
    """
    Основной метод программы.
    """
    # Парсинг аргументов командной строки.
    parser = argparse.ArgumentParser(description="Загрузка файла и визуализация прогресса.")
    parser.add_argument("url", help="URL файла для скачивания")  # URL файла.
    args = parser.parse_args()

    # Создаем и запускаем загрузчик файла.
    downloader = FileDownloader(args.url)
    downloader.start()


if __name__ == "__main__":
    # Точка входа в программу.
    main()
