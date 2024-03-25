import heapq  # Importar heapq para utilizar colas de prioridad
import networkx as nx  # Importar networkx para crear y manipular grafos
import matplotlib.pyplot as plt  # Importar matplotlib para visualizar grafos

class Grafo:
    def __init__(self):
        self.vertices = {}  # Inicializar un diccionario para almacenar los vértices y sus adyacencias

    def agregar_vertice(self, vertice):
        if vertice not in self.vertices:
            self.vertices[vertice] = {}  # Agregar un nuevo vértice al grafo si no existe

    def agregar_arista(self, origen, destino, peso):
        if origen in self.vertices and destino in self.vertices:
            self.vertices[origen][destino] = peso  # Agregar una arista bidireccional entre origen y destino con un peso dado
            self.vertices[destino][origen] = peso

    def dijkstra(self, inicio, fin):
        distancia = {vertice: float('inf') for vertice in self.vertices}  # Inicializar las distancias a cada vértice como infinito
        distancia[inicio] = 0  # La distancia al inicio es 0
        cola = [(0, inicio, [])]  # Inicializar una cola de prioridad con la distancia acumulada, el vértice actual y el camino recorrido
        while cola:
            distancia_actual, vertice_actual, camino = heapq.heappop(cola)  # Obtener el vértice más cercano de la cola
            if distancia_actual > distancia[vertice_actual]:
                continue  # Si ya se encontró un camino más corto, ignorar este vértice
            camino = camino + [vertice_actual]  # Agregar el vértice actual al camino recorrido
            if vertice_actual == fin:
                return camino  # Si se llega al destino, devolver el camino recorrido
            for vecino, peso_arista in self.vertices[vertice_actual].items():
                distancia_total = distancia_actual + peso_arista  # Calcular la distancia total hasta el vecino
                if distancia_total < distancia[vecino]:
                    distancia[vecino] = distancia_total  # Actualizar la distancia al vecino
                    heapq.heappush(cola, (distancia_total, vecino, camino))  # Agregar el vecino a la cola con su distancia acumulada
        return []  # Si no se encontró un camino al destino, devolver una lista vacía

    def graficar_recorrido(self, recorrido):
        G = nx.DiGraph()  # Crear un grafo dirigido
        for vertice in self.vertices:
            G.add_node(vertice)  # Agregar cada vértice al grafo
        for i in range(len(recorrido) - 1):
            origen = recorrido[i]
            destino = recorrido[i + 1]
            G.add_edge(origen, destino, weight=self.vertices[origen][destino])  # Agregar aristas con pesos al grafo
        pos = nx.spring_layout(G)  # Calcular posiciones para los nodos
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=1500, edge_color='black', linewidths=1, font_size=12, arrows=True)  # Dibujar el grafo
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
        
        # Resaltar la ruta señalada por una línea de color rojo
        ruta_edges = [(recorrido[i], recorrido[i + 1]) for i in range(len(recorrido) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=ruta_edges, edge_color='red', width=2, arrows=True)

        plt.title('Recorrido')  # Establecer el título del gráfico
        plt.show()  # Mostrar el gráfico

# Crear una instancia de la clase Grafo
grafo = Grafo()

# Definir las estaciones y agregarlas como vértices al grafo
estaciones = ["portal norte", "calle 200", "toberín", "mazurén", "pepe sierra", "calle 161", "calle 146", "calle 142"]
for estacion in estaciones:
    grafo.agregar_vertice(estacion)

# Agregar las aristas que representan las conexiones entre las estaciones
grafo.agregar_arista("portal norte", "calle 200", 5)
grafo.agregar_arista("portal norte", "toberín", 7)
grafo.agregar_arista("calle 200", "toberín", 3)
grafo.agregar_arista("calle 200", "mazurén", 4)
grafo.agregar_arista("toberín", "mazurén", 2)
grafo.agregar_arista("toberín", "pepe sierra", 5)
grafo.agregar_arista("mazurén", "pepe sierra", 3)
grafo.agregar_arista("mazurén", "calle 161", 6)
grafo.agregar_arista("pepe sierra", "calle 161", 2)
grafo.agregar_arista("calle 161", "calle 146", 3)
grafo.agregar_arista("calle 146", "calle 142", 2)

# Imprimir las estaciones disponibles
print("Estaciones disponibles:")
for estacion in estaciones:
    print(estacion)

# Solicitar al usuario el punto de partida y el destino
inicio = input("Ingrese el punto de partida: ").strip().lower()
fin = input("Ingrese el destino: ").strip().lower()

# Encontrar la mejor ruta utilizando el algoritmo de Dijkstra
mejor_ruta = grafo.dijkstra(inicio, fin)

# Imprimir la mejor ruta y su tiempo estimado
print(f"El mejor tiempo para llegar de {inicio.capitalize()} a {fin.capitalize()} es: {len(mejor_ruta) - 1} minutos.")
print("Recorrido:")
print(" -> ".join(mejor_ruta))

# Graficar el recorrido encontrado
grafo.graficar_recorrido(mejor_ruta)
