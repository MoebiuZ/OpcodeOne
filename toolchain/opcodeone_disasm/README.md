# OpcodeOne Disassembler Modular

Implementación modular activa del desensamblador.

Objetivo:

- separar el desensamblador por dominios claros
- facilitar evolución y pruebas sin mezclar decode, IO, formato y viewer

Módulos:

- `constants.py`
  constantes compartidas para resaltado y tema
- `model.py`
  tipos de datos y errores del desensamblador
- `theme.py`
  carga de tema, colores y construcción de paleta curses
- `formatting.py`
  helpers de texto, literales, tokens y render plano
- `json_decoder.py`
  runtime JSON-driven que carga la bundle ISA y reconstruye la sintaxis canónica o la superficie compacta documentada desde `encoding`, `syntax` y `compact_syntax`
- `decode.py`
  parsing de palabras, autodetección y wrapper público sobre el decoder JSON-driven
- `listing.py`
  construcción de listados `CODE SEGMENT` y `DATA SEGMENT`
- `io.py`
  lectura de entradas `O1OB`, legacy y autodetección
- `viewer.py`
  visor interactivo curses
- `cli.py`
  interfaz de línea de comandos

Estado actual:

- esta carpeta ya contiene implementación propia real
- el decode estricto activo ya deriva familias, formas y opcodes desde la bundle JSON de `isa/v0.9/`
- el paquete modular conserva compatibilidad observable con el flujo cubierto por los tests actuales
- el CLI `o1disasm` acepta `--compact` para volcar la superficie compacta no normativa
- el visor curses permite alternar entre sintaxis canónica y compacta con la tecla `c`
