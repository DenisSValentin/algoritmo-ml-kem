# Trabajo Fin de Grado de Denis Valentin Stoyanov D'Antonio

## ⚛️ Implementación de ML-KEM (FIPS 203) - Criptografía Post-Cuántica

Este repositorio contiene la implementación en **Python** del algoritmo **Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM)**. Este trabajo fue desarrollado como parte de mi Trabajo de Fin de Grado en Ingeniería Informática en la Universidad de Granada.

El algoritmo implementado corresponde al estándar **FIPS 203**, publicado por el **NIST** (National Institute of Standards and Technology) en agosto de 2024, y está diseñado para ser seguro frente a ataques de ordenadores cuánticos.

---

## 🤔 ¿Por qué este proyecto? El Desafío Post-Cuántico

La computación cuántica, aunque prometedora, representa una amenaza existencial para la criptografía que usamos hoy en día. Algoritmos cuánticos como el de **Shor** y el de **Grover** serán capaces de romper sistemas de cifrado asimétrico (como RSA) y debilitar los simétricos (como AES).

Para solucionar este problema, el NIST inició en 2017 un concurso para estandarizar nuevos algoritmos criptográficos, denominados **post-cuánticos**, que fueran resistentes a estas nuevas amenazas. Este proyecto se enfoca en la implementación de uno de los estándares ganadores.

---

## 🔐 Sobre el Algoritmo ML-KEM

**ML-KEM** es un Mecanismo de Encapsulamiento de Claves (KEM) cuya seguridad se basa en la dificultad de resolver problemas en **retículos** (en inglés, *lattices*), específicamente en el problema de **Module-LWE** (Aprendizaje Modular con Errores).

Este algoritmo es una evolución directa de **CRYSTALS-Kyber**, uno de los primeros algoritmos estandarizados por el NIST en 2022, e introduce mejoras y comprobaciones adicionales para robustecer su seguridad.

---

## ✨ Características del Proyecto

* **Implementación Completa en Python:** El algoritmo está desarrollado íntegramente en Python, utilizando una estructura de clase (`ML-KEM`) que encapsula toda la lógica.
* **Soporte para los 3 Niveles de Seguridad:** Incluye los tres conjuntos de parámetros oficiales definidos en el estándar FIPS 203:
    * `ML-KEM-512` (Categoría de Seguridad 1)
    * `ML-KEM-768` (Categoría de Seguridad 3 - Usado por defecto)
    * `ML-KEM-1024` (Categoría de Seguridad 5)
* **Librerías Eficientes:** Utiliza **NumPy** para las complejas operaciones con vectores y matrices y **hashlib** para las funciones hash requeridas (SHA3, SHAKE).
* **Interfaz Interactiva:** Se ha desarrollado una interfaz de usuario por consola para probar de forma sencilla e intuitiva todas las funcionalidades del algoritmo: generar claves, encapsular, desencapsular y comparar los resultados.

---
## 🎓 Objetivos del Trabajo de Fin de Grado

Este proyecto se realizó para cumplir con los siguientes objetivos académicos:

* Analizar el estado actual de la criptografía.
* Explicar los fundamentos de la computación cuántica y su amenaza.
* Investigar el concurso de estandarización post-cuántica del NIST.
* Introducir los problemas matemáticos basados en retículos.
* Seleccionar y desarrollar teóricamente un algoritmo KEM basado en retículos (ML-KEM).
* Implementar el algoritmo seleccionado (este repositorio).
* Implementar una interfaz de usuario para el algoritmo.
* Comprobar el correcto funcionamiento del algoritmo.
* Extraer conclusiones sobre el desarrollo y el aprendizaje obtenido.

---

## 🚀 Cómo Ejecutar el Algoritmo

### Prerrequisitos
* Python 3.x

### Instalación

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/DenisSValentin/Algoritmo_ML-KEM.git](https://github.com/DenisSValentin/Algoritmo_ML-KEM.git)
    cd Algoritmo_ML-KEM
    ```
2.  Instala las dependencias necesarias:
    ```bash
    pip install numpy
    ```
    *(La librería `hashlib` viene incluida con Python)*

### Uso

Para ejecutar el algoritmo, puedes utilizar la interfaz interactiva. Desde la raíz del proyecto, ejecuta el archivo principal:
```bash
python ml_kem_main.py
```
Esto lanzará un menú en la consola desde donde podrás probar todas las funcionalidades del algoritmo ML-KEM.
