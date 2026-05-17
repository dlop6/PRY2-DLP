## Descripción

Esta actividad consiste en la implementación de un generador de analizadores sintácticos, el cual, tomando como entrada un archivo escrito en YAPar, generará un analizador sintáctico SLR que deberá interactuar con un analizador léxico y será capaz de parsear un flujo de tokens. Además, deberá informar de los errores léxicos y sintácticos encontrados.

Para trabajar con YAPar, revise el siguiente documento:

[](https://uvg.instructure.com/courses/43731/files/11011282?wrap=1 "Enlace")[Consideraciones de YAPar.pdf](https://uvg.instructure.com/courses/43731/files/11011270?wrap=1 "Enlace")[Descargar Consideraciones de YAPar.pdf](https://uvg.instructure.com/courses/43731/files/11011270/download?download_frd=1)

## Objetivos

**Objetivo general**

* Implementar un generador de analizadores sintácticos.

**Objetivos específicos**

* Aplicar la teoría de analizadores sintácticos en la construcción de una herramienta de software generadora de dichos componentes.
* Implementar una herramienta de software que sea capaz de generar analizadores sintácticos funcionales basados en la especificación de gramáticas libres de contexto.
* Lograr la interacción entre un analizador léxico y una analizador sintáctico.

## Especificación del funcionamiento del generador de analizadores sintácticos

**Entrada**

* Un archivo que contiene la especificación del analizador léxico a generar, escrita en lenguaje YALex.
* Un archivo que contiene la especificación del analizador sintáctico a generar, escrita en lenguaje YAPar.

**Salida**

* Diagrama de transición de estados que representa la especificación de componentes léxicos definida.
* **Autómata LR(0) representado visualmente, el cual fue construido a** **partir de la gramática libre de contexto contenida en el archivo YAPar.**
* **Un programa fuente que implementa el analizador léxico y el analizador sintáctico con base en las especificaciones ingresadas en lenguaje YALex y YAPar, respectivamente.**

## Especificaciones del funcionamiento del analizador léxico y analizador sintáctico

**Entrada**

* Un archivo de texto plano con cadenas de caracteres.

**Salida**

* La impresión en pantalla de la secuencia de acciones que permitieron analizar sintácticamente el flujo de tokens, o en su defecto, los mensajes de los errores léxicos y sintácticos detectados.

**Funcionamiento**

* El analizador léxico procesará el archivo de texto plano de entrada y generará un flujo de tokens.
* El analizador sintáctico solicitará tokens al analizador léxico generado (uno a la vez) y los parseará.

## Entregables

Un documento que incluya:

* El nombre de los integrantes del grupo que colaboraron activamente en el proyecto y que tendrán derecho a nota.
* Diseño del software.
* Enlace al repositorio de GitHub con el código de la implementación.
* Documentación y explicación del código.

## Observaciones y restricciones

* La actividad deberá realizarse en los grupos que se conformaron al principio del semestre.
* El lenguaje de programación a utilizar para desarrollar el generador de analizadores sintácticos queda a elección del grupo.
* El software deberá contar con una interfaz gráfica amigable y estética. El incumplimiento de esta restricción se penalizará restando 3 puntos a la nota obtenida.
* El funcionamiento del analizador léxico generado deberá ser independiente del generador de analizadores léxicos. El incumplimiento de esta restricción se penalizará restando 3 puntos a la nota obtenida.
* El funcionamiento del analizador sintáctico generado deberá ser independiente del generador de analizadores sintácticos. El incumplimiento de esta restricción se penalizará restando 3 puntos a la nota obtenida.
* El uso de librerías para expresiones regulares está estrictamente prohibido; esta funcionalidad se deberá desarrollar por medio de autómatas finitos. El incumplimiento de esta restricción se penalizará colocando 0 puntos de nota.
* Cada grupo deberá escribir los archivos de prueba que se utilizarán en la
  calificación (especificación del analizador léxico, especificación del analizador sintáctico y archivo de texto plano de entrada); al menos tres grupos (de tres elementos): uno
  con complejidad baja, otro con complejidad media y otro con complejidad
  alta. El incumplimiento de este requerimiento se penalizará colocando 0 puntos de nota.
* A cada estudiante se le realizarán al menos dos preguntas directas, las cuales podrán ser preguntas teóricas o explicaciones sobre el código fuente.
