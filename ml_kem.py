import numpy as np
import hashlib

"""
    Clase que engloba todas las constantes, variables, métodos privados y métodos públicos
    para hacer funcionar correctamente el algoritmo ML-KEM.

    Las únicas funciones públicas que tiene esta clase son:
        establecer_parametros(x)
        ML_KEM_KeyGen()
        ML_KEM_Encaps(ek)
        ML_KEM_Decaps(dk, c)
        ML_KEM_Interfaz(encaps_k=None, decaps_k=None, K=None, K_prima=None, c=None)
"""
class ML_KEM:

    # CONSTANTES GLOBALES
    n = 256
    q = 3329

    # VARIABLES GLOBALES: Por defecto ML-KEM-768
    k = 3
    eta_1 = 2
    eta_2 = 2
    d_u = 10
    d_v = 4

    # CLAVES DE ENCAPSULAMIENTO Y DESENCAPSULAMIENTO DE LA EJECUCIÓN
    encaps_k = np.zeros(384*k+32, dtype=np.uint8)
    decaps_k = np.zeros(768*k+96, dtype=np.uint8)

    # Array necesario para calcular tanto NTT como NTT^-1
    _ArrayBitRev = np.array([
        1, 1729, 2580, 3289, 2642, 630, 1897, 848, 1062, 1919, 193, 797, 2786, 3260, 569,
        1746, 296, 2447, 1339, 1476, 3046, 56, 2240, 1333, 1426, 2094, 535, 2882, 2393, 2879,
        1974, 821, 289, 331, 3253, 1756, 1197, 2304, 2277, 2055, 650, 1977, 2513, 632, 2865,
        33, 1320, 1915, 2319, 1435, 807, 452, 1438, 2868, 1534, 2402, 2647, 2617, 1481, 648,
        2474, 3110, 1227, 910, 17, 2761, 583, 2649, 1637, 723, 2288, 1100, 1409, 2662, 3281,
        233, 756, 2156, 3015, 3050, 1703, 1651, 2789, 1789, 1847, 952, 1461, 2687, 939, 2308,
        2437, 2388, 733, 2337, 268, 641, 1584, 2298, 2037, 3220, 375, 2549, 2090, 1645, 1063,
        319, 2773, 757, 2099, 561, 2466, 2594, 2804, 1092, 403, 1026, 1143, 2150, 2775, 886,
        1722, 1212, 1874, 1029, 2110, 2935, 885, 2154
    ], dtype=np.int64)

    # Array necesario para calcular la multiplicación entre dos representaciones NTT
    _ArrayBitRev_Multiply = np.array([
        17, 3312, 2761, 568, 583, 2746, 2649, 680, 1637, 1692, 723, 2606, 2288, 1041, 1100,
        2229, 1409, 1920, 2662, 667, 3281, 48, 233, 3096, 756, 2573, 2156, 1173, 3015, 314,
        3050, 279, 1703, 1626, 1651, 1678, 2789, 540, 1789, 1540, 1847, 1482, 952, 2377, 1461,
        1868, 2687, 642, 939, 2390, 2308, 1021, 2437, 892, 2388, 941, 733, 2596, 2337, 992,
        268, 3061, 641, 2688, 1584, 1745, 2298, 1031, 2037, 1292, 3220, 109, 375, 2954, 2549,
        780, 2090, 1239, 1645, 1684, 1063, 2266, 319, 3010, 2773, 556, 757, 2572, 2099, 1230,
        561, 2768, 2466, 863, 2594, 735, 2804, 525, 1092, 2237, 403, 2926, 1026, 2303, 1143,
        2186, 2150, 1179, 2775, 554, 886, 2443, 1722, 1607, 1212, 2117, 1874, 1455, 1029, 2300,
        2110, 1219, 2935, 394, 885, 2444, 2154, 1175
    ], dtype=np.int64)

    ############################ MÉTODOS PRIVADOS ############################

    """
        Calcula el hash SHAKE256 de un array de 33 bytes y genera una salida pseudorandom
        cuya longitud depende del parámetro eta.

        Input:
            eta:
             Tipo: int
             Longitud: 1
             Descripción: Indica el multiplicador de la longitud de la salida deseada, eta = 2 o 3.
            
            s:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Entrada de 32 bytes.

            b:
             Tipo: numpy array, dtype = uint8
             Longitud: 1
             Descripción: Entrada de 1 byte.

        Output:
            shaked_bytes:
             Tipo: numpy array, dtype = uint8
             Longitud: 64*eta
             Descripción: Salida pseudorandom de (64*eta) bytes del hash calculado.
    """
    @staticmethod
    def _PRF(eta, s, b):
        # Concatenamos los datos de entrada para obtener un solo array de 33 bytes (32+1)
        datos_entrada = np.concatenate((s, b))

        # Calculamos la longitud deseada de salida gracias al parámetro eta
        longitud_salida = 64 * eta

        # Calculamos el hash SHAKE256 y generamos la salida con la longitud deseada
        shake = hashlib.shake_256(datos_entrada).digest(longitud_salida)

        #Convertimos el resultado a np.uint8
        shaked_bytes = np.frombuffer(shake, dtype=np.uint8)

        return shaked_bytes


    """
        Calcula el hash SHA3-256 a un array de bytes de longitud variable e imprime
        un array de 32 bytes de longitud.
        
        Input:
            s:
             Tipo: numpy array, dtype = uint8
             Longitud: Variable
             Descripción: Array de bytes de longitud variable.
        
        Output:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Salida de 32 bytes del hash calculado.
    """
    @staticmethod
    def _H(s):
        # Calculamos el hash SHA3-256 y generamos la salida de 32 bytes
        hash_output = hashlib.sha3_256(s).digest()

        return np.frombuffer(hash_output, dtype=np.uint8)


    """
        Calcula el hash SHAKE256 a un array de bytes longitud variable e imprime
        un array de 32 bytes de longitud.
        
        Input:
            s:
             Tipo: numpy array, dtype = uint8
             Longitud: Variable
             Descripción: Array de bytes de longitud variable.
        
        Output:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Salida de 32 bytes del hash calculado.
    """
    @staticmethod
    def _J(s):
        # Calculamos el hash SHAKE256 y generamos la salida de 32 bytes
        hash_output = hashlib.shake_256(s).digest(32)

        return np.frombuffer(hash_output, dtype=np.uint8)


    """
        Calcula el hash SHA3-512 a una entrada de bytes de longitud variable y
        produce como salida dos numpy array de 32 bytes cada uno (el hash tiene 64 bytes).
        
        Input:
            c:
             Tipo: numpy array, dtype = uint8
             Longitud: Variable
             Descripción: Array de bytes de longitud variable.
        
        Output:
            a:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Primeros 32 bytes del hash sha3_512.
            
            b:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Últimos 32 bytes del hash sha3_512.
    """
    @staticmethod
    def _G(c):
        # Calculamos el hash SHA3-512
        hash_output = hashlib.sha3_512(c).digest()

        # Generamos las dos salidas de 32 bytes
        a = np.frombuffer(hash_output[:32], dtype=np.uint8)
        b = np.frombuffer(hash_output[32:], dtype=np.uint8)

        return a, b


    """
        Toma un entero i en el rango {0, ..., 127}, invierte el orden de sus bits y
        devuelve el entero resultante.
        
        Input:
            i:
             Tipo: int
             Longitud: 1
             Descripción: Un entero entre 0 y 127.
        
        Output:
            bits_invertidos:
             Tipo: int
             Longitud: 1
             Descripción: El entero resultante de invertir los bits de i.
    """
    @staticmethod
    def _BitRev7(i):
        # Verificamos que el valor a invertir esté en el rango 0-127 que es lo que se puede represntar con 7 bits
        if not (0 <= i < 128):
            raise ValueError("El valor de entrada debe estar entre 0 y 127 (7 bits)")

        # Pasamos de un entero a representación de 7 bits
        bit_string = f'{i:07b}'

        #Invertimos el orden del string de bits
        bits_invertidos = bit_string[::-1]
        
        # Convertimos el string de bits a un entero
        bits_invertidos = int(bits_invertidos, 2)

        return bits_invertidos


    """
        Convierte un array de bits (longitud 8*x) en un array de bytes (longitud x).

        Input:
            b:
             Tipo: numpy array, dtype = uint8
             Longitud: 8*x
             Descripción: Array de bits con longitud múltiplo de 8.

        Output:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: 8*x // 8
             Descripción: Array de bytes producido de pasar de bits a bytes.
    """
    @staticmethod
    def _BitsToBytes(b):
        # Calculamos la longitud que tendrá el array de bytes
        x = len(b) // 8

        # Inicializamos el array de bytes de longitud n con ceros
        B = np.zeros(x, dtype=np.uint8)

        # Calculamos el valor de cada byte
        for i in range(len(b)): 
            B[i//8] = B[i//8] + b[i] * pow(2, i % 8) # Si b[i] es 1, suma el valor de esa posición del bit
        
        return B


    """
        Convierte un array de bytes (longitud x) en un array de bits (longitud 8*x).

        Input:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: x
             Descripción: Array de bytes.

        Output:
            b:
             Tipo: numpy array, dtype = uint8
             Longitud: 8*x
             Descripción: Array de bits producido al pasar de bytes a bits.
    """
    @staticmethod
    def _BytesToBits(B):
        # Extraemos la longitud del array de bytes y creamos el array de bits con esa longitud*8
        n = len(B)
        b = np.zeros(n * 8, dtype=np.uint8)

        # Copiamos el array para su modificación
        C = B.copy()

        # Ponemos el bit a 0 o 1 dependiendo del %2 del valor del byte en ese momento y nos desplazamos dividiendolo entre 2
        for i in range(n):
            for j in range(8):
                b[8*i + j] = C[i] % 2
                C[i] = C[i]//2
        return b


    """
        Comprime un valor de Z_q a un valor en Z_(2^d), con 1<=d<12.

        Input:
            x:
             Tipo: np.int64
             Longitud: 1
             Descripción: Un valor en Z_q.

            d:
             Tipo: np.int64
             Longitud: 1
             Descripción: Parámetro de compresión {1 <= d < 12}.

        Output:
             Tipo: np.int64
             Longitud: 1
             Descripción: Valor comprimido en Z_(2^d).
    """
    @staticmethod
    def _Compress(x, d):
        return round(((2**d) / ML_KEM.q) * x) % (2**d)


    """
        Descomprime un valor de Z_(2^d) a un valor en Z_q con 1<=d<12.

        Input:
            y:
             Tipo: np.int64 
             Longitud: 1
             Descripción: Valor en Z_(2^d).

            d:
             Tipo: np.int64
             Longitud: 1
             Descripción: Parámetro de descompresión {1 <= d < 12}.

        Output:
             Tipo: np.int64
             Longitud: 1
             Descripción: Valor descomprimido en Z_q.
    """
    @staticmethod
    def _Decompress(y, d):
        return round((ML_KEM.q / (2**d)) * y)


    """
        Codifica un array de 256 enteros en un array de 32*d bytes.
        d indica de cuántos en cuántos bits se cogerán de cada entero para después representar el byte.

        Input:
            F:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de enteros en Z_{2^d} para d<12 y Z_q para d = 12.
            
            d: 
             Tipo: int
             Longitud: 1
             Descripción: El número de bits utilizado para codificar cada entero, con d={1-12}

        Output:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*d
             Descripción: Array de bytes codificado.
    """
    @staticmethod
    def _ByteEncode(F, d):
        # Creamos un array con el número de bits que vamos a necesitar
        b = np.zeros(ML_KEM.n * d, dtype=np.uint8)

        # Calculamos su representación en bits parecido a BitsToBytes pero en lugar de con 8, con d
        for i in range(ML_KEM.n):
            a = F[i]
            for j in range(d):
                b[i*d + j] = a % 2
                a = (a - b[i*d + j]) // 2

        # Finalmente convertimos el array de bits obtenido a bytes (de 8 en 8)
        B = np.zeros((ML_KEM.n * d) // 8, dtype=np.uint8)
        B = ML_KEM._BitsToBytes(b)

        return B


    """
        Descodifica un array de 32*d bytes en un array de 256 enteros.
        d indica de cuántos en cuántos bits se cogerán para representar los enteros.

        Input:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*d
             Descripción: Array de bytes codificado.

            d:
             Tipo: int
             Longitud: 1
             Descripción: El número de bits utilizado para representar cada entero, con d={1-12}

        Output:
            F:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de enteros decodificados en Z_{2^d} para d<12 y Z_q para d = 12.
    """
    @staticmethod
    def _ByteDecode(B, d):
        # Primero convertimos el array a bits para poder trabajar de d en d bits
        b = ML_KEM._BytesToBits(B)

        # Si d es <12, podemos decodificar hasta 2^d, si no, debemos truncar en q
        m = 2**d if d < 12 else ML_KEM.q

        # Regeneramos el valor de F[i] igual que hacíamos para regenerar el valor de los bytes en BitsToBytes
        F = np.zeros(ML_KEM.n, dtype=np.int64)
        for i in range(ML_KEM.n):
            for j in range(d):
                F[i] = (F[i] + b[i*d + j] * pow(2, j)) % m 

        return F


    """
        Convierte un array de 34 bytes formado por una semilla de 32 bytes + 2 indices (1byte cada uno)
        en un polinomio en la representación NTT.

        Input:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: 34
             Descripción: Array de 32 bytes aleatorios (semilla) + 2 índices. 

        Output:
            a_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de coeficientes en Z_q.
    """
    @staticmethod
    def _SampleNTT(B):
        # Calcula el hash shake_128 con el array de bytes B
        ctx = hashlib.shake_128()
        ctx.update(B.tobytes())

        # Generamos el máximo de posibles bytes necesarios, 280 iteraciones máxima * 3 bytes utilizados por iteración
        C_total = ctx.digest(840)

        # Rellena a_hat con los valores d1 y d2 calculados a partir de los valores aleatorios extraidos en C
        a_hat = np.zeros(256, dtype=np.int64)
        j = 0
        i = 0
        while j < 256:
            # Extraemos 3 bytes pseudoaleatorios
            C = C_total[i:i+3]

            # Calculamos los coeficientes d1 y d2
            d1 = C[0] + 256 * (C[1] % 16)
            d2 = (C[1] // 16) + 16 * C[2]

            if d1 < ML_KEM.q:
                a_hat[j] = np.int64(d1)
                j += 1

            if d2 < ML_KEM.q and j < 256:
                a_hat[j] = np.int64(d2)
                j += 1
            
            # Avanzamos a los siguientes 3 bytes pseudoaleatorios
            i = i+3

        return a_hat


    """
        Si la entrada es una semilla de bytes aleatorios uniformemente distribuidos, la salida es
        un array con los 256 coeficientes en Z_q de la distribución D_eta(R_q).

        Input:
            B:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Array de 32 bytes aleatorios (semilla).

        Output:
            f:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripcióon: Array de coeficientes en Z_q.
    """
    @staticmethod
    def _SamplePolyCBD(B, eta):
        # Transformamos el array de bytes a bits 
        b = ML_KEM._BytesToBits(B)
        f = np.zeros(256, dtype=np.int64)

        # f[i] tiene el valor (x-y)%q y x e y solo pueden alcanzar 'eta' valor cada vez
        for i in range(256):
            x = 0
            y = 0
            for j in range(eta):
                x += b[2 * eta * i + j]
                y += b[2 * eta * i + eta + j]
            f[i] = (x - y) % ML_KEM.q

        return f


    """
        Calcula la representación NTT de un polinomio f que está en R_q.
        
        Input:
            f:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q.

        Output:
            f_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, que representa la NTT de f.
    """
    @staticmethod
    def _NTT(f):
        # Copiamos el contenido del array para crear f_hat
        f_hat = f.copy()

        # Organizamos el array en segmentos de longitud len_ y procesamos los valores de las posiciones por pares
        i = 1
        len_ = 128
        while len_ >= 2:
            for start in range(0, 256, 2 * len_):
                zeta = ML_KEM._ArrayBitRev[i]
                i += 1
                for j in range(start, start + len_):
                    t = (zeta * f_hat[j + len_]) % ML_KEM.q
                    f_hat[j + len_] = (f_hat[j] - t) % ML_KEM.q
                    f_hat[j] = (f_hat[j] + t) % ML_KEM.q
            len_ = len_ // 2

        return f_hat


    """
        Dado f_hat en T_q, que está en representación NTT, se calcula su inversa para obtener el polinomio f en R_q.
        
        Input:
            f_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, que representa la NTT de un polinomio f.

        Output:
            f:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, que representa el polinomio original.
    """
    @staticmethod
    def _InverseNTT(f_hat):
        # Copiamos el contenido del array para crear f_hat
        f = f_hat.copy()

        # Organizamos el array en segmentos de longitud len_ y procesamos los valores de las posiciones, aplicando las operaciones inversas a la NTT
        i = 127
        len_ = 2
        while len_ <= 128:
            for start in range(0, 256, 2 * len_):
                zeta = ML_KEM._ArrayBitRev[i]
                i -= 1
                for j in range(start, start + len_):
                    t = f[j]
                    f[j] = (t + f[j + len_]) % ML_KEM.q
                    f[j + len_] = (zeta * (f[j + len_] - t)) % ML_KEM.q
            len_ = len_ * 2
        for i in range(256):
            f[i] = (f[i] * 3303) % ML_KEM.q

        return f


    """
        Calcula el producto de dos polinomios de grado uno respecto a un módulo cuadrático.
        
        Input:
            a0, a1, b0, b1:
             Tipo: np.int64
             Longitud: 1 (cada uno)
             Descripción: Coeficientes de los polinomios a0 + a1*X y b0 + b1*X.

            gamma:
             Tipo: np.int64
             Longitud: 1
             Descripción: El valor de gamma, usado en el módulo cuadrático (X^2 - gamma).

        Output:
            c0, c1:
             Tipo: np.int64
             Longitud: 1 (cada uno)
             Descripción: Coeficientes del polinomio resultado.
    """
    @staticmethod
    def _BaseCaseMultiply(a0, a1, b0, b1, gamma):
        c0 = (a0 * b0 + a1 * b1 * gamma) % ML_KEM.q
        c1 = (a0 * b1 + a1 * b0) % ML_KEM.q

        return c0, c1
    
    
    """
        Calcula el producto (en el anillo T_q) de dos representaciones NTT.
        
        Input:
            f_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, representando la NTT de un polinomio.
            
            g_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, representando la NTT de un polinomio.

        Output:
            h_hat:
             Tipo: numpy array, dtype = np.int64
             Longitud: 256
             Descripción: Array de 256 coeficientes en Z_q, representando la NTT del producto de f_hat y g_hat.
    """
    @staticmethod
    def _MultiplyNTTs(f_hat, g_hat):
        # Creamos el array en el que se va a almacenar la multiplicación
        h_hat = np.zeros(256, dtype=np.int64)

        # Para cada 2 posiciones, extraemos los valores de ambos arrays, así como el valor gamma
        # Tras esto, obtenemos los valores de la multiplicación gracias a la función BaseCaseMultiply
        for i in range(128):
            f0, f1 = f_hat[2*i], f_hat[2*i + 1]
            g0, g1 = g_hat[2*i], g_hat[2*i + 1]
            gamma = ML_KEM._ArrayBitRev_Multiply[i]
            h0, h1 = ML_KEM._BaseCaseMultiply(f0, f1, g0, g1, gamma)
            h_hat[2*i], h_hat[2*i + 1] = h0, h1

        return h_hat


    """
        Genera una clave de cifrado pública y una clave de cifrado privada para un esquema PKE.

        Input:
            d:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Un valor de entrada que se utiliza como semilla inicial para la generación de claves.

        Output:
            ekPKE:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k + 32
             Descripción: La clave de cifrado pública del esquema PKE.
            
            dkPKE:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k
             Descripción: La clave de cifrado privada del esquema PKE.
    """
    @staticmethod
    def _K_PKE_KeyGen(d):
        # Transformamos la variable global k a un array de bytes para poder concatenarlo con la semilla d
        k_byte = np.array([ML_KEM.k], dtype=np.uint8)
        array_dk = np.concatenate((d, k_byte))

        # Mediante la función _G obtenemos 2 arrays de 32 bytes
        rho, sigma = ML_KEM._G(array_dk)

        # Creamos una matriz A_hat de dimensión k*k a partir de la semilla rho
        # Los valores de A_hat son el resultado del sample NTT a la semilla + 2 bytes de índices
        N = 0
        A_hat = np.zeros((ML_KEM.k, ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            i_byte = np.array([i], dtype=np.uint8)
            for j in range (ML_KEM.k):
                j_byte = np.array([j], dtype=np.uint8)
                combined_bytes = np.concatenate((rho, i_byte, j_byte))
                A_hat[i, j] = ML_KEM._SampleNTT(combined_bytes)

        # Creamos el vector de coeficientes que contendrá las variables secretas
        s = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            N_byte = np.array([N], dtype=np.uint8)
            s[i] = ML_KEM._SamplePolyCBD(ML_KEM._PRF(ML_KEM.eta_1, sigma, N_byte), ML_KEM.eta_1)
            N += 1

        # Creamos el vector de coeficientes que se utilizará como ruido
        e = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            N_byte = np.array([N], dtype=np.uint8)
            e[i] = ML_KEM._SamplePolyCBD(ML_KEM._PRF(ML_KEM.eta_1, sigma, N_byte), ML_KEM.eta_1)
            N += 1
        
        # Pasamos ambos vectores a la representación NTT
        s_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        e_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            s_hat[i] = ML_KEM._NTT(s[i])
            e_hat[i] = ML_KEM._NTT(e[i])

        # Creamos t_hat (A_hat*s_hat + e_hat) que será el vector utilizado para crear ekPKE
        t_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            for j in range(ML_KEM.k):
                t_hat[i] = (t_hat[i] + ML_KEM._MultiplyNTTs(A_hat[i, j], s_hat[j])) % ML_KEM.q

        for i in range(ML_KEM.k):
            t_hat[i] = (t_hat[i] + e_hat[i]) % ML_KEM.q

        # ekPKE es el vector t_hat aplicándole una codificación apropiada
        ekPKE = np.zeros(384*ML_KEM.k, dtype=np.uint8)
        for i in range(ML_KEM.k):
            t_encoded = ML_KEM._ByteEncode(t_hat[i], 12)
            for j in range(384):
                ekPKE[384*i+j] = t_encoded[j]
        
        # Además a ekPKE se le concatena la semilla rho utilizada para crear A_hat
        ekPKE = np.concatenate((ekPKE, rho))

        # La clave de descifrado es el vector de claves secretas s_hat con una codificación apropiada
        dkPKE = np.zeros(384*ML_KEM.k, dtype=np.uint8)
        for i in range(ML_KEM.k):
            s_encoded = ML_KEM._ByteEncode(s_hat[i], 12)
            for j in range(384):
                dkPKE[384*i+j] = s_encoded[j]
        
        return ekPKE, dkPKE


    """
        Este algoritmo utiliza la clave de cifrado pública del esquema PKE para cifrar un mensaje con una
        entrada de 32 bytes aleatorios, produciendo un texto cifrado.

        Input:
            ekPKE:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k + 32
             Descripción: La clave pública del esquema PKE.

            m:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: El mensaje que se desea cifrar.

            r:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Un array de 32 bytes aleatorios.

        Output:
            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*(d_u*k + d_v)
             Descripción: El texto cifrado resultante de la operación de cifrado.
    """
    @staticmethod
    def _K_PKE_Encrypt(ekPKE, m, r):

        # Inicializamos t_hat para su posterior recuperación a partir de la clave de cifrado ekPKE
        N = 0
        t_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            t_hat[i] = ML_KEM._ByteDecode(ekPKE[384*i:384*i+384], 12)
        
        # Extraemos la semilla de ekPKE y recreamos la matriz A_hat con ella
        rho = ekPKE[384*ML_KEM.k:384*ML_KEM.k + 32]
        A_hat = np.zeros((ML_KEM.k, ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            i_byte = np.array([i], dtype=np.uint8)
            for j in range (ML_KEM.k):
                j_byte = np.array([j], dtype=np.uint8)
                combined_bytes = np.concatenate((rho, i_byte, j_byte))
                A_hat[i, j] = ML_KEM._SampleNTT(combined_bytes)

        # Creamos un vector de ruido y
        y = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            N_byte = np.array([N], dtype=np.uint8)
            y[i] = ML_KEM._SamplePolyCBD(ML_KEM._PRF(ML_KEM.eta_1, r, N_byte), ML_KEM.eta_1)
            N += 1
        
        # Creamos un vector de ruido e1
        e1 = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            N_byte = np.array([N], dtype=np.uint8)
            e1[i] = ML_KEM._SamplePolyCBD(ML_KEM._PRF(ML_KEM.eta_2, r, N_byte), ML_KEM.eta_2)
            N += 1

        # Creamos un valor (256 coeficientes) de ruido
        N_byte = np.array([N], dtype=np.uint8)
        e2 = ML_KEM._SamplePolyCBD(ML_KEM._PRF(ML_KEM.eta_2, r, N_byte), ML_KEM.eta_2)
        
        # Convertirmos el vector y a su representación NTT
        y_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            y_hat[i] = ML_KEM._NTT(y[i])

        # Callculamos u_hat como (A_hat^T*y_hat)
        u_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            for j in range(ML_KEM.k):
                u_hat[i] = (u_hat[i] + ML_KEM._MultiplyNTTs(A_hat[j, i], y_hat[j])) % ML_KEM.q

        # Pasamos u_hat al anillo R_q
        u = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            u[i] = ML_KEM._InverseNTT(u_hat[i])
        
        # Le añadimos el ruido e1 a u
        for i in range(ML_KEM.k):
            u[i] = (u[i] + e1[i]) % ML_KEM.q

        # Decodificamos m (de bytes a 256 enteros)
        m_decoded = ML_KEM._ByteDecode(m, 1)
        
        # Y descomprimimos el valor de m_decoded
        mu = np.zeros(ML_KEM.n, dtype=np.int64)
        for i in range(ML_KEM.n):
            mu[i] = ML_KEM._Decompress(m_decoded[i], 1)

        # Calculamos la multiplicación entre (t_hat^T y y_hat)
        resultado_multiplicacion = np.zeros(ML_KEM.n, dtype=np.int64)
        for i in range(ML_KEM.k):
            resultado_multiplicacion = (resultado_multiplicacion + ML_KEM._MultiplyNTTs(t_hat[i], y_hat[i])) % ML_KEM.q
        
        # Pasamos el resultado de la multiplicación al anillo R_q
        mult_invertida = ML_KEM._InverseNTT(resultado_multiplicacion)

        # Creamos v como resultado de la inversa de la multiplicación + ruido e2 + mu
        v = np.zeros(ML_KEM.n, dtype=np.int64)
        v = (v + mult_invertida + e2 + mu) % ML_KEM.q
        
        # Una vez tenemos u y v, comprimimos cada uno de sus valores y los codificamos
        # Comprimimos y codificamos u
        u_compressed = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            for j in range(ML_KEM.n):
                u_compressed[i, j] = ML_KEM._Compress(u[i, j], ML_KEM.d_u)
        c1 = np.zeros(32*ML_KEM.d_u*ML_KEM.k, dtype=np.uint8)

        for i in range(ML_KEM.k):
            u_encoded = ML_KEM._ByteEncode(u_compressed[i], ML_KEM.d_u)
            for j in range(32*ML_KEM.d_u):
                c1[32*ML_KEM.d_u*i+j] = u_encoded[j]
        
        # Comprimimos y codificamos v
        v_compressed = np.zeros(ML_KEM.n, dtype=np.int64)
        for i in range(ML_KEM.n):
            v_compressed[i] = ML_KEM._Compress(v[i], ML_KEM.d_v)
        c2 = ML_KEM._ByteEncode(v_compressed, ML_KEM.d_v)

        # Concatenamos u y v para dar así como resultado el texto cifrado
        c = np.concatenate((c1, c2))
        
        return c


    """
        Este algoritmo utiliza la clave de cifrado privada del esquema PKE para descifrar un
        texto cifrado, recuperando el mensaje original.

        Input:
            dkPKE:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k
             Descripción: La clave privada del esquema criptográfico.

            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*(d_u*k + d_v)
             Descripción: El texto cifrado que se desea descifrar.

        Output:
            m:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: El mensaje descifrado.
    """
    @staticmethod
    def _K_PKE_Decrypt(dkPKE, c):

        # Extraemos c1 y c2 creados del texto cifrado
        c1 = c[0:32*ML_KEM.d_u*ML_KEM.k]
        c2 = c[32*ML_KEM.d_u*ML_KEM.k:32*(ML_KEM.d_u*ML_KEM.k + ML_KEM.d_v)]

        # Obtenemos u_prima realizandole las apropiadas decodificaciones y compresiones a c1
        u_prima = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            u_prima[i] = ML_KEM._ByteDecode(c1[32*ML_KEM.d_u*i:32*ML_KEM.d_u*i+32*ML_KEM.d_u], ML_KEM.d_u)
        
        for i in range(ML_KEM.k):
            for j in range(ML_KEM.n):
                u_prima[i, j] = ML_KEM._Decompress(u_prima[i, j], ML_KEM.d_u)

        # Obtenemos v_prima realizandole las apropiadas decodificaciones y compresiones a c2
        v_prima = np.zeros(ML_KEM.n, dtype=np.int64)
        v_decoded = ML_KEM._ByteDecode(c2, ML_KEM.d_v)
        for i in range(ML_KEM.n):
            v_prima[i] = ML_KEM._Decompress(v_decoded[i], ML_KEM.d_v)
        
        # Recosntruimos el vector de claves secretas apartir de decodificar la dkPKE
        s_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            s_hat[i] = ML_KEM._ByteDecode(dkPKE[384*i:384*i+384], 12)
        
        # Queremos conseguir v-inicial, que es la inversa de s_hat^T * NTT(u_prima)
        u_hat = np.zeros((ML_KEM.k, ML_KEM.n), dtype=np.int64)
        for i in range(ML_KEM.k):
            u_hat[i] = ML_KEM._NTT(u_prima[i])

        resultado_multiplicacion = np.zeros(ML_KEM.n, dtype=np.int64)
        for i in range(ML_KEM.k):
            resultado_multiplicacion = (resultado_multiplicacion + ML_KEM._MultiplyNTTs(s_hat[i], u_hat[i])) % ML_KEM.q
        
        v_inicial = ML_KEM._InverseNTT(resultado_multiplicacion)

        # Calculamos w que es v_prima - v_inicial
        w = (v_prima - v_inicial) % ML_KEM.q

        # Comprimimos y codificamos este mensaje para recuperar el mensaje inicial
        m = np.zeros(32, dtype=np.uint8)
        w_compressed = np.zeros(ML_KEM.n, dtype=np.int64)

        for i in range(ML_KEM.n):
            w_compressed[i] = ML_KEM._Compress(w[i], 1)

        m = ML_KEM._ByteEncode(w_compressed, 1)

        return m


    """
        Genera una clave de encapsulación y una clave de descapsulación a partir dos semillas aleatorias.

        Input:
            d:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Una semilla aleatoria.

            z:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Una semilla aleatoria.

        Output:
            encaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: La clave de encapsulación.

            decaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96 bytes
             Descripción: La clave de descapsulación generada (dkPKE + ekPKE + H(ekPKE) + z).
    """
    @staticmethod
    def _ML_KEM_KeyGenInternal(d, z):
        
        # Se crean las claves de cifrado y descifrado PKE a partir de d
        ekPKE, dkPKE = ML_KEM._K_PKE_KeyGen(d)

        # La clave de encapsulamiento es directamente la clave de cifrado
        encaps_k = ekPKE

        # La clave de desencapsulamiento se calcula de la siguiente manera
        decaps_k = np.concatenate((dkPKE, encaps_k, ML_KEM._H(encaps_k), z))

        return encaps_k, decaps_k


    """
        Utiliza la clave de encapsulación y un mensaje m generado aelatoriamente para obtener la clave secreta
        K y un valor de aletoriedad r. Después, con encaps_k, m y r, genera un texto cifrado.

        Input:
            encaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: La clave de encapsulación del esquema criptográfico.

            m:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Un valor aleatorio de 32 bytes que se utiliza como entrada.

        Output:
            K:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: La clave compartida generada.

            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*(d_u*k+d_v)
             Descripción: El texto cifrado resultante de la operación de encapsulación.
    """
    @staticmethod
    def _ML_KEM_EncapsInternal(encaps_k, m):
        # Obtener la clave secreta K y un valor de aletoriedad r
        K, r = ML_KEM._G(np.concatenate((m, ML_KEM._H(encaps_k))))

        # Crear un texto cifrado c
        c = ML_KEM._K_PKE_Encrypt(encaps_k, m, r)

        return K, c


    """
        Utiliza la clave de desencapsulamiento y un texto cifrado para producir una clave secreta K,
        que después verificamos si es la correcta o no gracias al propio texto cifrado pasado como argumento.

        Input:
            decaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96 bytes
             Descripción: La clave de descapsulación del esquema criptográfico.
            
            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32(d_u*k+d_v)
             Descripción: El texto cifrado que se desea descapsular.

        Output:
            K':
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: La clave compartida resultante de la operación de descapsulación.
    """
    @staticmethod
    def _ML_KEM_DecapsInternal(decaps_k, c):
        # Extraemos los 4 arrays que conforman la clave de desencapsulamiento
        dkPKE = decaps_k[0:384*ML_KEM.k]
        ekPKE = decaps_k[384*ML_KEM.k:768*ML_KEM.k+64]
        h = decaps_k[768*ML_KEM.k+32:768*ML_KEM.k+64]
        z = decaps_k[768*ML_KEM.k+64:768*ML_KEM.k+96]

        # Desciframos el mensaje 
        m_prima = ML_KEM._K_PKE_Decrypt(dkPKE, c)

        # Generamos K de la misma forma que en el proceso de encapsulamiento
        K_prima, r_prima = ML_KEM._G(np.concatenate((m_prima, h)))

        # Generamos una K_falsa por si los mensajes cifrados no coinciden
        K_falsa = ML_KEM._J(np.concatenate((z, c)))

        # Generamos un texto cifrado de la misma forma que el pasado por argumento
        c_prima = ML_KEM._K_PKE_Encrypt(ekPKE, m_prima, r_prima)

        # Comparamos los dos textos cifrados, en caso de no ser iguales, la K devuelta será la K falsa
        if not np.array_equal(c, c_prima):
            K_prima = K_falsa

        return K_prima


    """
        Comprueba si una clave de encapsulación cumple una serie de requisitos para poder ser utilziada.

        Input:
            encaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: Una clave de encapsulación del esquema ML-KEM..

        Output:
             True: Si pasa todas las comprobaciones.
             False: Si no pasa alguna comprobación.
    """
    @staticmethod
    def _comprobarEkValida(encaps_k):
        # Verificar la longitud y el tipo de la clave de encapsulación
        expected_length = 384*ML_KEM.k + 32
        if (len(encaps_k) != expected_length) or (encaps_k.dtype != np.uint8):
            print(f"\nError: Fallo en la longitud o el tipo de Ek.")
            return False

        # Comprueba que los arrays Codificados(Decodificados), tienen el mismo valor que antes de hacerlo
        for i in range(ML_KEM.k):
            test = ML_KEM._ByteEncode(ML_KEM._ByteDecode(encaps_k[384*i:384*i+384], 12), 12)
            if not np.array_equal(test, encaps_k[384*i:384*i+384]):
                print("\nError: Los valores codificados no coinciden con los originales.")
                return False
        
        return True


    """
        Comprueba si una clave de desencapsulación cumple una serie de requisitos para poder ser utilziada.

        Input:
            decaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96
             Descripción: Una clave de descapsulación del esquema ML-KEM.

        Output:
             True: Si pasa todas las comprobaciones.
             False: Si no pasa alguna comprobación.
    """
    @staticmethod
    def _comprobarDkValida(decaps_k):
        # Verificar la longitud y el tipo de clave de descapsulación
        expected_length = 768*ML_KEM.k + 96    
        if (len(decaps_k) != expected_length) or (decaps_k.dtype != np.uint8):
            print("\nError: Fallo en la longitud o el tipo de Dk.")
            return False
        
        # Verifica si aplicarle el hash a las posiciones extraídas es el mismo que ya se tiene en dk
        test = ML_KEM._H(decaps_k[384*ML_KEM.k:768*ML_KEM.k+32])
        if not np.array_equal(test, decaps_k[768*ML_KEM.k+32:768*ML_KEM.k+64]):
            print("\nError: Fallo en la verfificación del hash de la clave Dk")
            return False
        
        return True


    """
        Verifica si un determinado texto cifrado tiene el formato válido para ser utilizado.
        
        Input:
            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*(d_u*k + d_v)
             Descripción: Una texto cifrado esquema ML-KEM.

        Output:
             True: Si pasa todas las comprobaciones.
             False: Si no pasa alguna comprobación.
    """
    @staticmethod
    def _verificarC(c):
        # Verificar la longitud y el tipo del texto cifrado
        expected_length = 32*(ML_KEM.d_u*ML_KEM.k + ML_KEM.d_v)
        if (len(c) != expected_length) or (c.dtype != np.uint8):
            print("\nError: Longitud o tipo del texto cifrado inválido.")
            return False
        
        return True

    """
        Establece como clave de encapsulamiento una clave introducida por parámetro.

        Input:
            encaps_k:
             Tipo: numpy array, uint8
             Longitud: 384*k+32
             Descripción: Clave de encapsulamiento introducida por parámetro.

        Output:
             True: Si pasa todas las comprobaciones.
             False: Si no pasa alguna comprobación.
    """
    @staticmethod
    def _establecerEk(encaps_k):
        if(ML_KEM._comprobarEkValida(encaps_k)):
            ML_KEM.encaps_k = encaps_k
            print("\nNueva clave de encapsulamiento establecida.")
            return True
        
        return False


    """
        Establece como clave de desencapsulamiento una clave introducida por parámetro.

        Input:
            decaps_k:
             Tipo: numpy array, uint8
             Longitud: 768*k+96
             Descripción: Clave de desencapsulamiento introducida por parámetro.

        Output:
             True: Si pasa todas las comprobaciones.
             False: Si no pasa alguna comprobación.
    """
    @staticmethod
    def _establecerDk(decaps_k):
        if(ML_KEM._comprobarDkValida(decaps_k)):
            ML_KEM.decaps_k = decaps_k
            print("\nNueva clave de desencapsulamiento establecida.")
            return True
        
        return False


    """
        Comprueba si dos claves secretas k1 y k2 son idénticas.

        Input:
            k1:
             Tipo: numpy array, uint8
             Longitud: 32
             Descripción: Clave de secreta 1.

            k2:
             Tipo: numpy array, uint8
             Longitud: 32
             Descripción: Clave de secreta 2.

        Output:
             True: Si las dos claves secretas son iguales.
             False: Si las dos claves secretas no son iguales.
    """
    @staticmethod
    def _compararClavesSecretas(k1, k2):
        if np.array_equal(k1, k2):
            return True
        
        return False
    
    ############################ MÉTODOS PÚBLICOS ############################

    """
        Varía entre los distintos conjuntos de parámetros aceptados en función del argumento de entrada.

        Input:
            x:
             Tipo: entero
             Longitud: 1
             Descripción: Valor que define el conjunto de parámetros a utilziar.

        Output:
             Se actualizan las variables globales en base al parámetro introducido.
    """
    @staticmethod
    def establecer_parametros(x):
        # ML-KEM-512
        if x == 1:
            ML_KEM.k = 2
            ML_KEM.eta_1 = 3
            ML_KEM.eta_2 = 2
            ML_KEM.d_u = 10
            ML_KEM.d_v = 4
        # ML-KEM-768
        elif x == 2:
            ML_KEM.k = 3
            ML_KEM.eta_1 = 2
            ML_KEM.eta_2 = 2
            ML_KEM.d_u = 10
            ML_KEM.d_v = 4
        # ML-KEM-1024
        elif x == 3:
            ML_KEM.k = 4
            ML_KEM.eta_1 = 2
            ML_KEM.eta_2 = 2
            ML_KEM.d_u = 11
            ML_KEM.d_v = 5
        else:
            raise ValueError("Valor introducido inválido, debe de ser 1, 2 o 3.")

        ML_KEM.encaps_k = np.zeros(384*ML_KEM.k+32, dtype=np.uint8)
        ML_KEM.decaps_k = np.zeros(768*ML_KEM.k+96, dtype=np.uint8)
        

    """
        Genera una clave de encapsulación y una correspondiente clave de descapsulación utilizando 
        dos semillas aleatorias generadas internamente.

        Input:
            Ninguno.

        Output:
            encaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: La clave de encapsulación generada por el algoritmo.
            
            decaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96
             Descripción: La clave de descapsulación generada por el algoritmo.
    """
    @staticmethod
    def ML_KEM_KeyGen():
        # Genera aleatoriamente d y z, cada uno de 32 bytes
        d = np.random.randint(0, 256, size=32, dtype=np.uint8)
        z = np.random.randint(0, 256, size=32, dtype=np.uint8)

        # Si d o z se ha generado mal, mostrar error
        if d is None or z is None:
            raise ValueError("\nFallo al generar d o z")

        # Llamar al método interno de generación de claves para generar encaps_k y decaps_k 
        encaps_k, decaps_k = ML_KEM._ML_KEM_KeyGenInternal(d, z)

        return encaps_k, decaps_k


    """
        Utiliza la clave de encapsulación para generar una clave secreta compartida y un texto cifrado asociado.

        Input:
            encaps_k:
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: La clave de encapsulación.

        Output:
            K:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: La clave secreta compartida generada.

            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32*(d_u*k+d_v)
             Descripción: El texto cifrado resultante de la operación de encapsulación.
    """
    @staticmethod
    def ML_KEM_Encaps(encaps_k):
        # Genera un mesnaje aleatorio de 32 bytes
        m = np.random.randint(0, 256, size=32, dtype=np.uint8)

        # Si m se ha generado mal, mostrar error
        if m is None:
            raise ValueError("\nFallo al generar m")

        # Llamar al método interno de encapsulamiento para generar la clave secreta K y el texto cifrado c
        K, c = ML_KEM._ML_KEM_EncapsInternal(encaps_k, m)
        
        return K, c
        
        
    """
        Utiliza la clave de descapsulación para producir una clave compartida a partir de un texto cifrado.
        
        Input:
            dk:
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96
             Descripción: La clave de descapsulación del esquema criptográfico.

            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32(d_u*k+d_v)
             Descripción: El texto cifrado que se desea descapsular.

        Output:
            K_prime:
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: La clave compartida resultante de la operación de descapsulación.
    """
    @staticmethod
    def ML_KEM_Decaps(decaps_k, c):
        if(ML_KEM._verificarC(c)):
            
            # Llamar al método interno de desencapsulamiento para generar la clave secreta K a partir del texto cifrado c
            K_prima = ML_KEM._ML_KEM_DecapsInternal(decaps_k, c)

            return K_prima
        else:
            raise ValueError("\nEl texto cifrado 'c' no es válido.")
        
    """
        Interfaz diseñada para utilizar de manera intuitiva la clase ML-KEM.
        Dispone de 7 acciones:
         1: Modificar el conjunto de parámetros a utilizar.
         2: Generar el conjunto de claves aleatoriamente.
         3: Asignar la clave encaps_k introducida como argumento.
         4: Asignar la clave decaps_k introducida como argumento.
         5: Realizar el proceso de encapsulamiento de un mensaje.
         6: Realizar el proceso de desencapsulamiento de un mensaje cifrado.
        7: Comparar claves secretas compartidas.

        Input:
            encaps_k (opcional):
             Tipo: numpy array, dtype = uint8
             Longitud: 384*k+32
             Descripción: Una clave de encapsulación del esquema criptográfico ML-KEM.
            
            decaps_k (opcional):
             Tipo: numpy array, dtype = uint8
             Longitud: 768*k+96
             Descripción: Una clave de descapsulación del esquema criptográfico ML-KEM.

            K (opcional):
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Una clave secreta compartida.
            
            K_prima (opcional):
             Tipo: numpy array, dtype = uint8
             Longitud: 32
             Descripción: Otra clave secreta compartida. 
            
            c:
             Tipo: numpy array, dtype = uint8
             Longitud: 32(d_u*k+d_v)
             Descripción: Un texto cifrado para desencapsular.

        Output:
            Ninguno.
    """
    @staticmethod
    def ML_KEM_Interfaz(encaps_k=None, decaps_k=None, K=None, K_prima=None, c=None):

        print("\nBienvenido a la interfaz de usuario del modelo KEM: ML-KEM.")
        print("\nEsta interfaz ha sido desarrollada por Denis Valentin Stoyanov D'Antonio")
        parameter_set = "ML-KEM-768"
        ML_KEM.establecer_parametros(2)
        print(f"\nEl conjunto de parámetros establecido por defecto es: {parameter_set}.")

        bloqueo = 0
        seleccion = -1
        while(seleccion != 0):
            
            print("\n----------------------------------------------------------------")
            print(f"\nEl conjunto de parámetros actual es: {parameter_set}.")   
            print("\n¿Tienen algo almacenado los siguientes valores?: ")
            print(f"\n Clave encapsulamiento (encaps_k): '{encaps_k is not None}', Clave desencapsulamiento (decaps_k): '{decaps_k is not None}'")
            print(f"\n Clave secreta de encaps (K): '{K is not None}', Clave secreta de decaps (K'): '{K_prima is not None}', Texto cifrado (c): '{c is not None}'")

            print("\n\n¿Qué quieres hacer?: ")
            print(" 1: Modificar el conjunto de parámetros a utilizar (se deberán volver a generar o asignar las claves encaps_k y decaps_k).")
            print(" 2: Generar el conjunto de claves aleatoriamente.")
            print(" 3: Asignar la clave encaps_k introducida como argumento.")
            print(" 4: Asignar la clave decaps_k introducida como argumento.")
            print(" 5: Realizar el proceso de encapsulamiento de un mensaje.")
            print(" 6: Realizar el proceso de desencapsulamiento de un mensaje cifrado.")
            print(" 7: Comparar claves secretas compartidas.")
            print("\n 0: Cerrar la interfaz.")

            x = int(input("\n -> Introduce el número correspondiente a la acción a realizar: "))
            if(0 <= x <= 7):
                seleccion = x
            else:
                print("\nEl número introducido no tiene un valor correcto.")

            # Modificar parámeter set
            if(seleccion == 1):
                print("\n----------------------------------------------------------------")
                print("\n¿A qué conjunto de parámetros quieres pasar?: ")
                print(" 1: ML-KEM-512 (mayor rendimiento)")
                print(" 2: ML-KEM-768 (equilibrado)")
                print(" 3: ML-KEM-1024 (mayor seguridad)")
                print("\n 0: Volver al menú principal.")

                # Asegurar que el valor introducido es correcto
                x = int(input("\n -> Introduce el número correspondiente al conjunto de parámetros a utilizar: "))
                while (x != 0 and x != 1 and x != 2 and x != 3):
                    print("\nEl número introducido no tiene un valor correcto.")
                    x = int(input("\n -> Introduce el número correspondiente al conjunto de parámetros a utilizar: "))

                # Modificar el conjunto de parámetros o volver al menú principal
                if(x == 1):
                    if(parameter_set == "ML-KEM-512"):
                        print("\nYa tienes establecido el conjunto de parámetros ML-KEM-512")
                    else:
                        ML_KEM.establecer_parametros(x)
                        print("\nConjunto de parámetros cambiado a: ML-KEM-512.")
                        parameter_set = "ML-KEM-512"
                        bloqueo = 2
                        seleccion = -1
                elif(x == 2):
                    if(parameter_set == "ML-KEM-768"):
                        print("\nYa tienes establecido el conjunto de parámetros ML-KEM-768")
                    else:
                        ML_KEM.establecer_parametros(x)
                        print("\nConjunto de parámetros cambiado a: ML-KEM-768.")
                        parameter_set = "ML-KEM-768"
                        bloqueo = 2
                        seleccion = -1
                elif(x == 3):
                    if(parameter_set == "ML-KEM-1024"):
                        print("\nYa tienes establecido el conjunto de parámetros ML-KEM-1024")
                    else:
                        ML_KEM.establecer_parametros(x)
                        print("\nConjunto de parámetros cambiado a: ML-KEM-1024.")
                        parameter_set = "ML-KEM-1024"
                        bloqueo = 2
                        seleccion = -1
                else:
                    seleccion = -1

            # Generar claves aleatorias
            if(seleccion == 2):
                print("\n----------------------------------------------------------------")
                while(seleccion == 2): # Para cuando de error el squeeze
                    encaps_k, decaps_k = ML_KEM.ML_KEM_KeyGen()
                    if(ML_KEM._establecerEk(encaps_k) and ML_KEM._establecerDk(decaps_k)):
                        print("\nClaves pública y privada creadas y establecidas con éxito.")
                        bloqueo = 0
                        seleccion = -1
            
            # Usar la encaps_k introducida por argumento
            if(seleccion == 3):
                print("\n----------------------------------------------------------------")
                if(ML_KEM._establecerEk(encaps_k)):
                    print("\nLa clave pública introducida como argumento hansido establecida con éxito.")
                    if((bloqueo-1)>=0):
                        bloqueo = bloqueo - 1
                else:
                    print("\nLa clave de encapsulamiento introducida como argumento no es válida.")
                    print("\nAbre la interfaz con unos argumentos válidos, o, si crees que lo son, cambia al parameter set adecuado para los mismos.")

                seleccion = -1

            # Usar la decaps_k introducida por argumento
            if(seleccion == 4):
                print("\n----------------------------------------------------------------")
                if(ML_KEM._establecerDk(decaps_k)):
                    print("\nLa clave privada introducida como argumento hansido establecida con éxito.")
                    if((bloqueo-1)>=0):
                        bloqueo = bloqueo - 1
                else:
                    print("\nLa clave de desencapsulamiento introducida como argumento no es válida.")
                    print("\nAbre la interfaz con unos argumentos válidos, o, si crees que lo son, cambia al parameter set adecuado para los mismos.")
                
                seleccion = -1

            # Proceso de encapsulamiento
            if(seleccion == 5):
                print("\n----------------------------------------------------------------")
                if(bloqueo == 0):
                    if(encaps_k is not None):
                        K, c = ML_KEM.ML_KEM_Encaps(encaps_k)
                        print("\nEncapsulamiento realizado con éxito.")
                        print("\nSe han generado la clave secreta K y el texto cifrado c.")
                    else:
                        print("\nError: No hay ninguna clave de encapsulamiento para usar actualmente.")
                else:
                    print("\nDespués de modificar los parámetros, tienes que volver a crear o asignar las claves encaps_k y decaps_k")
                seleccion = -1

            # Proceso de desencapsulamiento
            if(seleccion == 6):
                print("\n----------------------------------------------------------------")
                if(bloqueo == 0):
                    if(decaps_k is not None and c is not None):
                            K_prima = ML_KEM.ML_KEM_Decaps(decaps_k, c)
                            print("\nDesencapsulamiento realizado con éxito.")
                            print("\nSe ha obtenido la clave secreta K_prima.")
                    else:
                        print("\nError: No hay ninguna clave de desencapsulamiento para usar actualmente.")
                else:
                    print("\nDespués de modificar los parámetros, tienes que volver a crear o asignar las claves encaps_k y decaps_k")
                seleccion = -1

            # Comparar las claves K y K_prima
            if(seleccion == 7):
                print("\n----------------------------------------------------------------")
                if(K is not None and K_prima is not None):
                    if ML_KEM._compararClavesSecretas(K, K_prima):
                            print("\nSe han comparado las claves secretas generadas durante el encapsulamiento y el desencapsulamiento y son iguales.")
                            print("\nPor lo tanto, el modelo ML-KEM funciona correctamente con este conjunto de claves y parámetros.")
                    else:
                        print("\nError: Las claves secretas K y K_prima no coinciden.")
                        print(f"Clave K generada en el proceso de encapsulamiento: {K}")
                        print(f"Clave K' generada en el proceso de desencapsulamiento:: {K_prima}")
                elif(K is None):
                    print("\nLa clave K generada en el proceso de encapsulamiento no tiene valor.")
                else:
                    print("\nLa clave K' generada en el proceso de desencapsulamiento no tiene valor.")
                
                seleccion = -1

        print("\n----------------------------------------------------------------")
        print("\nGracias por utilizar la interfaz de ML_KEM, hasta pronto.")
        print("\n----------------------------------------------------------------")
