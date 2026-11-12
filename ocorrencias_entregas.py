"""
Registro de ocorrências de entrega + relatório em PDF.

Como usar
---------
1. Instale a dependência (uma única vez):  pip install reportlab
2. Execute:                                python ocorrencias_entregas.py
3. Preencha o nº do pedido, escolha a data e o motivo e clique em "Adicionar".
4. Quando terminar, clique em "Gerar PDF" e escolha onde salvar o relatório.

O tkinter já vem junto com o Python no Windows e no macOS.
No Linux (Debian/Ubuntu) instale com:  sudo apt install python3-tk
"""

import tkinter as tk
from collections import Counter
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MOTIVOS = [
    "Endereço não localizado",
    "Problemas com o veículo",
    "Cliente ausente",
]

COR_PRINCIPAL = colors.HexColor("#1F3A5F")
COR_ZEBRA = colors.HexColor("#F2F5F9")
COR_LINHA = colors.HexColor("#C9D1DC")


# --------------------------------------------------------------------------
# Geração do PDF
# --------------------------------------------------------------------------
def gerar_pdf(registros, caminho):
    """Gera o relatório em PDF.

    registros: lista de tuplas (pedido, data "dd/mm/aaaa", motivo)
    caminho:   arquivo de saída (.pdf)
    """
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "Titulo", parent=estilos["Title"], textColor=COR_PRINCIPAL, fontSize=20, spaceAfter=4
    )
    subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"], textColor=colors.grey, fontSize=10, spaceAfter=14
    )
    secao = ParagraphStyle(
        "Secao", parent=estilos["Heading2"], textColor=COR_PRINCIPAL, fontSize=13,
        spaceBefore=14, spaceAfter=6,
    )

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, "Relatório de ocorrências de entrega")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="Relatório de ocorrências de entrega",
    )

    historia = [
        Paragraph("Relatório de ocorrências de entrega", titulo),
        Paragraph(
            f"Gerado em {datetime.now():%d/%m/%Y às %H:%M} &nbsp;•&nbsp; "
            f"{len(registros)} ocorrência(s) registrada(s)",
            subtitulo,
        ),
    ]

    # --- Resumo por motivo ---
    contagem = Counter(r[2] for r in registros)
    linhas_resumo = [["Motivo", "Quantidade"]]
    for motivo in MOTIVOS:
        linhas_resumo.append([motivo, str(contagem.get(motivo, 0))])
    linhas_resumo.append(["Total", str(len(registros))])

    tabela_resumo = Table(linhas_resumo, colWidths=[11 * cm, 4 * cm])
    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), COR_ZEBRA),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_LINHA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    historia += [Paragraph("Resumo por motivo", secao), tabela_resumo]

    # --- Detalhamento ---
    historia.append(Paragraph("Detalhamento", secao))
    linhas = [["Nº do pedido", "Data", "Motivo"]] + [list(r) for r in registros]
    tabela = Table(linhas, colWidths=[4 * cm, 3.5 * cm, 9.5 * cm], repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_LINHA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(2, len(linhas), 2):  # linhas alternadas
        estilo.append(("BACKGROUND", (0, i), (-1, i), COR_ZEBRA))
    tabela.setStyle(TableStyle(estilo))
    historia.append(tabela)

    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)


# --------------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ocorrências de entrega")
        self.minsize(760, 480)
        self.geometry("820x520")

        hoje = date.today()
        self.var_pedido = tk.StringVar()
        self.var_dia = tk.StringVar(value=f"{hoje.day:02d}")
        self.var_mes = tk.StringVar(value=f"{hoje.month:02d}")
        self.var_ano = tk.StringVar(value=str(hoje.year))
        self.var_motivo = tk.StringVar()

        self._montar_formulario(hoje)
        self._montar_tabela()
        self._montar_rodape()
        self._atualizar_contador()

    # ---- construção da tela ----
    def _montar_formulario(self, hoje):
        form = ttk.LabelFrame(self, text="Nova ocorrência", padding=12)
        form.pack(fill="x", padx=12, pady=(12, 6))

        # Coluna 1: número do pedido
        ttk.Label(form, text="Nº do pedido").grid(row=0, column=0, sticky="w")
        self.entry_pedido = ttk.Entry(form, textvariable=self.var_pedido, width=22)
        self.entry_pedido.grid(row=1, column=0, padx=(0, 14), sticky="w")

        # Coluna 2: data (dia / mês / ano)
        ttk.Label(form, text="Data").grid(row=0, column=1, sticky="w")
        quadro_data = ttk.Frame(form)
        quadro_data.grid(row=1, column=1, padx=(0, 14), sticky="w")
        ttk.Combobox(
            quadro_data, textvariable=self.var_dia, width=4, state="readonly",
            values=[f"{d:02d}" for d in range(1, 32)],
        ).pack(side="left")
        ttk.Label(quadro_data, text="/").pack(side="left", padx=2)
        ttk.Combobox(
            quadro_data, textvariable=self.var_mes, width=4, state="readonly",
            values=[f"{m:02d}" for m in range(1, 13)],
        ).pack(side="left")
        ttk.Label(quadro_data, text="/").pack(side="left", padx=2)
        ttk.Combobox(
            quadro_data, textvariable=self.var_ano, width=6, state="readonly",
            values=[str(a) for a in range(hoje.year - 2, hoje.year + 2)],
        ).pack(side="left")

        # Coluna 3: motivo
        ttk.Label(form, text="Motivo").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            form, textvariable=self.var_motivo, values=MOTIVOS, width=28, state="readonly"
        ).grid(row=1, column=2, padx=(0, 14), sticky="w")

        ttk.Button(form, text="Adicionar", command=self.adicionar).grid(
            row=1, column=3, sticky="e"
        )
        form.columnconfigure(3, weight=1)

        self.entry_pedido.focus_set()
        self.bind("<Return>", lambda _e: self.adicionar())

    def _montar_tabela(self):
        quadro = ttk.Frame(self)
        quadro.pack(fill="both", expand=True, padx=12, pady=6)

        self.tabela = ttk.Treeview(
            quadro, columns=("pedido", "data", "motivo"), show="headings", selectmode="extended"
        )
        self.tabela.heading("pedido", text="Nº do pedido")
        self.tabela.heading("data", text="Data")
        self.tabela.heading("motivo", text="Motivo")
        self.tabela.column("pedido", width=160, anchor="center")
        self.tabela.column("data", width=120, anchor="center")
        self.tabela.column("motivo", width=360, anchor="w")

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.tabela.bind("<Delete>", lambda _e: self.remover())

    def _montar_rodape(self):
        rodape = ttk.Frame(self)
        rodape.pack(fill="x", padx=12, pady=(6, 12))

        self.lbl_total = ttk.Label(rodape, text="")
        self.lbl_total.pack(side="left")

        ttk.Button(rodape, text="Gerar PDF", command=self.exportar_pdf).pack(side="right")
        ttk.Button(rodape, text="Limpar tudo", command=self.limpar).pack(side="right", padx=6)
        ttk.Button(rodape, text="Remover selecionado", command=self.remover).pack(side="right")

    # ---- ações ----
    def adicionar(self):
        pedido = self.var_pedido.get().strip()
        motivo = self.var_motivo.get().strip()

        if not pedido:
            messagebox.showwarning("Atenção", "Informe o número do pedido.")
            self.entry_pedido.focus_set()
            return
        if not motivo:
            messagebox.showwarning("Atenção", "Selecione o motivo.")
            return

        try:
            data = date(
                int(self.var_ano.get()), int(self.var_mes.get()), int(self.var_dia.get())
            )
        except ValueError:
            messagebox.showwarning("Atenção", "A data selecionada não existe (ex.: 31/02).")
            return

        existentes = [self.tabela.item(i, "values")[0] for i in self.tabela.get_children()]
        if pedido in existentes and not messagebox.askyesno(
            "Pedido repetido", f"O pedido {pedido} já está na lista. Adicionar mesmo assim?"
        ):
            return

        self.tabela.insert("", "end", values=(pedido, data.strftime("%d/%m/%Y"), motivo))
        self.var_pedido.set("")
        self.entry_pedido.focus_set()
        self._atualizar_contador()

    def remover(self):
        for item in self.tabela.selection():
            self.tabela.delete(item)
        self._atualizar_contador()

    def limpar(self):
        if self.tabela.get_children() and messagebox.askyesno(
            "Limpar", "Remover todos os registros da lista?"
        ):
            self.tabela.delete(*self.tabela.get_children())
            self._atualizar_contador()

    def exportar_pdf(self):
        registros = [self.tabela.item(i, "values") for i in self.tabela.get_children()]
        if not registros:
            messagebox.showinfo("Sem dados", "Adicione ao menos uma ocorrência antes de gerar o PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".pdf",
            initialfile=f"relatorio_ocorrencias_{date.today():%Y-%m-%d}.pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not caminho:
            return

        try:
            gerar_pdf(registros, caminho)
        except Exception as erro:  # ex.: arquivo aberto em outro programa
            messagebox.showerror("Erro ao gerar o PDF", str(erro))
            return
        messagebox.showinfo("Pronto", f"Relatório salvo em:\n{caminho}")

    def _atualizar_contador(self):
        total = len(self.tabela.get_children())
        self.lbl_total.config(text=f"{total} ocorrência(s) na lista")


if __name__ == "__main__":
    App().mainloop()
