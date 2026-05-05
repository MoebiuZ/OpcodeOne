# Modelo JSON de OpcodeOne

Este documento fija el significado de los términos usados en la fuente machine-readable de `isa/v0.9/`.

## Términos base

### `family`
Grupo arquitectónico de operaciones que comparte un `opcode_ref` y una idea común de codificación.  
Ejemplo: `PLUS`, `FLOW`, `LOGIC`.

### `form`
Variante concreta y ensamblable dentro de una familia.  
Ejemplo: en `PLUS` existen `reg_reg`, `imm6` e `imm16`.

### `shape`
Estructura JSON normalizada que debe seguir cada objeto.  
Ejemplo: una `family` siempre usa `name`, `opcode_ref`, `status`, `forms`.

### `bundle`
JSON agregado generado desde los ficheros modulares. No es la fuente canónica; solo una vista unificada.

## Sintaxis

### `syntax`
Describe cómo se escribe una forma en ensamblador canónico.

### `pattern`
Una realización concreta de la sintaxis de una forma. Una forma puede tener uno o varios patrones.

### `literal token`
Palabra fija del ensamblador, como `PLUS`, `ENTER` o `when`.

### `slot token`
Hueco variable dentro de un patrón. Puede ser:
- `operand`: operando real, como `reg24` o `imm16_signed`
- `enum`: valor elegido de un conjunto discreto
- `keyword`: palabra clave opcional, como `unsigned`

### `named literal token`
Literal de sintaxis que además emite una entrada explícita usando `name` como
clave y `value` como valor.

Ejemplo: un patrón de `LOGIC` puede usar el literal `AND` con `name:
"operation"` para emitir `sequence.operation = "AND"`.

## Modelo de datos

### `operand_kind_ref`
Referencia a un tipo de operando declarado en `operand_kinds.json`.

### `enum_ref`
Referencia a un mapa simbólico declarado en `abstract_enums.json`.

### `keyword_ref`
Referencia a una palabra clave reutilizable declarada en `abstract_kinds.json`.

### `defaults`
Valores implícitos de slots opcionales cuando no aparecen en la sintaxis.

### `constraints`
Reglas semánticas o estructurales que restringen una forma.  
Ejemplo: operandos del mismo ancho.

## Codificación

### `derived_fields`
Campos calculados a partir de entradas explícitas de `sequence` antes de
codificar.
Ejemplo: `width`, `mode`, `condition`, `addr_hi`.

### `decode_rule`
Regla usada para distinguir una forma frente a otras dentro de la misma familia.

### `encoding`
Descripción de las palabras máquina y de sus bitfields.

### `field`
Fragmento concreto dentro de una palabra: `OPCODE`, `SZ`, `RA`, `IMM16`, etc.

### `source`
Origen del valor de un campo de codificación. Solo debe apuntar a:
- `family_opcode`
- `sequence.<name>`
- `sequence.<name>.<member>`
- `derived.<name>`

### `opcode_ref`
Clave simbólica de la familia para resolver su opcode contra `opcode_slots.json`.

### `timing_model`
Tabla global que define modelos temporales exactos por `path`.

El modelo por defecto actual actúa como referencia para calibrar otras implementaciones de la VM. La fuente machine-readable usa `chronons` como nombre canónico de la unidad temporal y, hoy, esos `chronons` corresponden a enteros en picosegundos medidos sobre la VM de referencia para `RP2350`.

Dentro de cada modelo la vista temporal canónica es:

- `paths`: rutas medidas de la VM de referencia, con `chronons` exactos y su enlace a `family`, `form` y sus `conditions`
