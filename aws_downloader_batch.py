import pandas as pd
import time
import os
import json
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
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSDownloaderFast:
    def __init__(self, csv_file="Informacion archivos cargados Ruta Costera.csv", download_folder="downloads", batch_size=1500):
        self.csv_file = csv_file
        self.download_folder = download_folder
        self.batch_size = batch_size
        self.driver = None
        self.wait = None
        self.fast_wait = None  # Wait más rápido para elementos comunes
        self.progress_file = "download_progress.json"
        
        # Crear carpeta de descarga
        Path(download_folder).mkdir(exist_ok=True)
        
    def load_progress(self):
        """Cargar progreso guardado"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                logger.info(f"📊 Progreso cargado: {progress['completed']}/{progress['total']} archivos completados")
                return progress
            except Exception as e:
                logger.warning(f"⚠️ Error cargando progreso: {e}")
        
        return {
            'completed': 0,
            'total': 0,
            'current_batch': 1,
            'failed_files': [],
            'successful_files': [],
            'last_processed_file': None,
            'start_time': datetime.now().isoformat()
        }
    
    def save_progress(self, progress):
        """Guardar progreso actual"""
        try:
            progress['last_update'] = datetime.now().isoformat()
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando progreso: {e}")
    
    def setup_driver(self):
        """Configurar Chrome driver optimizado para velocidad"""
        logger.info("🔧 Configurando Chrome driver optimizado...")
        
        chrome_options = Options()
        
        # Configurar carpeta de descarga
        download_path = os.path.abspath(self.download_folder)
        prefs = {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
            # OPTIMIZACIONES PARA VELOCIDAD
            "profile.default_content_setting_values.notifications": 2,  # Bloquear notificaciones
            "profile.managed_default_content_settings.images": 2,  # No cargar imágenes
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Opciones de rendimiento optimizadas
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-images")  # No cargar imágenes
        chrome_options.add_argument("--disable-javascript")  # Deshabilitar JS innecesario
        chrome_options.add_argument("--disable-plugins")  # No cargar plugins
        chrome_options.add_argument("--disable-extensions")  # No cargar extensiones
        chrome_options.add_argument("--no-first-run")  # Saltar configuración inicial
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Instalar y usar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Configurar timeouts optimizados
        self.driver.set_page_load_timeout(15)  # Reducido de 30 a 15 segundos
        self.wait = WebDriverWait(self.driver, 8)  # Reducido de 20 a 8 segundos
        self.fast_wait = WebDriverWait(self.driver, 3)  # Wait rápido para elementos comunes
        
        # Configurar script para evitar detección
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("✅ Chrome driver optimizado configurado")
        
    def load_files_from_csv(self):
        """Cargar lista de archivos desde CSV"""
        logger.info(f"📁 Cargando archivos desde {self.csv_file}")
        
        try:
            if self.csv_file.endswith('.csv'):
                # Detectar separador automáticamente
                with open(self.csv_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                
                if ';' in first_line and first_line.count(';') > first_line.count(','):
                    separator = ';'
                    logger.info("🔍 Detectado separador: punto y coma (;)")
                else:
                    separator = ','
                    logger.info("🔍 Detectado separador: coma (,)")
                
                df = pd.read_csv(self.csv_file, sep=separator)
            else:
                df = pd.read_excel(self.csv_file)
            
            if 'file' not in df.columns:
                logger.error(f"❌ No se encontró la columna 'file'. Columnas disponibles: {list(df.columns)}")
                return []
                
            files = df['file'].dropna().unique().tolist()
            logger.info(f"📊 Se encontraron {len(files)} archivos para descargar")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error leyendo archivo CSV: {e}")
            return []
    
    def get_downloaded_files(self):
        """Obtener lista de archivos ya descargados de forma optimizada"""
        downloaded = set()  # Usar set para búsquedas más rápidas
        if os.path.exists(self.download_folder):
            # Solo obtener nombres de archivos PDF
            for filename in os.listdir(self.download_folder):
                if filename.endswith('.pdf'):
                    downloaded.add(filename)
        logger.info(f"📁 Archivos ya descargados: {len(downloaded)}")
        return downloaded
    
    def wait_for_user_navigation(self, batch_number, total_batches):
        """Esperar a que el usuario navegue manualmente a S3"""
        print("\n" + "="*80)
        print(f"🚀 DESCARGA RÁPIDA - TANDA {batch_number}/{total_batches}")
        print(f"📦 Se procesarán hasta {self.batch_size} archivos en esta tanda")
        print("⚡ MODO OPTIMIZADO: ~3-5 segundos por archivo")
        print("🌐 INSTRUCCIONES:")
        print("1. El navegador se abrirá automáticamente")
        print("2. Navega manualmente a tu bucket de AWS S3")
        print("3. Ve a la carpeta 'legalAspects/files/' (o donde estén tus archivos)")
        print("4. Cuando estés listo, presiona Enter en esta consola")
        print("5. 💾 El progreso se guarda automáticamente cada 5 archivos")
        print("="*80 + "\n")
        
        input("⏳ Presiona Enter cuando estés en la página correcta de S3...")
        logger.info(f"🚀 Iniciando descarga rápida de tanda {batch_number}/{total_batches}")
    
    def search_and_download_file_fast(self, filename, file_number, batch_total, overall_progress):
        """Versión optimizada para buscar y descargar archivos"""
        start_time = time.time()
        
        try:
            # Mostrar progreso más compacto
            if file_number % 10 == 1 or file_number <= 5:  # Solo mostrar detalles cada 10 archivos o primeros 5
                print(f"\n📥 ({file_number}/{batch_total}) - Total: {overall_progress['completed']+1}/{overall_progress['total']}")
                print(f"🔍 {filename[:50]}...")
            else:
                # Progreso en línea compacto
                print(f"📥 {file_number}/{batch_total}", end=" ", flush=True)
            
            # OPTIMIZACIÓN 1: Buscar campo de búsqueda con wait más rápido
            search_box = None
            try:
                # Intentar primero con el selector más común
                search_box = self.fast_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Buscar objetos') or contains(@placeholder, 'Search objects')]"))
                )
            except:
                # Fallback a selectores alternativos
                search_selectors = [
                    "//input[contains(@placeholder, 'buscar')]",
                    "//input[@type='text' and contains(@class, 'search')]"
                ]
                for selector in search_selectors:
                    try:
                        search_box = self.fast_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                        break
                    except:
                        continue
            
            if not search_box:
                print("❌ Campo búsqueda no encontrado")
                return False
            
            # OPTIMIZACIÓN 2: Limpiar y buscar más rápido
            search_box.clear()
            search_box.send_keys(filename)
            search_box.send_keys(Keys.ENTER)
            
            # OPTIMIZACIÓN 3: Espera reducida para resultados
            time.sleep(1.5)  # Reducido de 3 a 1.5 segundos
            
            # OPTIMIZACIÓN 4: Buscar archivo con wait más rápido
            file_link = None
            try:
                # Probar selector más directo primero
                file_link = self.fast_wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{filename}')]"))
                )
            except:
                # Selectores alternativos
                file_selectors = [
                    f"//span[contains(text(), '{filename}')]/ancestor::a",
                    f"//td[contains(text(), '{filename}')]/ancestor::tr//a"
                ]
                for selector in file_selectors:
                    try:
                        file_link = self.fast_wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except:
                        continue
            
            if not file_link:
                print("⚠️ No encontrado")
                return False
            
            # OPTIMIZACIÓN 5: Click y navegación más rápida
            file_link.click()
            time.sleep(1)  # Reducido de 3 a 1 segundo
            
            # OPTIMIZACIÓN 6: Buscar botón de descarga optimizado
            download_button = None
            try:
                # Probar selectores más comunes primero
                download_button = self.fast_wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Descargar') or contains(text(), 'Download')]"))
                )
            except:
                download_selectors = [
                    "//a[contains(text(), 'Descargar') or contains(text(), 'Download')]",
                    "//span[contains(text(), 'Descargar') or contains(text(), 'Download')]/ancestor::button"
                ]
                for selector in download_selectors:
                    try:
                        download_button = self.fast_wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except:
                        continue
            
            if download_button:
                download_button.click()
                
                # OPTIMIZACIÓN 7: Volver atrás más rápido
                time.sleep(0.5)  # Reducido de 2 a 0.5 segundos
                self.driver.back()
                time.sleep(0.5)  # Reducido de 2 a 0.5 segundos
                
                elapsed = time.time() - start_time
                if file_number % 10 == 1 or file_number <= 5:
                    print(f"✅ Descargado en {elapsed:.1f}s")
                else:
                    print("✅", end=" ", flush=True)
                
                return True
            else:
                print("❌ Sin botón descarga")
                self.driver.back()
                time.sleep(0.5)
                return False
                
        except Exception as e:
            elapsed = time.time() - start_time
            if file_number % 10 == 1 or file_number <= 5:
                print(f"❌ Error en {elapsed:.1f}s: {str(e)[:30]}...")
            else:
                print("❌", end=" ", flush=True)
            try:
                self.driver.back()
                time.sleep(0.5)
            except:
                pass
            return False
    
    def download_batch(self, files_batch, batch_number, total_batches, progress):
        """Descargar una tanda de archivos de forma optimizada"""
        self.setup_driver()
        
        try:
            # Abrir navegador y esperar navegación manual
            self.driver.get("https://console.aws.amazon.com")
            self.wait_for_user_navigation(batch_number, total_batches)
            
            batch_successful = 0
            batch_failed = 0
            batch_start_time = time.time()
            
            print(f"\n🚀 Iniciando descarga de {len(files_batch)} archivos...")
            
            # Procesar cada archivo en la tanda
            for i, filename in enumerate(files_batch, 1):
                success = self.search_and_download_file_fast(filename, i, len(files_batch), progress)
                
                if success:
                    batch_successful += 1
                    progress['successful_files'].append(filename)
                else:
                    batch_failed += 1
                    progress['failed_files'].append(filename)
                
                # Actualizar progreso
                progress['completed'] += 1
                progress['last_processed_file'] = filename
                
                # OPTIMIZACIÓN: Guardar progreso cada 5 archivos (en lugar de 10)
                if progress['completed'] % 5 == 0:
                    self.save_progress(progress)
                    elapsed = time.time() - batch_start_time
                    avg_time = elapsed / i
                    remaining = len(files_batch) - i
                    eta = remaining * avg_time
                    print(f"\n💾 Progreso: {progress['completed']}/{progress['total']} | Promedio: {avg_time:.1f}s/archivo | ETA: {eta/60:.1f}min")
                
                # OPTIMIZACIÓN: Sin pausa entre archivos (eliminada time.sleep(1))
            
            # Resumen de la tanda
            total_time = time.time() - batch_start_time
            avg_time = total_time / len(files_batch) if len(files_batch) > 0 else 0
            
            print(f"\n\n📊 RESUMEN TANDA {batch_number}:")
            print(f"Exitosos: {batch_successful}")
            print(f"Fallidos: {batch_failed}")
            print(f"Tiempo total: {total_time/60:.1f} minutos")
            print(f"Tiempo promedio: {avg_time:.1f} segundos/archivo")
            print(f"Total procesado: {progress['completed']}/{progress['total']}")
            
            # Guardar progreso final de la tanda
            progress['current_batch'] = batch_number + 1
            self.save_progress(progress)
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Descarga interrumpida por el usuario en tanda {batch_number}")
            self.save_progress(progress)
            return False
            
        finally:
            print("\n⏳ Cerrando navegador...")
            if self.driver:
                self.driver.quit()
        
        return True
    
    def download_all_files(self):
        """Proceso principal de descarga por tandas optimizado"""
        # Cargar progreso previo
        progress = self.load_progress()
        
        # Cargar todos los archivos
        all_files = self.load_files_from_csv()
        if not all_files:
            return
        
        # Obtener archivos ya descargados para evitar duplicados
        downloaded_files = self.get_downloaded_files()
        
        # OPTIMIZACIÓN: Usar set para filtrado más rápido
        remaining_files = [f for f in all_files if f not in downloaded_files]
        
        # Si es la primera vez, inicializar progreso
        if progress['total'] == 0:
            progress['total'] = len(all_files)
            progress['completed'] = len(downloaded_files)
        
        print(f"\n📊 ESTADO ACTUAL:")
        print(f"Total archivos: {len(all_files)}")
        print(f"Ya descargados: {len(downloaded_files)}")
        print(f"Por descargar: {len(remaining_files)}")
        print(f"Tamaño de tanda: {self.batch_size}")
        
        if len(remaining_files) == 0:
            print("✅ ¡Todos los archivos ya han sido descargados!")
            return
        
        # Dividir en tandas
        total_batches = (len(remaining_files) + self.batch_size - 1) // self.batch_size
        estimated_time = len(remaining_files) * 4 / 60  # 4 segundos promedio por archivo
        print(f"📦 Total de tandas necesarias: {total_batches}")
        print(f"⏱️ Tiempo estimado total: {estimated_time:.1f} minutos")
        
        current_batch = progress.get('current_batch', 1)
        
        # Procesar cada tanda
        for batch_num in range(current_batch, total_batches + 1):
            start_idx = (batch_num - 1) * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(remaining_files))
            files_batch = remaining_files[start_idx:end_idx]
            
            print(f"\n🚀 INICIANDO TANDA {batch_num}/{total_batches}")
            print(f"📁 Archivos en esta tanda: {len(files_batch)}")
            estimated_batch_time = len(files_batch) * 4 / 60
            print(f"⏱️ Tiempo estimado tanda: {estimated_batch_time:.1f} minutos")
            
            # Preguntar si continuar
            if batch_num > 1:
                response = input(f"\n¿Continuar con tanda {batch_num}? (s/n/q para salir): ").lower()
                if response == 'n':
                    print("⏸️ Pausando en esta tanda")
                    break
                elif response == 'q':
                    print("🛑 Saliendo del programa")
                    return
            
            # Descargar la tanda
            success = self.download_batch(files_batch, batch_num, total_batches, progress)
            
            if not success:
                print(f"⚠️ Tanda {batch_num} interrumpida")
                break
            
            print(f"✅ Tanda {batch_num} completada")
            
            # OPTIMIZACIÓN: Pausa reducida entre tandas
            if batch_num < total_batches:
                print(f"\n⏱️ Pausa de 10 segundos antes de la siguiente tanda...")
                time.sleep(10)  # Reducido de 30 a 10 segundos
        
        # Resumen final
        self.print_final_summary(progress)
    
    def print_final_summary(self, progress):
        """Imprimir resumen final"""
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL COMPLETO:")
        print(f"Total archivos: {progress['total']}")
        print(f"Completados: {progress['completed']}")
        print(f"Exitosos: {len(progress['successful_files'])}")
        print(f"Fallidos: {len(progress['failed_files'])}")
        
        if progress['total'] > 0:
            completion_rate = (progress['completed'] / progress['total']) * 100
            print(f"Porcentaje completado: {completion_rate:.1f}%")
        
        print(f"📁 Carpeta de descarga: {os.path.abspath(self.download_folder)}")
        print(f"💾 Archivo de progreso: {self.progress_file}")
        
        if progress['failed_files']:
            print(f"\n❌ Archivos que fallaron ({len(progress['failed_files'])}):")
            for i, file in enumerate(progress['failed_files'][:10]):
                print(f"  {i+1}. {file}")
            if len(progress['failed_files']) > 10:
                print(f"  ... y {len(progress['failed_files']) - 10} más")
        
        print("="*80)

def main():
    """Función principal"""
    print("⚡ AWS S3 File Downloader - VERSIÓN OPTIMIZADA")
    print("="*60)
    print("🚀 Optimizaciones:")
    print("• Timeouts reducidos (8s en lugar de 20s)")
    print("• Sin carga de imágenes/plugins")
    print("• Pausas mínimas entre acciones")
    print("• Progreso cada 5 archivos")
    print("• ~3-5 segundos por archivo")
    print("• Mantiene todas las funcionalidades")
    print("="*60)
    
    csv_file = "Informacion archivos cargados Ruta Costera.csv"
    download_folder = "downloads"
    batch_size = 1500
    
    if not os.path.exists(csv_file):
        print(f"❌ No se encontró el archivo: {csv_file}")
        return
    
    # Crear downloader optimizado
    downloader = AWSDownloaderFast(csv_file, download_folder, batch_size)
    downloader.download_all_files()

if __name__ == "__main__":
    main()
    