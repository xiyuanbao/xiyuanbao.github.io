-- scripts/author_mark.lua
-- Bold target author names and add daggers in Pandoc AST for CSL entries.

local bold_pairs = {
  {last="Bao", first="Xiyuan"},
}

local dagger_pairs = {
  {last="Zhang", first="Xubo"},
  {last="Li", first="Shaohua"},
}

local function str_text(node) return (node and node.t=="Str") and node.text or nil end
local function is_space(node) return node and (node.t=="Space" or (node.t=="Str" and node.text==" ")) end

local function strip_punct(s)
  return s and s:gsub("[,%.]$","") or s
end

local function push(tbl, x) tbl[#tbl+1] = x end

-- replace-inline sequence with bold wrapper
local function wrap_bold(seq)
  local out = { pandoc.RawInline("html","<strong>") }
  for _,n in ipairs(seq) do push(out, n) end
  push(out, pandoc.RawInline("html","</strong>"))
  return out
end

local function process_inlines(inlines, targets, mode)
  local out = {}
  local i = 1
  while i <= #inlines do
    local a = inlines[i]
    local b = inlines[i+1]
    local c = inlines[i+2]

    local handled = false
    if a and b and c and is_space(b) and str_text(a) and str_text(c) then
      local at = strip_punct(str_text(a))
      local ct = strip_punct(str_text(c))

      for _, t in ipairs(targets) do
        -- patterns: "Last," " " "First"  OR  "First" " " "Last,"
        if (at == t.last and ct == t.first) or (at == t.first and ct == t.last) then
          if mode == "bold" then
            local seq = {a,b,c}
            for _,n in ipairs(wrap_bold(seq)) do push(out, n) end
          elseif mode == "dagger" then
            push(out, a); push(out, b); push(out, c); push(out, pandoc.Str("†"))
          end
          i = i + 3
          handled = true
          break
        end
      end
    end

    if not handled then
      push(out, a)
      i = i + 1
    end
  end
  return out
end

function Div(el)
  if el.classes:includes("csl-entry") then
    for bi, blk in ipairs(el.content) do
      if blk.t=="Plain" or blk.t=="Para" then
        blk.content = process_inlines(blk.content, bold_pairs, "bold")
        blk.content = process_inlines(blk.content, dagger_pairs, "dagger")
        el.content[bi] = blk
      end
    end
    return el
  end
  return nil
end
