# Instalar y cargar la biblioteca tidymodels
#install.packages("tidymodels")
#este ejercicio proporciona una visión completa del proceso de análisis de 
#regresión lineal utilizando tidymodels en R, desde la preparación 
#hasta la interpretación de los resultados del modelo ajustado basado en un conjunto de datos llamado "mtcars".
#Este conjunto de datos es un conjunto de datos clásico en R que contiene información
#sobre diferentes características de varios modelos de automóviles


library(tidymodels)

# Cargar el conjunto de datos mtcars
data(mtcars)

# Crear un marco de datos tibble (tidyverse) para trabajar con tidymodels
mtcars_tibble <- as_tibble(mtcars)

# Crear especificación de receta para preprocesamiento
receta <- recipe(mpg ~ wt + hp, data = mtcars_tibble) %>%
  step_scale(all_predictors()) %>%
  step_center(all_predictors())

# Crear modelo de regresión lineal
modelo <- linear_reg() %>%
  set_engine("lm") %>%
  set_mode("regression")

# Combinar la receta y el modelo en un flujo de trabajo
wf <- workflow() %>%
  add_recipe(receta) %>%
  add_model(modelo)

# Ajustar el modelo
ajuste <- fit(wf, data = mtcars_tibble)

# Visualizar los resultados del ajuste
summary(ajuste)

# Realizar predicciones
predicciones <- predict(ajuste, new_data = mtcars_tibble)

# Visualizar los resultados
plot(mtcars$mpg, predicciones$.pred, xlab = "MPG Observado", ylab = "MPG Predicho", main = "MPG Observado vs MPG Predicho")
abline(0, 1, col = "red")  # Agregar una línea de igualdad

