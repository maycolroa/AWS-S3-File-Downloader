import pandas as pd
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSDownloader:
    def __init__(self, csv_file="Informacion archivos cargados Ruta Costera.csv", download_folder="downloads_test"):
        self.csv_file = csv_file
        self.download_folder = download_folder
        self.driver = None
        self.wait = None
        
        # Crear carpeta de descarga
        Path(download_folder).mkdir(exist_ok=True)
        
    def setup_driver(self):
        """Configurar Chrome driver con opciones optimizadas"""
        logger.info("🔧 Configurando Chrome driver...")
        
        chrome_options = Options()
        
        # Configurar carpeta de descarga
        download_path = os.path.abspath(self.download_folder)
        prefs = {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Opciones adicionales para mejor rendimiento
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Instalar y usar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Configurar script para evitar detección
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 20)
        logger.info("✅ Chrome driver configurado correctamente")
        
    def load_files_from_csv(self):
        """Cargar lista de archivos desde CSV"""
        logger.info(f"📁 Cargando archivos desde {self.csv_file}")
        
        try:
            if self.csv_file.endswith('.csv'):
                # Intentar múltiples estrategias de lectura
                try:
                    # Estrategia 1: Detectar separador automáticamente
                    # Leer primera línea para detectar separador
                    with open(self.csv_file, 'r', encoding='utf-8') as f:
                        first_line = f.readline()
                    
                    # Detectar separador
                    if ';' in first_line and first_line.count(';') > first_line.count(','):
                        separator = ';'
                        logger.info("🔍 Detectado separador: punto y coma (;)")
                    else:
                        separator = ','
                        logger.info("🔍 Detectado separador: coma (,)")
                    
                    df = pd.read_csv(self.csv_file, sep=separator)
                    
                except Exception as e1:
                    logger.warning(f"⚠️ Estrategia 1 falló: {e1}")
                    try:
                        # Estrategia 2: Forzar punto y coma
                        df = pd.read_csv(self.csv_file, sep=';')
                        logger.info("🔧 Usando separador forzado: punto y coma (;)")
                    except Exception as e2:
                        logger.warning(f"⚠️ Estrategia 2 falló: {e2}")
                        try:
                            # Estrategia 3: Forzar coma
                            df = pd.read_csv(self.csv_file, sep=',')
                            logger.info("🔧 Usando separador forzado: coma (,)")
                        except Exception as e3:
                            logger.warning(f"⚠️ Estrategia 3 falló: {e3}")
                            # Estrategia 4: Con engine python (más lento pero más robusto)
                            df = pd.read_csv(
                                self.csv_file,
                                engine='python',
                                sep=None,  # Auto-detectar separador
                                on_bad_lines='skip'
                            )
                            logger.info("🔧 Usando auto-detección de separador")
            else:
                df = pd.read_excel(self.csv_file)
            
            # Verificar columnas
            logger.info(f"📋 Columnas encontradas: {list(df.columns)}")
            
            if 'file' not in df.columns:
                logger.error(f"❌ No se encontró la columna 'file'. Columnas disponibles: {list(df.columns)}")
                return []
                
            files = df['file'].dropna().unique().tolist()
            logger.info(f"📊 Se encontraron {len(files)} archivos para descargar")
            
            # Mostrar algunas muestras para verificar
            if files:
                logger.info(f"📄 Ejemplos de archivos encontrados:")
                for i, file in enumerate(files[:3]):
                    logger.info(f"  {i+1}. {file}")
                if len(files) > 3:
                    logger.info(f"  ... y {len(files) - 3} más")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error leyendo archivo CSV: {e}")
            return self._read_csv_manual()
    
    def _read_csv_manual(self):
        """Leer CSV manualmente línea por línea como backup"""
        logger.info("🔧 Intentando lectura manual del CSV...")
        
        files = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Buscar la línea de headers y detectar separador
            header_line = None
            file_column_index = None
            separator = ','
            
            for i, line in enumerate(lines[:10]):  # Buscar en las primeras 10 líneas
                if 'file' in line.lower():
                    header_line = i
                    
                    # Detectar separador
                    if ';' in line and line.count(';') > line.count(','):
                        separator = ';'
                        logger.info("🔍 Separador detectado en lectura manual: punto y coma (;)")
                    else:
                        separator = ','
                        logger.info("🔍 Separador detectado en lectura manual: coma (,)")
                    
                    headers = [h.strip().strip('"') for h in line.strip().split(separator)]
                    if 'file' in headers:
                        file_column_index = headers.index('file')
                        break
            
            if file_column_index is None:
                logger.error("❌ No se encontró la columna 'file' en el archivo")
                return []
            
            logger.info(f"📍 Columna 'file' encontrada en posición {file_column_index}")
            
            # Leer los datos
            for i, line in enumerate(lines[header_line + 1:], header_line + 2):
                try:
                    # Dividir la línea por el separador detectado
                    if separator == ';':
                        parts = [part.strip().strip('"') for part in line.strip().split(';')]
                    else:
                        # Para comas, manejar comillas
                        parts = []
                        current_part = ""
                        inside_quotes = False
                        
                        for char in line.strip():
                            if char == '"':
                                inside_quotes = not inside_quotes
                            elif char == ',' and not inside_quotes:
                                parts.append(current_part.strip().strip('"'))
                                current_part = ""
                            else:
                                current_part += char
                        
                        if current_part:
                            parts.append(current_part.strip().strip('"'))
                    
                    # Extraer el archivo si hay suficientes columnas
                    if len(parts) > file_column_index and parts[file_column_index].strip():
                        file_name = parts[file_column_index].strip()
                        if file_name and file_name != 'file':
                            files.append(file_name)
                
                except Exception as e:
                    logger.warning(f"⚠️ Error en línea {i}: {e}")
                    continue
            
            # Eliminar duplicados
            files = list(set(files))
            logger.info(f"📊 Lectura manual completada: {len(files)} archivos únicos encontrados")
            
            # Mostrar ejemplos
            if files:
                logger.info(f"📄 Ejemplos de archivos encontrados:")
                for i, file in enumerate(files[:3]):
                    logger.info(f"  {i+1}. {file}")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error en lectura manual: {e}")
            return []
    
    def wait_for_user_navigation(self):
        """Esperar a que el usuario navegue manualmente a S3"""
        print("\n" + "="*60)
        print("🧪 MODO PRUEBA - INSTRUCCIONES:")
        print("1. El navegador se abrirá automáticamente")
        print("2. Navega manualmente a tu bucket de AWS S3")
        print("3. Ve a la carpeta 'legalAspects/files/' (o donde estén tus archivos)")
        print("4. Cuando estés listo, presiona Enter en esta consola")
        print("5. 🛡️ SOLO SE DESCARGARÁN 5 ARCHIVOS COMO PRUEBA")
        print("="*60 + "\n")
        
        input("⏳ Presiona Enter cuando estés en la página correcta de S3...")
        logger.info("🚀 Iniciando proceso de descarga automática - MODO PRUEBA")
    
    def search_and_download_file(self, filename, file_number, total_files):
        """Buscar y descargar un archivo específico"""
        try:
            print(f"\n🔍 PRUEBA ({file_number}/{total_files}): {filename}")
            print("   ⏳ Presiona Ctrl+C si quieres parar la prueba...")
            
            # Buscar el campo de búsqueda con múltiples selectores
            search_selectors = [
                "//input[contains(@placeholder, 'Buscar objetos')]",
                "//input[contains(@placeholder, 'Search objects')]",
                "//input[contains(@placeholder, 'buscar')]",
                "//input[@type='text' and contains(@class, 'search')]"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if not search_box:
                print(f"   ❌ No se encontró el campo de búsqueda")
                return False
            
            print(f"   🔍 Buscando archivo...")
            # Limpiar búsqueda anterior y buscar archivo
            search_box.clear()
            time.sleep(0.5)
            search_box.send_keys(filename)
            search_box.send_keys(Keys.ENTER)
            
            # Esperar resultados
            time.sleep(3)
            
            # Buscar el archivo en los resultados
            file_selectors = [
                f"//a[contains(text(), '{filename}')]",
                f"//span[contains(text(), '{filename}')]/ancestor::a",
                f"//td[contains(text(), '{filename}')]/ancestor::tr//a"
            ]
            
            file_link = None
            for selector in file_selectors:
                try:
                    file_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if not file_link:
                print(f"   ⚠️ No se encontró el archivo en los resultados")
                return False
            
            print(f"   📁 Archivo encontrado, abriendo...")
            # Click en el archivo
            file_link.click()
            time.sleep(3)
            
            # Buscar botón de descarga
            download_selectors = [
                "//button[contains(text(), 'Descargar')]",
                "//button[contains(text(), 'Download')]",
                "//a[contains(text(), 'Descargar')]",
                "//a[contains(text(), 'Download')]",
                "//span[contains(text(), 'Descargar')]/ancestor::button",
                "//span[contains(text(), 'Download')]/ancestor::button"
            ]
            
            download_button = None
            for selector in download_selectors:
                try:
                    download_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except:
                    continue
            
            if download_button:
                print(f"   ⬇️ Iniciando descarga...")
                download_button.click()
                print(f"   ✅ ÉXITO: Descarga iniciada")
                time.sleep(2)
                
                # Volver a la lista
                self.driver.back()
                time.sleep(2)
                return True
            else:
                print(f"   ❌ No se encontró botón de descarga")
                self.driver.back()
                time.sleep(2)
                return False
                
        except Exception as e:
            print(f"   ❌ Error procesando archivo: {e}")
            try:
                self.driver.back()
                time.sleep(2)
            except:
                pass
            return False
    
    def download_test_files(self, max_files=5):
        """Proceso de prueba con pocos archivos"""
        files_to_download = self.load_files_from_csv()
        if not files_to_download:
            return
        
        # LIMITACIÓN PARA PRUEBA
        files_to_download = files_to_download[:max_files]
        print(f"\n🧪 MODO PRUEBA: Solo procesando {len(files_to_download)} archivos")
        print(f"📁 Los archivos se guardarán en: {os.path.abspath(self.download_folder)}")
        
        self.setup_driver()
        
        try:
            # Abrir navegador y esperar navegación manual
            self.driver.get("https://console.aws.amazon.com")
            self.wait_for_user_navigation()
            
            successful_downloads = 0
            failed_downloads = []
            
            # Procesar cada archivo
            for i, filename in enumerate(files_to_download, 1):
                success = self.search_and_download_file(filename, i, len(files_to_download))
                
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads.append(filename)
                
                # Pausa más larga en modo prueba
                print("   ⏱️ Esperando 3 segundos antes del siguiente...")
                time.sleep(3)
            
            # Resumen de prueba
            print("\n" + "="*60)
            print("🧪 RESUMEN DE PRUEBA:")
            print(f"Archivos probados: {len(files_to_download)}")
            print(f"Descargas exitosas: {successful_downloads}")
            print(f"Fallos: {len(failed_downloads)}")
            if len(files_to_download) > 0:
                print(f"Tasa de éxito: {(successful_downloads/len(files_to_download)*100):.1f}%")
            
            if failed_downloads:
                print(f"\n❌ Archivos que fallaron:")
                for file in failed_downloads:
                    print(f"  - {file}")
            
            if successful_downloads > 0:
                print(f"\n✅ ¡PRUEBA EXITOSA! El sistema funciona.")
                print(f"📁 Revisa tu carpeta '{self.download_folder}/' para confirmar")
                print(f"🚀 Si todo está bien, puedes ejecutar la versión completa")
            else:
                print(f"\n⚠️ Ninguna descarga fue exitosa. Revisa la configuración.")
            
            print("="*60)
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Prueba interrumpida por el usuario")
            print(f"📊 Descargas completadas hasta ahora: {successful_downloads}")
            
        finally:
            print("\n⏳ Esperando 10 segundos antes de cerrar...")
            time.sleep(10)
            if self.driver:
                self.driver.quit()

def main():
    """Función principal MODO PRUEBA"""
    print("🧪 AWS S3 File Downloader - MODO PRUEBA")
    print("="*50)
    print("🛡️ Esta versión solo descargará 5 archivos como prueba")
    print("📁 Los archivos se guardarán en 'downloads_test/'")
    print("="*50)
    
    csv_file = "Informacion archivos cargados Ruta Costera.csv"
    download_folder = "downloads_test"  # Carpeta diferente para pruebas
    
    if not os.path.exists(csv_file):
        print(f"❌ No se encontró el archivo: {csv_file}")
        print("📁 Archivos disponibles en el directorio:")
        for file in os.listdir("."):
            if file.endswith(('.csv', '.xlsx', '.xls')):
                print(f"  - {file}")
        return
    
    # Crear downloader para prueba
    downloader = AWSDownloader(csv_file, download_folder)
    downloader.download_test_files(max_files=5)  # Solo 5 archivos

if __name__ == "__main__":
    main()
    