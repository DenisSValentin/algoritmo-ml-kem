# Importar la clase ML_KEM desde el archivo ml_kem.py
from ml_kem import ML_KEM
import timeit

# Main creado para utilizar la interfaz de la clase ML_KEM y pruebas de medición de tiempos de ejecución
if __name__ == "__main__":

    # Utilizar la interfaz por defecto
    ML_KEM.ML_KEM_Interfaz()


    # Utilizar la interfaz con un conjunto de claves encaps-decaps precreadas
    # ML_KEM.establecer_parametros(1)
    # clave_encaps, clave_decaps = ML_KEM.ML_KEM_KeyGen()
    # ML_KEM.ML_KEM_Interfaz(encaps_k=clave_encaps, decaps_k=clave_decaps)


    # Utilizar la interfaz para desencapsular un texto cifrado
    # clave_encaps, clave_decaps = ML_KEM.ML_KEM_KeyGen()
    # clave_secreta, texto_cifrado = ML_KEM.ML_KEM_Encaps(clave_encaps)
    # ML_KEM.ML_KEM_Interfaz(decaps_k=clave_decaps, K=clave_secreta, c=texto_cifrado)


    # Utilizar la interfaz para comparar directamente dos claves secretas
    # clave_encaps, clave_decaps = ML_KEM.ML_KEM_KeyGen()
    # clave_secreta, texto_cifrado = ML_KEM.ML_KEM_Encaps(clave_encaps)
    # clave_secreta_prima = ML_KEM.ML_KEM_Decaps(clave_decaps, texto_cifrado)
    # ML_KEM.ML_KEM_Interfaz(K=clave_secreta, c=texto_cifrado)
    

    # # Prueba de rendimiento de la generación de claves para las distintas configuraciones
    # def medir_ml_kem_keygen():
    #     clave_encaps, clave_decaps = ML_KEM.ML_KEM_KeyGen()

    # # Para el conjunto de parámetros ML-KEM-512
    # ML_KEM.establecer_parametros(1)

    # tiempo = timeit.timeit('medir_ml_kem_keygen()', globals=globals(), number=100)
    # print(f"Tiempo promedio de ejecución (100 repeticiones) para ML-KEM-512: {tiempo/100} segundos")

    # # Prueba de rendimiento de la generación de claves para las distintas configuraciones
    # # Para el conjunto de parámetros ML-KEM-768
    # ML_KEM.establecer_parametros(2)

    # tiempo = timeit.timeit('medir_ml_kem_keygen()', globals=globals(), number=100)
    # print(f"Tiempo promedio de ejecución (100 repeticiones) para ML-KEM-768: {tiempo/100} segundos")

    # # Prueba de rendimiento de la generación de claves para las distintas configuraciones
    # # Para el conjunto de parámetros ML-KEM-1024
    # ML_KEM.establecer_parametros(3)

    # tiempo = timeit.timeit('medir_ml_kem_keygen()', globals=globals(), number=100)
    # print(f"Tiempo promedio de ejecución (100 repeticiones) para ML-KEM-1024: {tiempo/100} segundos")