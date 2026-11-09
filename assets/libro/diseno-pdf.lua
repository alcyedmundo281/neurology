-- Filtro Lua de diseño editorial para la salida PDF (LuaLaTeX) de medsemiotics.
-- Convierte divisiones semánticas de Quarto en entornos LaTeX definidos en
-- assets/libro/preambulo.tex y reemplaza reglas horizontales por filetes.

local MapaEntornos = {
  ["portadilla-pdf"] = "portadillapdf",
  ["portadilla-titulo"] = "portadillatitulo",
  ["creditos-pdf"] = "creditospdf",
  ["dedicatoria-pdf"] = "dedicatoriapdf",
  ["triada-signo"] = "triadasigno",
  ["alerta-ficha"] = "alertaficha",
  ["caso-socratico"] = "casosocratico",
  ["perlas-clinicas"] = "perlasclinicas",
  ["enlace-ficha"] = "enlaceficha",
  ["legado"] = "legadoobra",
}

local function envolver_entorno(bloques, nombre_entorno)
  local resultado = pandoc.List({
    pandoc.RawBlock("latex", "\\begin{" .. nombre_entorno .. "}"),
  })
  resultado:extend(bloques)
  resultado:insert(pandoc.RawBlock("latex", "\\end{" .. nombre_entorno .. "}"))
  return resultado
end

function Div(el)
  if not quarto.doc.is_format("pdf") then
    return nil
  end
  for clase, entorno in pairs(MapaEntornos) do
    if el.classes:includes(clase) then
      return envolver_entorno(el.content, entorno)
    end
  end
  return nil
end

function HorizontalRule()
  if not quarto.doc.is_format("pdf") then
    return nil
  end
  return pandoc.RawBlock(
    "latex",
    "\\par\\vspace{0.55em}\\noindent{\\color{libroborde}\\rule{\\linewidth}{0.4pt}}\\par\\vspace{0.55em}"
  )
end
