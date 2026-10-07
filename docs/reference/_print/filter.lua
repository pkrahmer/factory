--[[
Pandoc filter: the reference's Markdown conventions as book elements, for the Typst writer.

Metadata it reads (set by book.py with -M):
  chapter   the chapter's folder name, e.g. "02-concepts", or "preface"
  planner   "true" or "false": keep or drop the planner boxes
  included  the folder names in this build, separated by commas
  figdir    where book.py put the print figures, as Typst sees them (root-relative)
  figfs     the same folder on disk, to read each figure's size
  repo_url  the repository's blob URL at the pinned commit, e.g. https://github.com/o/r/blob/abc1234

What it does:
  - GitHub alerts (`> [!NOTE]`, `> [!IMPORTANT] **Planner:**`, `> [!WARNING] **v1 limit:**`)
    become #note, #planner and #limitbox; planner boxes are dropped when planner=false. The
    box's label replaces the lead, and the word after it gains a capital.
  - The chapter's first-level heading "4. Work items" becomes #chapter-opener("4") followed by
    the level-1 heading "Work items" with the chapter's label; in the preface the document
    title is dropped and "## Preface" becomes the chapter's heading.
  - A paragraph that is only an image, followed by an italic "Figure n-m. …" paragraph,
    becomes #book-figure(…) with the caption, a short caption for the list of figures (the
    SVG's own title) and the SVG's size.
  - Links: to a chapter in this build, a cross-reference with its page ("chapter 3 (page 27)",
    or "chapter 3, page 27" inside parentheses); to a chapter not yet written, plain text; to a
    figure's description, plain text; to any other repository file or to the web, the text
    with the URL in a footnote.
  - A paragraph directly before a table is kept on the table's page.
  - "chapter 4", "page 29", "Figure 2-1" and the like are tied with a non-breaking space.
  - HTML comments are dropped; header identifiers get the chapter as prefix.
]]

local stringify = pandoc.utils.stringify

local chapter = "preface"
local keep_planner = true
local included = {}
local figdir = "figures"
local figfs = "figures"
local repo_url = ""

local function raw(text) return pandoc.RawInline("typst", text) end
local function rawblock(text) return pandoc.RawBlock("typst", text) end

-- The Typst writer turns the apostrophe back into ', for Typst's smart quotes, but Typst reads
-- ' after a digit as a prime ("v1′s"). There the apostrophe is written out as the character.
local APOSTROPHE = "\u{2019}"
local NBSP = "\u{00A0}"

local function keep_apostrophes(str)
  local text = str.text
  if not text:find("%d" .. APOSTROPHE) then return nil end
  local out = pandoc.Inlines({})
  local start = 1
  for at in text:gmatch("%d()" .. APOSTROPHE) do
    out:insert(pandoc.Str(text:sub(start, at - 1)))
    out:insert(raw(APOSTROPHE))
    start = at + #APOSTROPHE
  end
  out:insert(pandoc.Str(text:sub(start)))
  return out
end

local function typst_inlines(inlines)
  local doc = pandoc.Pandoc({ pandoc.Plain(inlines) }):walk({ Str = keep_apostrophes })
  return (pandoc.write(doc, "typst"):gsub("%s+$", ""))
end

local function typst_string(text)
  return '"' .. text:gsub("\\", "\\\\"):gsub('"', '\\"') .. '"'
end

local function label_of(folder) return "<ch-" .. folder .. ">" end

-- Resolve a relative link from this chapter's folder to a path inside docs/reference or the repo.
local function resolve(target)
  local parts = {}
  local base = chapter == "preface" and "docs/reference" or ("docs/reference/" .. chapter)
  for part in base:gmatch("[^/]+") do table.insert(parts, part) end
  for part in target:gmatch("[^/]+") do
    if part == ".." then table.remove(parts)
    elseif part ~= "." then table.insert(parts, part) end
  end
  return table.concat(parts, "/")
end

function Meta(meta)
  chapter = meta.chapter and stringify(meta.chapter) or chapter
  -- `-M planner=false` arrives as a YAML boolean, not as the string "false"
  keep_planner = not (meta.planner == false
    or (meta.planner ~= nil and stringify(meta.planner) == "false"))
  figdir = meta.figdir and stringify(meta.figdir) or figdir
  figfs = meta.figfs and stringify(meta.figfs) or figfs
  repo_url = meta.repo_url and stringify(meta.repo_url) or repo_url
  if meta.included then
    for name in stringify(meta.included):gmatch("[^,]+") do included[name] = true end
  end
end

-- Alerts ---------------------------------------------------------------------------------------

local function strip_lead(blocks, lead)
  -- Drop a leading **Lead:** from the first paragraph, which the box's label replaces. What
  -- followed the colon now begins the box, so a plain lowercase word gains its capital; a name
  -- such as "v1" keeps its own spelling.
  local first = blocks[1]
  if first and (first.t == "Para" or first.t == "Plain") and first.content[1]
      and first.content[1].t == "Strong" and stringify(first.content[1]) == lead then
    first.content:remove(1)
    if first.content[1] and first.content[1].t == "Space" then first.content:remove(1) end
    local word = first.content[1]
    if word and word.t == "Str" and word.text:match("^%l[%l%p]*$") then
      word.text = word.text:sub(1, 1):upper() .. word.text:sub(2)
    end
  end
  return blocks
end

local function boxed(fn, blocks)
  local out = pandoc.Blocks({ rawblock("#" .. fn .. "[") })
  out:extend(blocks)
  out:insert(rawblock("]"))
  return out
end

local function alert(div)
  local kind = div.classes[1]
  local blocks = pandoc.Blocks({})
  for _, b in ipairs(div.content) do
    if not (b.t == "Div" and b.classes:includes("title")) then blocks:insert(b) end
  end
  local lead = blocks[1] and blocks[1].content and blocks[1].content[1]
  local lead_text = lead and lead.t == "Strong" and stringify(lead) or ""
  if kind == "important" and lead_text == "Planner:" then
    -- The preface explains the boxes with one of each, so its sample stays in every edition.
    if not keep_planner and chapter ~= "preface" then return {} end
    return boxed("planner", strip_lead(blocks, "Planner:"))
  elseif kind == "warning" and lead_text == "v1 limit:" then
    return boxed("limitbox", strip_lead(blocks, "v1 limit:"))
  elseif kind == "warning" or kind == "caution" then
    return boxed("warnbox", blocks)
  elseif kind == "tip" then
    return boxed("tipbox", blocks)
  end
  return boxed("note", blocks)
end

-- Figures --------------------------------------------------------------------------------------

-- The print figure's size in px and its own title, which names it in the list of figures.
local function svg_head(path)
  local file = io.open(path, "r")
  if not file then return 0, 0, nil end
  local head = file:read(4000) or ""
  file:close()
  local tag = head:match("<svg[^>]*>") or ""
  local width = tonumber(tag:match(' width="(%d+)"')) or 0
  local height = tonumber(tag:match(' height="(%d+)"')) or 0
  local title = head:match("<title[^>]*>([^<]+)</title>")
  if title then
    title = title:gsub("&amp;", "&"):gsub("&lt;", "<"):gsub("&gt;", ">"):gsub("&#39;", "'")
      :gsub("&quot;", '"'):gsub("'", APOSTROPHE)
  end
  return width, height, title
end

local function figure(image, caption)
  local name = image.src:match("([^/]+)%.svg$")
  local src = figdir .. "/" .. chapter .. "/" .. name .. ".svg"
  local width, height, title = svg_head(figfs .. "/" .. chapter .. "/" .. name .. ".svg")
  local text = stringify(caption):gsub(NBSP, " ")
  local number, rest = text:match("^(Figure%s+[%w%-]+)%.%s*(.*)$")
  -- the list of figures names a figure by its drawing's title, else by its caption's lead
  local short = title or (rest and rest:match("^([^:;]+)") or text):gsub("%.$", "")
  -- The caption without its "Figure n-m." lead, which the template sets itself: inlines are
  -- dropped until they have spelled it, then the spaces after it.
  local inlines = caption:clone()
  if number then
    local dropped = ""
    while #inlines > 0 and dropped ~= number .. "." do
      dropped = (dropped .. stringify(inlines:remove(1)):gsub(NBSP, " ")):gsub("^%s+", "")
    end
    while inlines[1] and (inlines[1].t == "Space" or inlines[1].t == "SoftBreak") do
      inlines:remove(1)
    end
  end
  -- the blank line after it keeps the next paragraph out of the call's line
  return rawblock(string.format(
    "#book-figure(%s, number: %s, short: %s, width-px: %d, height-px: %d)[%s]\n",
    typst_string(src), typst_string(number or ""), typst_string(short), width, height,
    typst_inlines(inlines)))
end

-- Headings -------------------------------------------------------------------------------------

local function chapter_head(header)
  local text = stringify(header.content)
  local number, title = text:match("^(%w+)%.%s+(.+)$")
  local title_inlines = header.content:clone()
  if number then
    -- drop "4." and the space after it
    title_inlines:remove(1)
    if title_inlines[1] and title_inlines[1].t == "Space" then title_inlines:remove(1) end
  end
  return rawblock(string.format("#chapter-opener(%s)\n\n= %s %s",
    typst_string(number or ""), typst_inlines(title_inlines), label_of(chapter)))
end

-- The document ---------------------------------------------------------------------------------

function Pandoc(doc)
  local blocks = doc.blocks
  local out = pandoc.Blocks({})
  local i = 1
  local preface_head_done = false
  while i <= #blocks do
    local b = blocks[i]
    if b.t == "RawBlock" and b.format == "html" then
      -- comments and other raw HTML have no place in print
    elseif b.t == "Header" and chapter == "preface" and b.level == 1 then
      -- the book's title page carries the title
    elseif b.t == "Header" and chapter == "preface" and b.level == 2 and not preface_head_done then
      out:insert(rawblock("#chapter-opener(\"\")\n\n= " .. typst_inlines(b.content) .. " "
        .. label_of("preface")))
      preface_head_done = true
    elseif b.t == "Header" and b.level == 1 then
      out:insert(chapter_head(b))
    elseif b.t == "Header" then
      if chapter == "preface" then b.level = b.level - 1 end
      b.identifier = chapter .. "-" .. b.identifier
      out:insert(b)
    elseif b.t == "Div" and #b.classes > 0 and b.content[1] and b.content[1].t == "Div"
        and b.content[1].classes:includes("title") then
      out:extend(alert(b))
    elseif b.t == "Para" and #b.content == 1 and b.content[1].t == "Image"
        and blocks[i + 1] and blocks[i + 1].t == "Para" and blocks[i + 1].content[1]
        and blocks[i + 1].content[1].t == "Emph"
        and stringify(blocks[i + 1].content[1]):match("^Figure") then
      out:insert(figure(b.content[1], blocks[i + 1].content[1].content))
      i = i + 1
    elseif b.t == "Para" and blocks[i + 1] and blocks[i + 1].t == "Table" then
      -- the paragraph that leads into a table goes to the next page with it (#lead-in)
      local after_heading = blocks[i - 1] and blocks[i - 1].t == "Header"
      out:insert(rawblock(after_heading and "#lead-in(after-heading: true)[" or "#lead-in["))
      out:insert(b)
      out:insert(rawblock("]"))
    else
      out:insert(b)
    end
    i = i + 1
  end
  doc.blocks = out
  return doc
end

-- Links (run before Pandoc(), as an inline filter) ----------------------------------------------

local function footnote_url(url)
  return pandoc.Note({ pandoc.Plain({ pandoc.Code(url) }) })
end

-- `aside`: nil outside parentheses; inside them "end" when the parenthesis closes after the
-- link, "more" when its text goes on. The page then follows a comma instead of more parentheses.
local function chapter_link(link, folder, aside)
  if not included[folder] then return link.content end
  local out = pandoc.Inlines({ raw("#link(" .. label_of(folder) .. ")[") })
  out:extend(link.content)
  local args = label_of(folder)
  if aside then args = args .. ", inner: true" .. (aside == "more" and ", more: true" or "") end
  out:insert(raw("]#chapter-page(" .. args .. ")"))
  return out
end

local function convert_link(link, aside)
  local target = link.target
  if target:match("^https?://") then
    if stringify(link.content) == target then return pandoc.Inlines({ pandoc.Code(target) }) end
    local out = pandoc.Inlines(link.content)
    out:insert(footnote_url(target))
    return out
  end
  if target:match("^#") then return link.content end
  local path = target:gsub("#.*$", "")
  local resolved = resolve(path)
  local folder = resolved:match("^docs/reference/([^/]+)/README%.md$")
  if folder then return chapter_link(link, folder, aside) end
  if resolved == "docs/reference/README.md" then return chapter_link(link, "preface", aside) end
  if resolved:match("^docs/reference/.+%.md$") then return link.content end
  local out = pandoc.Inlines(link.content)
  out:insert(footnote_url(repo_url .. "/" .. resolved))
  return out
end

-- A word that names a numbered thing stays on one line with its number: "chapter 4", "page 29",
-- "Figure 2-1", "run 4".
local NUMBERED = {
  chapter = true, chapters = true, page = true, figure = true, part = true, appendix = true,
  run = true, runs = true, generation = true, criterion = true, step = true,
}

local function tie(before, after)
  return before and after and before.t == "Str" and after.t == "Str"
    and NUMBERED[before.text:lower():gsub("^%(", "")] and after.text:match("^%(?[%dIVX]")
end

-- Each run of inlines is walked in order, counting the parentheses the text has opened, so a
-- link knows whether it stands inside them, and whether the aside goes on after it.
function Inlines(inlines)
  local out = pandoc.Inlines({})
  local depth = 0
  for i, el in ipairs(inlines) do
    if el.t == "Link" then
      local aside = nil
      if depth > 0 then
        local after = inlines[i + 1]
        local goes_on = after and (after.t == "Space" or after.t == "SoftBreak")
        aside = goes_on and "more" or "end"
      end
      out:extend(convert_link(el, aside))
    elseif (el.t == "Space" or el.t == "SoftBreak") and tie(inlines[i - 1], inlines[i + 1]) then
      out:insert(pandoc.Str(NBSP))
    else
      if el.t == "Str" then
        local _, opened = el.text:gsub("%(", "")
        local _, closed = el.text:gsub("%)", "")
        depth = math.max(0, depth + opened - closed)
      end
      out:insert(el)
    end
  end
  return out
end

return {
  { Meta = Meta },
  { Inlines = Inlines },
  { Pandoc = Pandoc },
  { Str = keep_apostrophes },
}
