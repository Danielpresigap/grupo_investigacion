import tkinter as tk 
from tkinter import messagebox
import random
import requests

# --- Daniel Alejandro Presiga, Grupo de Investigacion
class SopaDeLetrasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sopa de Letras Inteligente con Gemini")
        self.root.geometry("950x700")

        # --- Panel Izquierdo (Controles y Entradas) ---
        self.frame_izquierda = tk.Frame(root)
        self.frame_izquierda.pack(side=tk.LEFT, padx=15, pady=15, anchor=tk.N)

        tk.Label(self.frame_izquierda, text="API Key de Gemini:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.entrada_api = tk.Entry(self.frame_izquierda, width=25, show="*")
        self.entrada_api.pack(pady=5)

        tk.Label(self.frame_izquierda, text="Palabra inicial (Término central):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.entrada_palabra = tk.Entry(self.frame_izquierda, width=25)
        self.entrada_palabra.pack(pady=5)

        tk.Label(self.frame_izquierda, text="Número de palabras (Máx. 20):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.entrada_cantidad = tk.Entry(self.frame_izquierda, width=25)
        self.entrada_cantidad.pack(pady=5)
        self.entrada_cantidad.insert(0, "5")

        self.boton_generar = tk.Button(self.frame_izquierda, text="Generar Sopa de Letras", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.generar_sopa)
        self.boton_generar.pack(pady=15, fill=tk.X)

        self.boton_me_rindo = tk.Button(self.frame_izquierda, text="Me Rindo (Mostrar Solución)", bg="#f44336", fg="white", font=("Arial", 10, "bold"), command=self.mostrar_palabras)
        self.boton_me_rindo.pack(pady=5, fill=tk.X)

        tk.Label(self.frame_izquierda, text="Palabras a encontrar:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        
        self.palabras_frame = tk.Frame(self.frame_izquierda, bg="white", relief=tk.SUNKEN, bd=1)
        self.palabras_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- Panel Derecho (Cuadrícula de la Sopa de Letras) ---
        self.frame_derecha = tk.Frame(root)
        self.frame_derecha.pack(side=tk.RIGHT, padx=15, pady=15, expand=True)

        self.grid_frame = tk.Frame(self.frame_derecha)
        self.grid_frame.pack()

        # Variables de Estado del Juego
        self.sopa = []
        self.botones = []
        self.palabras = []
        self.seleccion_actual = []
        self.palabras_encontradas = set()

    def obtener_palabras_gemini(self, palabra_inicial, cantidad):
        """Conecta con la API probando múltiples modelos en secuencia para evitar errores 503 por alta demanda."""
        api_key = self.entrada_api.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Por favor ingresa tu API Key.")
            return []

        # Lista de modelos oficiales ordenados para alternar en caso de saturación
        modelos_a_probar = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-flash-latest"]
        
        prompt = (
            f"Genera exactamente {cantidad} palabras en español relacionadas estrictamente con el término '{palabra_inicial}'. "
            f"Incluye también la palabra '{palabra_inicial}' dentro de la lista si es apta. "
            f"Reglas estrictas: "
            f"1. Deben ser palabras simples de una sola palabra (sin espacios, sin guiones, sin caracteres especiales). "
            f"2. Devuelve ÚNICAMENTE las palabras separadas por comas (ejemplo: PALABRA1, PALABRA2, PALABRA3). "
            f"3. No incluyas numeración, ni explicaciones adicionales, ni introducciones."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": api_key
        }

        # Intenta con cada modelo disponible hasta que uno responda con éxito
        for modelo in modelos_a_probar:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
            try:
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    texto_respuesta = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    palabras_brutas = [p.strip().upper() for p in texto_respuesta.split(',')]
                    palabras_validas = [p for p in palabras_brutas if p.isalpha() and len(p) <= 15]
                    
                    resultado = list(set(palabras_validas))[:cantidad]
                    if resultado:
                        return resultado
            except Exception:
                continue # Pasa al siguiente modelo si ocurre un fallo de red o saturación

        messagebox.showerror("Error de API", "Los servidores de Gemini están ocupados en este momento (Error 503). Por favor, dale clic de nuevo en unos segundos.")
        return []

    def generar_sopa(self):
        """Controla el flujo de validación, obtención de IA y construcción del tablero."""
        palabra_inicial = self.entrada_palabra.get().strip()
        
        try:
            cantidad = int(self.entrada_cantidad.get().strip())
        except ValueError:
            messagebox.showerror("Error", "La cantidad de palabras debe ser un número entero.")
            return

        if not palabra_inicial:
            messagebox.showerror("Error", "Por favor ingresa una palabra inicial.")
            return

        if cantidad < 1 or cantidad > 20:
            messagebox.showerror("Error", "La cantidad de palabras debe estar entre 1 y 20.")
            return

        self.reiniciar_sopa()
        self.palabras = self.obtener_palabras_gemini(palabra_inicial, cantidad)

        if not self.palabras:
            return

        max_longitud = max(len(p) for p in self.palabras)
        tamano = max(max_longitud + 3, int((cantidad * 1.5) ** 0.5) + max_longitud, 8)
        tamano = min(tamano, 25)

        self.sopa = [['' for _ in range(tamano)] for _ in range(tamano)]
        
        for palabra in self.palabras:
            self.colocar_palabra_en_sopa(palabra, tamano)

        self.rellenar_espacios_vacios()
        self.mostrar_sopa(tamano)
        self.mostrar_lista_palabras()

    def colocar_palabra_en_sopa(self, palabra, tamano):
        """Intenta ubicar una palabra aleatoriamente en direcciones horizontal, vertical o diagonales."""
        direcciones = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        colocada = intents = 0

        while not colocada and intents < 100:
            fila = random.randint(0, tamano - 1)
            col = random.randint(0, tamano - 1)
            dir_fila, dir_col = random.choice(direcciones)

            if self.puede_colocar_palabra(fila, col, dir_fila, dir_col, palabra, tamano):
                for i, letra in enumerate(palabra):
                    self.sopa[fila + i * dir_fila][col + i * dir_col] = letra
                colocada = True
            intents += 1

    def puede_colocar_palabra(self, fila, col, dir_fila, dir_col, palabra, tamano):
        """Verifica si una palabra cabe en la posición y dirección seleccionada sin interferir."""
        for i, letra in enumerate(palabra):
            nueva_fila = fila + i * dir_fila
            nueva_col = col + i * dir_col

            if not (0 <= nueva_fila < tamano and 0 <= nueva_col < tamano):
                return False
            if self.sopa[nueva_fila][nueva_col] not in ('', letra):
                return False
        return True

    def rellenar_espacios_vacios(self):
        """Rellena las casillas vacías de la matriz con letras aleatorias del abecedario."""
        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for fila in range(len(self.sopa)):
            for col in range(len(self.sopa[fila])):
                if self.sopa[fila][col] == '':
                    self.sopa[fila][col] = random.choice(letras)

    def mostrar_sopa(self, tamano):
        """Genera los botones visuales que forman la cuadrícula interactiva."""
        self.botones = []
        for fila in range(tamano):
            fila_botones = []
            for col in range(tamano):
                boton = tk.Button(self.grid_frame, text=self.sopa[fila][col], width=3, height=1,
                                  font=("Arial", 10, "bold"),
                                  command=lambda f=fila, c=col: self.seleccionar_casilla(f, c))
                boton.grid(row=fila, column=col, padx=1, pady=1)
                fila_botones.append(boton)
            self.botones.append(fila_botones)

    def seleccionar_casilla(self, fila, col):
        """Maneja la selección interactiva de casillas por parte del usuario."""
        boton = self.botones[fila][col]
        if (fila, col) in self.seleccion_actual:
            boton.config(bg="SystemButtonFace")
            self.seleccion_actual.remove((fila, col))
        else:
            boton.config(bg="yellow")
            self.seleccion_actual.append((fila, col))

        self.verificar_palabra()

    def verificar_palabra(self):
        """Verifica si la selección actual del usuario corresponde a una palabra de la lista."""
        palabra_formada = ''.join([self.sopa[f][c] for f, c in self.seleccion_actual])
        
        if palabra_formada in self.palabras or palabra_formada[::-1] in self.palabras:
            palabra_encontrada = palabra_formada if palabra_formada in self.palabras else palabra_formada[::-1]
            
            for f, c in self.seleccion_actual:
                self.botones[f][c].config(bg="green")
            
            self.palabras_encontradas.add(palabra_encontrada)
            self.seleccion_actual = []
            self.actualizar_lista_palabras_visual()

            if len(self.palabras_encontradas) == len(self.palabras):
                messagebox.showinfo("¡Felicidades!", "¡Has encontrado todas las palabras!")

    def mostrar_palabras(self):
        """Revela la solución completa marcando las palabras en rojo."""
        for palabra in self.palabras:
            for fila in range(len(self.sopa)):
                for col in range(len(self.sopa[fila])):
                    for dir_fila, dir_col in [(0,1), (1,0), (1,1), (-1,1)]:
                        if self.puede_colocar_palabra_solucion(fila, col, dir_fila, dir_col, palabra):
                            for i in range(len(palabra)):
                                f = fila + i * dir_fila
                                c = col + i * dir_col
                                self.botones[f][c].config(bg="red")

    def puede_colocar_palabra_solucion(self, fila, col, dir_fila, dir_col, palabra):
        """Función auxiliar para comprobar ubicación exacta al mostrar solución."""
        for i, letra in enumerate(palabra):
            nueva_fila = fila + i * dir_fila
            nueva_col = col + i * dir_col
            if not (0 <= nueva_fila < len(self.sopa) and 0 <= nueva_col < len(self.sopa)):
                return False
            if self.sopa[nueva_fila][nueva_col] != letra:
                return False
        return True

    def mostrar_lista_palabras(self):
        """Muestra la lista inicial de palabras a buscar en el panel lateral."""
        for widget in self.palabras_frame.winfo_children():
            widget.destroy()
        
        for palabra in self.palabras:
            lbl = tk.Label(self.palabras_frame, text=f"• {palabra}", bg="white", font=("Arial", 10))
            lbl.pack(anchor=tk.W, padx=5, pady=2)

    def actualizar_lista_palabras_visual(self):
        """Cambia de color las palabras ya encontradas en la lista lateral."""
        for widget in self.palabras_frame.winfo_children():
            widget.destroy()
        
        for palabra in self.palabras:
            if palabra in self.palabras_encontradas:
                lbl = tk.Label(self.palabras_frame, text=f"✓ {palabra}", bg="white", fg="green", font=("Arial", 10, "bold"))
            else:
                lbl = tk.Label(self.palabras_frame, text=f"• {palabra}", bg="white", font=("Arial", 10))
            lbl.pack(anchor=tk.W, padx=5, pady=2)

    def reiniciar_sopa(self):
        """Limpia la cuadrícula anterior antes de generar una nueva."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.botones = []
        self.sopa = []
        self.seleccion_actual = []
        self.palabras_encontradas.clear()

if __name__ == "__main__":
    root = tk.Tk()
    app = SopaDeLetrasApp(root)
    root.mainloop()