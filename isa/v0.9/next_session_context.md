# Contexto para la próxima sesión sobre `OpcodeOne` ISA

## Estado general

`tmp/ISA_v0.9.md` pasa a considerarse un documento histórico de trabajo.

La referencia legible principal para `OpcodeOne ISA v0.9` es el libro bajo `docs/src/`, y la fuente machine-readable normativa sigue viviendo en `isa/v0.9/`.

La fuente machine-readable vive en `isa/v0.9/` y ya es coherente en forma, pero **solo cubre las familias que están realmente cerradas**.

Si se conserva `tmp/ISA_v0.9.md`, debe tratarse como material histórico y no como fuente editorial principal.

Las decisiones pendientes abiertas del proyecto no deben mantenerse aquí como lista paralela: la referencia canónica para pendientes es `TODO.md`.

## Base ya cerrada

Estas partes están suficientemente consolidadas:

- modelo general: palabra de 16 bits, direcciones de 24 bits, little-endian, sin alineación
- bancos de registros: `A..H`, `X..W`, `K`, `SP`, `PC`
- familias de memoria y movimiento: `MEMREGOFF`, `MEMABS8`, `MEMABS16`, `MEMABS24`, `MOVECOPY`
- pila y flujo: `STACK`, `FLOW`, `SYSTEM`
- ALU ya cerrada: `PLUS`, `MINUS`, `TIMES`, `DIV`, `UNARY`, `SET`, `LOGIC`, `BIT`, `MINMAX`, `SHIFT`, `ROTATE`
- saltos: `JABS`, `JREG`, `JCOND`

Decisiones ya fijadas:

- `BP` y `FP` no existen
- división por cero queda como comportamiento no definido
- `FLOW` ya tiene codificación completa para `ENTER addr`, `ENTER reg24` y `LEAVE`
- la sintaxis compacta salió del documento principal y quedó como extra separado

## Cierre actual

No quedan familias técnicas pendientes de cierre dentro del alcance ya modelado en `isa/v0.9/`.

## Estado de la fuente JSON

`isa/v0.9/` ya está normalizado y validado como fuente de verdad para las familias cerradas.

Actualmente cubre:

- `MOVECOPY`
- `MEMREGOFF`
- `MEMABS8`
- `MEMABS16`
- `MEMABS24`
- `STACK`
- `FLOW`
- `SYSTEM`
- `PLUS`
- `MINUS`
- `TIMES`
- `DIV`
- `UNARY`
- `SET`
- `LOGIC`
- `BIT`
- `MINMAX`
- `SHIFT`
- `ROTATE`
- `JABS`
- `JREG`
- `JCOND`

Archivos importantes:

- `isa/v0.9/index.json`
- `isa/v0.9/generated/opcodeone_isa_v0.9.full.json`
- `isa/v0.9/model_terms.md`

Regla práctica:

- cuando se cierre o cambie una familia en la documentación legible principal, hay que mantener `isa/v0.9/` alineado en el mismo cambio

## Uso recomendado

Usa este archivo solo como contexto resumido de estado para la ISA ya cerrada.

Para trabajo pendiente real:

- consulta `TODO.md`
- actualiza `TODO.md` en el mismo cambio si se abre, cierra o reformula una decisión pendiente
