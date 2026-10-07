// The reference as a book: A4 paper with a book's measure, for printing at home.
//
// book.py writes build/main.typ, which applies `book` and includes one file per chapter; the
// chapter files come from Pandoc through filter.lua and call the functions defined here.

// --- type and color ----------------------------------------------------------------------------

#let serif = ("Libertinus Serif",)
#let sans = ("Segoe UI", "Roboto")
#let mono = ("Cascadia Mono", "DejaVu Sans Mono")

#let ink = rgb("#1d1f24")
#let muted = rgb("#5b606b")
#let hairline = rgb("#c9ced6")
#let accent = rgb("#2f6db5") // the agents' blue in the figures
#let amber = rgb("#b06a00") // the human's amber, darkened for text
#let slate = rgb("#5d6f8c")

// Inline code is sized so its x-height matches the text around it: Cascadia Mono's x-height is
// 0.52 em, Libertinus Serif's 0.43 and Segoe UI's 0.50. Typst sets code at 0.8 em by default,
// which the division undoes; em sizes multiply, so the table's factor applies on top.
#let code-in-serif = 0.85em / 0.8
#let code-in-sans = 0.93em / 0.85

// --- the page ----------------------------------------------------------------------------------

#let text-width = 128mm
#let wide-width = 156mm // figures and tables may use this, beyond the text block
#let outdent = (wide-width - text-width) / 2
#let side = (210mm - text-width) / 2
#let page-top = 30mm
#let page-bottom = 32mm
#let text-height = 297mm - page-top - page-bottom

#let chapter-number = state("chapter-number", "")

// --- small helpers called by the chapter files -------------------------------------------------

#let horizontalrule = align(center, line(length: 30%, stroke: 0.5pt + hairline))

// The page an element sits on, in that page's numbering (iii, 41).
#let page-label(loc) = {
  let style = loc.page-numbering()
  let n = counter(page).at(loc)
  if style == none { str(n.first()) } else { numbering(style, ..n) }
}

// Display text set in balanced lines: the narrowest measure that needs no more lines than the
// full one, found by halving, so a two-line subtitle does not leave one word on its own.
#let balanced(body, width: 100%) = layout(size => {
  let full = if type(width) == ratio { size.width * width } else { width }
  let height(w) = measure(block(width: w, body)).height
  let target = height(full)
  let (low, high) = (full / 3, full)
  for _ in range(12) {
    let mid = (low + high) / 2
    if height(mid) > target { low = mid } else { high = mid }
  }
  block(width: high, body)
})

// Leaders for the contents and the list of figures: light, so the titles lead.
#let dots = box(width: 1fr, repeat(gap: 0.42em, text(fill: muted)[.]))

// "chapter 3" gains its page: "chapter 3 (page 41)". Inside parentheses (`inner`) it is
// "chapter 3, page 41", so they do not nest, with a second comma when the aside goes on
// (`more`): "(chapter 3, page 41, maps them)".
#let chapter-page(target, inner: false, more: false) = context {
  let found = query(target)
  if found.len() > 0 {
    let page = page-label(found.first().location())
    if not inner [ (page~#page)] else if more [, page~#page,] else [, page~#page]
  }
}

// The paragraph that leads into a table: kept on the table's page when the table must move. A
// paragraph of more than four lines is left free, because Typst moves a kept block whole, and
// a long one would leave a gap at the foot of the page. Right after a heading it adds no space
// above: the heading's own space below is the one wanted.
#let lead-in(after-heading: false, body) = context {
  let lines = measure(block(width: text-width, body)).height / (1em + par.leading).to-absolute()
  let above = if after-heading { 0pt } else { par.spacing }
  block(above: above, below: par.spacing, sticky: lines < 4.5, body)
}

// A sidebar, its label run into the first line. A short box stays on one page; a long one may
// break, because moving it whole would leave a large gap at the foot of the page before it.
#let callout(label, fill, color, body) = context {
  let box-of(breakable) = block(
    width: 100%,
    fill: fill,
    stroke: (left: 2.4pt + color),
    inset: (left: 11pt, right: 10pt, top: 8pt, bottom: 9pt),
    radius: (right: 2pt),
    breakable: breakable,
    above: 1.5em,
    below: 1.5em,
  )[
    #set text(size: 9.2pt)
    #set par(leading: 0.58em, spacing: 0.75em)
    #set list(spacing: 0.58em)
    #let tag = text(font: sans, size: 7.8pt, weight: "bold", fill: color, tracking: 0.04em, label)
    #tag#h(0.7em)#body
  ]
  let tall = measure(box-of(false), width: text-width).height > text-height / 5
  box-of(tall)
}

#let note(body) = callout("Note", rgb("#f4f5f7"), muted, body)
#let tipbox(body) = callout("Tip", rgb("#eef7f3"), rgb("#22775e"), body)
#let warnbox(body) = callout("Warning", rgb("#fcefef"), rgb("#a32f2f"), body)
#let planner(body) = callout("For the planner", rgb("#eef4fb"), accent, body)
#let limitbox(body) = callout("v1 limit", rgb("#fff6e8"), amber, body)

// --- figures -----------------------------------------------------------------------------------

// Set ragged right under the drawing's left edge, whatever alignment places the drawing.
#let figure-caption(number, body) = align(left, {
  set text(font: sans, size: 8.2pt, fill: ink, hyphenate: false)
  set par(justify: false, leading: 0.5em)
  if number != "" [#text(weight: "bold")[#number.] ]
  body
})

// The figure kit draws its body text at 12.5 px. A figure prints in the text when that text
// reaches 6.5 pt at the wide measure; it is never enlarged beyond 8 pt, so a small drawing does
// not shout, nor made taller than most of a page.
#let label-px = 12.5
#let label-min = 6.5pt
#let label-max = 8pt

// A figure: in the text when it is narrow enough, else on its own page, turned a quarter (its
// top to the left edge, as books do) so a wide drawing keeps legible labels.
#let book-figure(src, number: "", short: "", width-px: 1000, height-px: 600, body) = {
  let ratio = height-px / width-px
  let inline = label-px * wide-width / width-px >= label-min
  let entry = [#metadata((number: number, short: short, turned: not inline)) <book-figure>]
  if inline {
    let w = calc.min(wide-width, label-max * width-px / label-px, 0.7 * text-height / ratio)
    block(width: 100%, above: 1.8em, below: 1.8em, breakable: false)[
      #entry
      #pad(x: -outdent, align(center, block(width: w, stack(
        spacing: 0.8em,
        image(src, width: w),
        figure-caption(number, body),
      ))))
    ]
  } else {
    // The turned page: the drawing's width runs down the text block's height, and the drawing
    // and its caption together across the wide measure. The caption's height depends on the
    // width it is set to, so the width is found in two rounds.
    let gap = 3mm
    let caption(w) = block(width: w, figure-caption(number, body))
    place(top, float: true, scope: "parent", clearance: 0pt, block(
      width: 100%,
      height: text-height,
      breakable: false,
    )[
      #entry
      #context {
        let w = text-height
        for _ in range(2) {
          w = calc.min(text-height, (wide-width - gap - measure(caption(w)).height) / ratio)
        }
        let drawing = stack(spacing: gap, image(src, width: w), caption(w))
        pad(x: -outdent, block(width: 100%, height: 100%, align(
          center + horizon,
          rotate(-90deg, reflow: true, drawing),
        )))
      }
    ])
  }
}

// --- tables ------------------------------------------------------------------------------------

#let table-size = 8pt
#let cell-inset = 6pt // left and right; the first column has none on its left, at the edge

// The pieces of a cell a line cannot break, as (text, code) pairs: its words, cut after the
// hyphens and slashes where a line may also break.
#let unbreakable(it, code: false) = {
  if type(it) == str {
    it.replace("-", "- ").replace("/", "/ ").split(" ").filter(w => w != "").map(w => (w, code))
  } else if it.func() == raw {
    unbreakable(it.text, code: true)
  } else if it.has("text") {
    unbreakable(it.text, code: code)
  } else if it.has("children") {
    it.children.map(c => unbreakable(c, code: code)).join(default: ())
  } else if it.has("body") {
    unbreakable(it.body, code: code)
  } else if it.has("child") {
    unbreakable(it.child, code: code)
  } else { () }
}

// Column widths for a table, as a typesetter would choose them: the widths that make the table
// shortest. A cell's height in lines is estimated from its length on one line. A column is
// never narrower than its longest word, so nothing runs into the next column, nor wider than
// its longest cell, so a table whose cells all fit on one line keeps its natural widths. A
// column of short entries is not wrapped at all. The search starts from widths in proportion
// to the columns' mean cell length and moves width between columns while that makes the table
// shorter, which also evens out the rows.
#let fit-columns(n, head, cells, room) = {
  let set-in(body, weight: "regular", code: false) = text(
    font: if code { mono } else { sans },
    size: if code { table-size * 0.93 } else { table-size }, // code: see code-in-sans
    weight: weight,
    body,
  )
  let natural(body, weight: "regular") = measure(set-in(body, weight: weight)).width + 0.5pt
  // words are measured in semibold, the widest weight a cell uses
  let widest-word(body) = calc.max(0pt, ..unbreakable(body).map(((w, code)) => (
    measure(set-in(w, weight: "semibold", code: code)).width + 0.5pt
  )))
  let rows = cells.map(c => natural(c.body)).chunks(n)
  let header = head.map(c => natural(c.body, weight: "semibold"))
  let longest = range(n).map(j => calc.max(header.at(j), ..rows.map(r => r.at(j))))
  let mean = range(n).map(j => rows.map(r => r.at(j)).sum() / rows.len())
  let insets = range(n).map(j => if j == 0 { cell-inset } else { 2 * cell-inset })
  let free = room - insets.sum()
  // A column of short entries (a term, a date, a number) keeps each on one line.
  let floor = range(n).map(j => if longest.at(j) <= free / 4 { longest.at(j) } else {
    calc.min(longest.at(j), calc.max(
      ..(head.at(j), ..cells.slice(j).chunks(n).map(r => r.first())).map(c => widest-word(c.body)),
    ))
  })
  if longest.sum() <= free { return range(n).map(j => longest.at(j) + insets.at(j)) }
  // Lines per row, plus a trace of the unrounded heights so that a move that saves no whole
  // line yet is still told apart from one that leads nowhere. Words rarely fill a line: 1.1.
  let height(ws) = rows
    .map(r => {
      let lines = range(n).map(j => r.at(j) * 1.1 / ws.at(j))
      calc.max(..lines.map(calc.ceil)) + calc.max(..lines) / 100
    })
    .sum()
  // the start: in proportion to the mean, within the bounds, scaled until the widths fill the room
  let ws = mean
  for _ in range(6) {
    ws = ws.map(w => w * (free / ws.sum()))
    ws = range(n).map(j => calc.max(floor.at(j), calc.min(longest.at(j), ws.at(j))))
  }
  let step = free / 60
  for _ in range(120) {
    let best = (height(ws), ws)
    for (a, b) in range(n).map(a => range(n).map(b => (a, b))).flatten().chunks(2) {
      if a == b { continue }
      let t = ws
      t.at(a) -= step
      t.at(b) += step
      if t.at(a) >= floor.at(a) and t.at(b) <= longest.at(b) {
        let h = height(t)
        if h < best.first() { best = (h, t) }
      }
    }
    if best.last() == ws { break }
    ws = best.last()
  }
  range(n).map(j => ws.at(j) + insets.at(j))
}

// --- chapters, parts and the front matter ------------------------------------------------------

// A new right-hand page. The mark before the break lets the running head tell an empty
// left-hand page on the way: it lies after a mark and before the next opener.
#let to-recto() = {
  [#metadata("end") <flow-end>]
  pagebreak(to: "odd", weak: true)
}

#let blank-page(page) = {
  let openers = selector(heading.where(level: 1)).or(<book-part>)
  query(<flow-end>).any(end => {
    let next = query(openers.after(end.location())).first(default: none)
    end.location().page() < page and next != none and next.location().page() > page
  })
}

// Footnotes are numbered afresh in each chapter.
#let chapter-opener(number) = {
  to-recto()
  chapter-number.update(number)
  counter(footnote).update(0)
}

// A part page has the chapter opener's shape, larger and lower on the page.
#let part-page(number, title) = {
  to-recto()
  chapter-number.update("part")
  set par(justify: false)
  set text(hyphenate: false)
  v(62mm)
  if number != "" {
    text(font: sans, size: 10pt, weight: "bold", tracking: 0.25em, fill: accent)[PART #number]
    v(1.1em)
  }
  balanced(text(font: sans, size: 34pt, weight: "light", fill: ink)[#title])
  v(7mm)
  line(length: 40mm, stroke: 2pt + accent)
  [#metadata((number: number, title: title)) <book-part>]
  pagebreak()
}

#let title-page(title, subtitle, foot) = {
  set par(justify: false)
  set text(hyphenate: false)
  v(36mm)
  balanced(text(font: sans, size: 40pt, weight: "light", fill: ink)[#title])
  v(6mm)
  line(length: 40mm, stroke: 2pt + accent)
  v(7mm)
  balanced(text(font: sans, size: 15pt, weight: "light", fill: muted)[#subtitle])
  v(1fr)
  set par(leading: 0.6em)
  text(font: sans, size: 8.6pt, fill: muted, tracking: 0.02em)[#foot]
  pagebreak()
}

// The back of the title page: what this copy is, set small at the foot of the page.
#let edition-page(body) = {
  set text(size: 8.6pt, fill: muted, hyphenate: false)
  set par(justify: false, leading: 0.55em, spacing: 1.1em)
  v(1fr)
  block(width: 85%, body)
  pagebreak()
}

#let front-chapter(title) = {
  to-recto()
  chapter-number.update("front")
  heading(level: 1, outlined: false, title)
}

// One line of the contents or the list of figures: the label hangs in its own column, a title
// that wraps keeps to its left edge, and leaders run to the page number on the last line.
// (A `set par` inside the block would not reach this paragraph, so it is built explicitly.)
#let toc-line(target, label-width, label, title, page, indent: 0pt, above: 0.3em, below: 0.3em) = {
  let folio = box(width: 2.4em, align(right, page))
  let entry = link(target)[#box(width: label-width, label)#title#h(0.5em)#dots#folio]
  block(above: above, below: below, inset: (left: indent), par(hanging-indent: label-width, entry))
}

// The plain text of a heading's body, for comparing it with a fixed title.
#let plain-text(it) = {
  if type(it) == str { it } else if it.has("text") { it.text } else if it.has("children") {
    it.children.map(plain-text).join()
  } else if it.has("body") { plain-text(it.body) } else if it == [ ] { " " } else { "" }
}

// Every chapter of Parts II to IV opens with these two sections; listed under each chapter they
// would repeat on every line of the contents, usually with the chapter's own page number.
#let routine-sections = ("The concept", "In v1")

#let contents() = {
  front-chapter[Contents]
  set par(justify: false, leading: 0.52em)
  set text(size: 9.6pt, hyphenate: false)
  let number-width = 7mm
  context {
    let wanted = selector(<book-part>).or(heading.where(level: 1, outlined: true)).or(
      heading.where(level: 2))
    let in-outlined-chapter = false
    for el in query(wanted) {
      let loc = el.location()
      if el.func() == metadata {
        let name = if el.value.number == "" { upper(el.value.title) } else [
          PART #el.value.number#h(0.6em)·#h(0.6em)#upper(el.value.title)
        ]
        block(above: 1.9em, below: 0.9em, text(
          font: sans,
          size: 7.6pt,
          weight: "bold",
          tracking: 0.2em,
          fill: accent,
          name,
        ))
      } else if el.level == 1 {
        in-outlined-chapter = true
        let n = chapter-number.at(loc)
        let num = if n in ("", "front", "part") { [] } else [#n]
        set text(font: sans, size: 10pt)
        toc-line(
          loc,
          number-width,
          text(weight: "semibold", num),
          text(weight: "semibold", el.body),
          text(weight: "semibold", page-label(loc)),
          above: 1.1em,
          below: 0.55em,
        )
      } else if in-outlined-chapter and plain-text(el.body) not in routine-sections {
        toc-line(
          loc,
          0pt,
          [],
          el.body,
          text(font: sans, size: 8.8pt, page-label(loc)),
          indent: number-width,
        )
      }
    }
  }
}

#let figures-list() = {
  front-chapter[Figures]
  set par(justify: false, leading: 0.52em)
  set text(size: 9.6pt, hyphenate: false)
  context {
    let figures = query(<book-figure>)
    let label(f) = text(font: sans, weight: "semibold", f.value.number)
    let width = calc.max(0pt, ..figures.map(f => measure(label(f)).width)) + 0.9em
    let chapter = none
    for f in figures {
      // a little air between the chapters' figures: "Figure 2-1" starts chapter 2
      let this = f.value.number.split("-").first()
      toc-line(
        f.location(),
        width,
        label(f),
        f.value.short,
        text(font: sans, page-label(f.location())),
        above: if chapter != none and this != chapter { 1.3em } else { 0.6em },
        below: 0.6em,
      )
      chapter = this
    }
  }
}

// --- the book ----------------------------------------------------------------------------------

// The verso names the chapter, the recto the section: the first that starts on the page, else
// the one running into it. Openers, part pages and blank pages carry no head; a turned figure's
// page carries only its folio, because a head would run across the drawing.
#let running-head() = context {
  let here-page = here().page()
  let on-page(sel) = query(sel).filter(e => e.location().page() == here-page)
  if on-page(heading.where(level: 1)).len() > 0 or on-page(<book-part>).len() > 0 { return }
  if blank-page(here-page) { return }
  let before = query(heading.where(level: 1).before(here()))
  if before.len() == 0 { return }
  let chapter = before.last()
  let number = chapter-number.at(chapter.location())
  // An appendix is numbered by a letter, a chapter by digits.
  let kind = if number.match(regex("^\d+$")) != none { "Chapter" } else { "Appendix" }
  let chapter-label = if number in ("", "front", "part") { chapter.body } else [
    #kind #number#h(0.5em)·#h(0.5em)#chapter.body
  ]
  let sections = query(heading.where(level: 2).after(chapter.location())).filter(h => (
    h.location().page() <= here-page
  ))
  let starting = sections.filter(h => h.location().page() == here-page)
  let section = if starting.len() > 0 { starting.first().body } else if sections.len() > 0 {
    sections.last().body
  } else { chapter-label }
  let turned = on-page(<book-figure>).any(f => f.value.turned)
  set text(font: sans, size: 7.8pt, fill: muted, tracking: 0.04em, hyphenate: false)
  let folio = text(fill: ink, weight: "semibold", counter(page).display())
  if calc.even(here-page) {
    if turned { folio } else [#folio#h(1.4em)#chapter-label]
  } else {
    if turned [#h(1fr)#folio] else [#h(1fr)#section#h(1.4em)#folio]
  }
}

#let opener-foot() = context {
  let here-page = here().page()
  let openers = query(heading.where(level: 1)).filter(h => h.location().page() == here-page)
  if openers.len() > 0 {
    align(center, text(font: sans, size: 7.8pt, fill: muted)[#counter(page).display()])
  }
}

#let book(title: "", planner: true, body) = {
  set document(title: title)
  set page(
    paper: "a4",
    margin: (top: page-top, bottom: page-bottom, inside: side, outside: side),
    header: running-head(),
    header-ascent: 40%,
    footer: opener-foot(),
    numbering: "i",
  )
  set text(font: serif, size: 10.5pt, lang: "en", region: "us", hyphenate: true, fill: ink)
  // Justified, with a little give in the letter spacing so a line rarely opens wide gaps.
  set par(
    justify: true,
    leading: 0.66em, // 10.5 on 13.8 pt: a long measure needs the air
    spacing: 1.1em, // without a first-line indent, a paragraph break must show: a third of a line
    first-line-indent: 0pt,
    justification-limits: (
      spacing: (min: 75%, max: 135%),
      tracking: (min: -0.01em, max: 0.012em),
    ),
  )
  // Cascadia Mono's regular is darker than the serif; its variable weight axis gives a
  // lighter cut that matches the color of the text around it. Code in bold (a strong span
  // adds its weight on top) or in a semibold heading keeps the weight around it.
  show raw: set text(font: mono)
  show raw: it => context if text.weight == "regular" { text(weight: 350, it) } else { it }
  show raw.where(block: false): set text(size: code-in-serif)
  // A short command never breaks at its spaces ("GET /" … "health"). Other code spans break
  // only where Typst finds a break in them, after a slash or a hyphen, as paths do in print.
  show raw.where(block: false): it => if it.text.contains(" ") and it.text.len() <= 24 {
    box(it)
  } else { it }
  // Code blocks keep Typst's 0.8 em (8.4 pt), set ragged on a light ground.
  show raw.where(block: true): it => block(
    width: 100%,
    fill: rgb("#f5f6f8"),
    inset: (x: 8pt, y: 7pt),
    radius: 2pt,
    above: 1.2em,
    below: 1.2em,
    { set par(justify: false); it },
  )
  show quote.where(block: true): it => pad(left: 1.4em, right: 1em, it.body)
  // A list item that runs over several lines stands apart from the next.
  set list(indent: 0.6em, body-indent: 0.55em, marker: ([•], [–]), spacing: 0.78em)
  set enum(indent: 0.4em, body-indent: 0.55em, spacing: 0.78em)
  // A list inside a list item follows its lead-in as closely as the items follow each other.
  show list: it => context {
    show list: set block(above: list.spacing)
    it
  }
  set footnote.entry(
    separator: line(length: 25%, stroke: 0.5pt + hairline),
    gap: 0.45em,
    clearance: 1.1em,
  )
  show footnote.entry: set text(size: 8pt, hyphenate: false)
  show footnote.entry: set par(justify: false, leading: 0.5em)
  show link: it => it

  // Headings: chapters open a page; sections are set in the sans of the figures.
  set heading(numbering: none)
  show heading: set text(hyphenate: false)
  show heading.where(level: 1): it => {
    set par(justify: false)
    v(24mm)
    context {
      let number = chapter-number.get()
      if number not in ("", "front", "part") {
        text(font: sans, size: 9pt, weight: "bold", tracking: 0.25em, fill: accent)[CHAPTER #number]
        v(0.7em)
      }
    }
    block(below: 0pt, balanced(text(font: sans, size: 26pt, weight: "light", fill: ink, it.body)))
    v(5mm)
    line(length: 22mm, stroke: 1.6pt + accent)
    v(13mm, weak: true) // weak: a section heading right after it adds no space of its own,
    // since of two adjacent weak spaces only the larger is kept
  }
  show heading.where(level: 2): it => block(above: 2em, below: 0.85em, sticky: true)[
    #set par(justify: false)
    #text(font: sans, size: 13.5pt, weight: "semibold", fill: ink, it.body)
  ]
  show heading.where(level: 3): it => block(above: 1.55em, below: 0.7em, sticky: true)[
    #set par(justify: false)
    #text(font: sans, size: 11pt, weight: "semibold", fill: ink, it.body)
  ]
  show heading.where(level: 4): it => block(above: 1.2em, below: 0.6em, sticky: true)[
    #set par(justify: false)
    #text(style: "italic", it.body)
  ]

  // Tables: the sans of the figures, small, with hairlines between rows. A table of up to three
  // columns keeps the text's measure; one of four or more takes the wide measure of the figures,
  // so its columns do not wrap every few words. Narrow columns are set ragged, unhyphenated.
  // A table shorter than a sixth of a page stays whole; a longer one breaks between rows and
  // repeats its header.
  show figure.where(kind: table): set block(breakable: true) // the figure's own block
  show figure.where(kind: table): it => context {
    let tall = measure(it.body, width: text-width).height > text-height / 6
    block(above: 1.4em, below: 1.6em, breakable: tall, it.body)
  }
  set table(
    inset: (x, y) => (left: if x == 0 { 0pt } else { cell-inset }, right: cell-inset, y: 4.4pt),
    stroke: (x, y) => if y == 0 { (top: 0.8pt + ink) } else { (top: 0.35pt + hairline) },
  )
  set table.hline(stroke: 0.6pt + ink)
  set table.cell(breakable: false) // a page break falls between rows, never inside one
  show table: set text(font: sans, size: table-size, hyphenate: false)
  show table: set par(justify: false, leading: 0.5em)
  show table.cell.where(y: 0): set text(weight: "semibold")
  show table: it => context {
    // Pandoc's table (a header, its rule, then plain cells) is rebuilt once. The rebuilt table
    // passes through this rule again, and its second header tells it apart.
    // - No orphan row: its first row becomes a second, unrepeated header. Typst keeps a header
    //   with at least one row after it, so a page never ends on the header and a single row.
    //   (A footer would keep the last rows together too, but Typst 0.15 can set an unrepeated
    //   footer on a page of its own.)
    // - Its columns get widths that fit their contents (see fit-columns).
    let n = it.columns.len()
    let kinds = it.children.map(c => c.func())
    let cells = it.children.filter(c => c.func() == table.cell)
    let plain = kinds.len() > 2 and kinds.slice(0, 2) == (table.header, table.hline)
    if plain and cells.len() == kinds.len() - 2 and it.columns.all(c => c == auto) {
      let fields = it.fields()
      let _ = fields.remove("children")
      let head = it.children.first().children
      let room = if n >= 4 { wide-width } else { text-width }
      fields.insert("columns", fit-columns(n, head, cells, room))
      let rows = if cells.len() >= 3 * n {
        (table.header(level: 2, repeat: false, ..cells.slice(0, n)), ..cells.slice(n))
      } else { cells }
      return table(..fields, ..it.children.slice(0, 2), ..rows)
    }
    show raw.where(block: false): set text(size: code-in-sans)
    let ruled = block(stroke: (bottom: 0.8pt + ink), it)
    if n >= 4 { pad(x: -outdent, ruled) } else { ruled }
  }

  body
}
