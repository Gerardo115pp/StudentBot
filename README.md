# Student bot

## Instalacion y Uso(para dummys :3)

primero que nada descarga el release 0.9 desde aqui
[Releases](https://github.com/Gerardo115pp/StudentBot/releases/tag/0.9)


<img src="https://github.com/Gerardo115pp/StudentBot/blob/with_docs/imgs_docs/releases.png?raw=true"/>

descarga el que dice 'ReadyToUse', y de los 3 archivos que te van a aparecer, solo necesitas StudentBotv0.9

* StudentBotv0.9.zip <--- ESTE
* Source code(zip)
* Source code(tar.gz)

Extraelos y te deberian quedar estos archivos:

|StudentBotv0.9.zip|
|------|
|BotSelectors.py|
|meetBot.py|
|pydependencys.txt|
|Recorder.py|
|schedule.json|
|thrid-party-dependencys.zip|
|user_data.json|

<br/>

> **Antes de continuar vale la pena mencionar que dare por sentado que tienes instalado Python3.6+. si no es asi necesitas instalarlo antes, googlealo, es facil. Ademas de eso tiene que tener instalada la version 86 de chrome y tambien es importante mencionar que por el momento este bot solo es compatible con windows. aunque no costaria demasiado hacerlo compatible con linux, si ten interesa esa caracteristica comentamelo**

<br/>

primero que nada en la consola estando en el mismo directorio ejecuta el siguiente commando para instalar los modulos de python necesarios

```
pip install -r pydependencys.txt
```

extrae *thrid-party-dependencys.zip* tendras estos archivos:

|thrid-party-dependencys.zip|
|------|
|chromedriver.exe|
|ffmpeg-N-99880-g8fbcc546b8-win64-gpl-shared.zip|
|Setup.Screen.Capturer.Recorder.v0.12.11|


chromedriver
: es el driver que vamos a usar para controlar chrome, ponlo en el mismo direcotrio que el resto de archivos (los .py)

ffmpeg-N-99880-g8fbcc546b8-win64-gpl-shared.zip
:es un proyecto OpenSource para hacer diferentes tareas con video, lo necesitaremos para grabar las clases

Setup.Screen.Capturer.Recorder.v0.12.11.exe
: es una herramienta de ffmpeg para encontrar la pantalla y el displositivo de salida de audio correctos, este simplemente dale doble click eh instalalo como cualquier otro programa

## **instalando ffmpeg**
---
descomprime ffmpeg en una carpeta apropiada, preferiblemente en ProgramFiles(C:\Program Files\ffmpeg tomaremos por ejemplo).
ahora necesitas agregar la ruta C:\Program Files\ffmpeg\bin (si lo descomprimiste en otro lado pues en ese directorio + \bin ) a tu path, eso te lo explicaran [Aqui](https://medium.com/@01luisrene/como-agregar-variables-de-entorno-s-o-windows-10-e7f38851f11f)

una vez tengas eso asegurate de recargar las variables de entorno(aka reinicia tu terminal) ya tienes instalado ffmpeg. para verificarlo ejecuta el comando 

```
ffmpeg
```

si eso te lanza como respuesta otra cosa que no sea *'ffmpeg' no se reconoce como comando interno o externo* es que lo instalaste correctamente

okey ahora teniendo instalado:
*chromedriver.exe
*ffmpeg
*Setup.Screen.Capturer.Recorder.v0.12.11

ya solo tenemos que configurar tus datos para el uso del bot

## **configurando user_data.json**
---

si abres el archivo user_data.json veras algo como esto 

```

primero que nada configuremos tus datos para que el bot pueda usar tu cuenta.
abre el archivo meetBot.py

ve hasta abajo y borra todo lo que hay despues del `if if __name__ == "__main__":`

y pon esto:

```
if __name__ == "__main__":
    secretary = ScheduleHandler("lalo")
    while True:
        pass
```

despues ejecuta meetBot.py

```
python meetBot.py
```

ahora te deberia aparecer un navegador de chrome, en este navegador inicia sesion con tu **cuenta que usas para entrar a tu clases**

### ahora hay que configurar tus clases

abre el user_data.json

{
    "meet": "https://meet.google.com",
    "lalo":{
        "udg_account": "YOUR_UDG_EMAIL",
        "password": "YOUR_PASSWORD",
        "asignatures": {
            "ESTE ES EL NOMBRE DE LA CLASE": {
                "code":"ESTE ES EL CODIGO DE LA CLASE"
            }
        }
    }
}
```

ignora por completo los campos 'udg_account' y 'password'

el nombre de la clase puede se cualquier nombre random, pero el codigo de la clase debe ser el codigo de invitacion de la clase

![alt Este](https://github.com/Gerardo115pp/StudentBot/blob/with_docs/imgs_docs/class_code.png?raw=true)

teniendo esto ahora hay que configurar el schedule.json, que es el archivo que utilizara el bot para saber cuando logearse a que clase, cuando abras el archivo veras que contiene algo como esto

```
{
    "1,3:09:05": {
        "class_name": "SDTII",
        "stay": 15
    }
}
```

la llave `"1,3:09:05"` indica una clase que ocurre todos los martes y jueves, comienza a las 9:05, valor 'stay' es la cantidad de minutos que el bot se mantendra en la clase, el valor class_name debe ser el mismo que pusisite en user_data.json

### *schedule.json*

```
{
    "1,3:09:05": {
        "class_name": "IGUAL AQUI!!",
        "stay": 15
    }
}
```

### *user_data.json*
```
{
    "meet": "https://meet.google.com",
    "lalo":{
        "udg_account": "YOUR_UDG_EMAIL",
        "password": "YOUR_PASSWORD",
        "asignatures": {
            "IGUAL AQUI!!": {
                "code":"ESTE ES EL CODIGO DE LA CLASE"
            }
        }
    }
}
```

ahora tienes todo configurado. solo tienes que abrir el meetBot.py y cambian el `if __name__ == "__main__":` por esto

```
if __name__ == "__main__":
    secretary = ScheduleHandler("lalo")
    secretary.awaitEvent()
    # secretary.shutdownAt("hh:mm") decomenta si quieres que el bot apague tu computadora en un perdiodo de tiempo definido por hh:mm
    del secretary.student_bot
    exit(0)
```

ahora correlo y el bot esperara a que la clase empiece, si tienes algun problema comentamelo por Whatsapp
