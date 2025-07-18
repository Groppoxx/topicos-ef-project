# Examen Final: Tópicos de Ciencias de la Computación

**Alumno:** Iam Anthony Marcelo Alvarez Orellana  
**Código:** u202118258

## Descripción del Proyecto

En la simulación del **Smart Home** se crearon cuatro agentes según lo solicitado en el examen:

1. **Washer** (lavadora)  
2. **Dishwasher** (lavaplatos)  
3. **Lights** (luces inteligentes)  
4. **EnergyManager** (administrador central de energía)  

Cada electrodoméstico tiene una **hora ideal de finalización**, pero para darle dinamismo se introduce:

- Un margen aleatorio de **±1 hora** sobre su preferencia.
- Para las **luces**, además un ajuste de **±10 % de brillo**.

Cada **10 segundos**, cada dispositivo envía su petición al EnergyManager con:
- **Modo**: `eco` o `normal`.  
- **Hora preferida** de finalización.  
- **Brillo** (solo en el agente de luces).  

El **EnergyManager**, que conoce dos tramos de tarifa (horas pico y no pico), aplica una regla sencilla:

- **Si es hora pico**: sugiere pasar a **modo eco**, adelantar el inicio ±1 h y reducir el brillo un **30 %**.  
- **Si no es hora pico**: mantiene el modo y horario solicitados.  

La propuesta viaja de vuelta a cada dispositivo, que la **acepta** o **rechaza** según cuánto se desvíe de su preferencia (±2 h y ±20 % de brillo). El ciclo “Petición → Propuesta → Aceptar/Rechazar” se repite continuamente, simulando la negociación dinámica de un hogar inteligente.

## Instalación y Ejecución

1. **Clonar este repositorio**  
   ```bash
   git clone <URL-de-tu-repositorio>
   cd <tu-repositorio>
   ```

2. **Crear y activar el entorno virtual**  
   ```bash
   python -m venv venv
   venv\Scripts\activate       # En Windows
   ```
   
3. **Instalar dependencias**  
   ```bash
   pip install spade
   ```

4. **Registrar los agentes en Prosody**  
   ```bash
   sudo prosodyctl register energymanager localhost 1234
   sudo prosodyctl register washer         localhost 1234
   sudo prosodyctl register dishwasher     localhost 1234
   sudo prosodyctl register lights         localhost 1234
   ```

5. **Verificar cuentas creadas**  
   ```bash
   sudo ls /var/lib/prosody/localhost/accounts
   ```

## Uso de Inteligencia Artificial
Durante el desarrollo he contado con la asistencia de ChatGPT para:

* **Redacción del README:** estructurar secciones, mejorar la legibilidad y el estilo.

* **Corrección y refactorización de código:** optimizar comportamientos SPADE y ajustar la lógica de negociación.

* **Generación de comandos en WSL/Prosody:** asegurar los pasos exactos para registrar y validar agentes.
