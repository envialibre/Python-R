#pip install nltk
#Este ejercicio busca realizar un análisis básico de texto utilizando herramientas de procesamiento
# de lenguaje natural (NLP) proporcionadas por la biblioteca NLTK (Natural Language Toolkit) en Python

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.probability import FreqDist

# Descargar los recursos de NLTK (solo necesario una vez)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('gutenberg')
nltk.download('genesis')

# Texto de muestra para el análisis
texto_ejemplo = """El deporte es una parte integral de la sociedad humana, con una rica historia que se remonta a miles de años. Desde los Juegos Olímpicos de la antigua Grecia hasta los eventos deportivos contemporáneos que atraen a millones de espectadores de todo el mundo, el deporte ha desempeñado un papel fundamental en la cultura, la identidad nacional y la cohesión social.

En la actualidad, el mundo del deporte es más diverso y globalizado que nunca. Se practican una amplia variedad de deportes en todos los rincones del mundo, desde el fútbol y el baloncesto hasta el cricket, el rugby, el tenis y muchos más. Los atletas compiten a nivel local, nacional e internacional, representando a sus países de origen en campeonatos mundiales, torneos olímpicos y otros eventos deportivos de renombre.

Además de la competencia en el campo de juego, el deporte también abarca una amplia gama de industrias y actividades relacionadas. Desde la gestión y la organización de eventos deportivos hasta la comercialización y la transmisión de derechos de televisión, el deporte genera empleo, ingresos y oportunidades económicas en todo el mundo. Las marcas deportivas, los patrocinadores y los medios de comunicación desempeñan un papel crucial en la promoción y la difusión del deporte a nivel global.

En el ámbito de la tecnología y la innovación, el deporte también está experimentando cambios significativos. La implementación de tecnologías como el análisis de datos, la realidad virtual y la inteligencia artificial está transformando la forma en que se entrena, se compite y se disfruta del deporte. Los datos recopilados a partir de dispositivos portátiles y sensores están ayudando a los atletas y a los entrenadores a mejorar el rendimiento y a prevenir lesiones, mientras que las plataformas digitales y las redes sociales están acercando a los fanáticos al deporte como nunca antes.

En resumen, el mundo del deporte es un campo dinámico y en constante evolución que abarca una amplia gama de actividades, industrias y tecnologías. Desde el entretenimiento y la competencia hasta la innovación y el impacto social, el deporte sigue desempeñando un papel crucial en la vida de las personas en todo el mundo."""

# Tokenizar el texto en palabras
tokens = word_tokenize(texto_ejemplo)

# Eliminar las palabras de parada
stop_words = set(stopwords.words('spanish'))
tokens_filtrados = [word for word in tokens if word.lower() not in stop_words]

# Realizar la derivación de raíces
porter = PorterStemmer()
tokens_derivados = [porter.stem(word) for word in tokens_filtrados]

# Calcular la distribución de frecuencia de las palabras
dist_freq = FreqDist(tokens_derivados)
print("Distribución de frecuencia:")
print(dist_freq.most_common())
