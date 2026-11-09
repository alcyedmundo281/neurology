-- Quarto abre el libro con un `\chapter*` del título (la cabecera de index.qmd) que queda como
-- página 1, antes de la portada. La portada es la página 1: este filtro, que corre tras los de
-- Quarto, quita solo esa cabecera, la marcada `.titulo-de-obra`. El título de la portadilla es un
-- bloque aparte (`.portadilla-titulo`) y no se toca.

local quitada = false

function Header(el)
  if quitada or not quarto.doc.is_format("pdf") then
    return nil
  end
  if el.level == 1 and el.classes:includes("titulo-de-obra") then
    quitada = true
    return {}
  end
  return nil
end
